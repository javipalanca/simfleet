import asyncio
import io
import json
import os
import threading
import time

import faker
import pandas as pd
from aiohttp import web as aioweb
from loguru import logger
from spade.agent import Agent
from tabulate import tabulate

from .customer import CustomerAgent
from .directory import DirectoryAgent
from .fleetmanager import FleetManagerAgent
from .route import RouteAgent
from .station import StationAgent
from .transport import TransportAgent
from .utils import load_class, status_to_str, avg
from .utils import request_path as async_request_path

faker_factory = faker.Factory.create()


class SimulatorAgent(Agent):
    """
    The Simulator. It manages all the simulation processes.
    Tasks done by the simulator at initialization:
        #. Create the XMPP server
        #. Run the SPADE backend
        #. Run the directory and route agents.
        #. Create agents defined in scenario (if any).

    After these tasks are done in the Simulator constructor, the simulation is started when the ``run`` method is called.
    """

    def __init__(self, config, agentjid="simulator@localhost", password="simulator123j3"):
        self.config = config

        super().__init__(jid=agentjid, password=password)

        self.pretty_name = "({})".format(self.config.simulation_name) if self.config.simulation_name else ""
        self.verbose = self.config.verbose

        self.host = config.host

        self.directory_agent = None

        self.df_avg = None
        self.customer_df = None
        self.transport_df = None
        self.manager_df = None
        self.station_df = None

        self.simulation_mutex = threading.Lock()
        self.simulation_running = False
        self.simulation_time = None
        self.simulation_init_time = None
        self.kill_simulator = threading.Event()
        self.kill_simulator.clear()
        self.lock = threading.RLock()
        self.route_id = None

        self.fleetmanager_strategy = None
        self.transport_strategy = None
        self.customer_strategy = None
        self.directory_strategy = None
        self.station_strategy = None

        logger.info("Starting SimFleet {}".format(self.pretty_name))

        self.set_default_strategies(config.fleetmanager_strategy, config.transport_strategy, config.customer_strategy,
                                    config.directory_strategy, config.station_strategy)

        self.route_id = "{}@{}".format(config.route_name, self.host)
        self.route_agent = RouteAgent(self.route_id, config.route_password)
        self.route_agent.start()

        self.clear_agents()

        self._icons = None
        icons_path = os.path.dirname(__file__) + os.sep + "templates" + os.sep + "data" + os.sep + "img_transports.json"
        self.load_icons(icons_path)

        self.create_directory_agent(name=config.directory_name, password=config.directory_password)

        logger.info("Creating {} managers, {} transports, {} customers and {} stations.".format(config.num_managers,
                                                                                                config.num_transport,
                                                                                                config.num_customers,
                                                                                                config.num_stations))
        self.load_scenario()

        self.template_path = os.path.dirname(__file__) + os.sep + "templates"

    async def setup(self):
        logger.info("Simulator agent running")
        self.web.add_get("/app", self.index_controller, "index.html")
        self.web.add_get("/init", self.init_controller, None)
        self.web.add_get("/entities", self.entities_controller, None)
        self.web.add_get("/run", self.run_controller, None)
        self.web.add_get("/stop", self.stop_agents_controller, None)
        self.web.add_get("/clean", self.clean_controller, None)
        self.web.add_get("/download/excel/", self.download_stats_excel_controller, None, raw=True)
        self.web.add_get("/download/json/", self.download_stats_json_controller, None, raw=True)

        self.web.app.router.add_static("/assets", os.path.dirname(os.path.realpath(__file__)) + "/templates/assets")

        self.web.start(hostname=self.config.http_ip, port=self.config.http_port, templates_path=self.template_path)
        logger.info("Web interface running at http://{}:{}/app".format(self.config.http_ip, self.config.http_port))

    def load_scenario(self):
        """
        Load the information from the preloaded scenario through the SimfleetConfig class
        """
        logger.info("Loading scenario...")
        for manager in self.config["fleets"]:
            name = manager["name"]
            password = manager["password"] if "password" in manager else faker_factory.password()
            fleet_type = manager["fleet_type"]
            strategy = manager.get("strategy")
            icon = manager.get("icon")
            agent = self.create_fleetmanager_agent(name, password, fleet_type=fleet_type, strategy=strategy)

            self.set_icon(agent, icon, default=fleet_type)

        while len(self.manager_agents) < self.config.num_managers:
            time.sleep(0.1)

        for transport in self.config["transports"]:
            name = transport["name"]
            password = transport["password"] if "password" in transport else faker_factory.password()
            position = transport["position"]
            fleetmanager = transport["fleet"]
            fleet_type = transport["fleet_type"]
            speed = transport.get("speed")
            fuel = transport.get("fuel")
            autonomy = transport.get("autonomy")
            current_autonomy = transport.get("current_autonomy")
            strategy = transport.get("strategy")
            icon = transport.get("icon")
            agent = self.create_transport_agent(name, password, position=position, speed=speed, fleet_type=fleet_type,
                                                fleetmanager=fleetmanager, strategy=strategy, autonomy=autonomy,
                                                current_autonomy=current_autonomy)

            if icon:
                self.set_icon(agent, icon, default=fleet_type)

        for customer in self.config["customers"]:
            name = customer["name"]
            password = customer["password"] if "password" in customer else faker_factory.password()
            fleet_type = customer["fleet_type"]
            position = customer["position"]
            target = customer["destination"]
            strategy = customer.get("strategy")
            icon = customer.get("icon")
            agent = self.create_customer_agent(name, password, fleet_type, position=position, target=target,
                                               strategy=strategy)

            self.set_icon(agent, icon, default="customer")

        for station in self.config["stations"]:
            password = station["password"] if "password" in station else faker_factory.password()
            strategy = station.get("strategy")
            icon = station.get("icon")
            agent = self.create_station_agent(station["name"], password, position=station["position"],
                                              power=station["power"], places=station["places"], strategy=strategy)
            self.set_icon(agent, icon, default="electric_station")

    def load_icons(self, filename):
        with open(filename, 'r') as f:
            logger.info("Reading icons {}".format(filename))
            self._icons = json.load(f)

    def assigning_fleet_icon(self, fleet_type, default=None):
        if fleet_type not in self._icons:
            fleet_type = "default" if default is None else default
        icon = self._icons[fleet_type].pop(0)
        self._icons[fleet_type].append(icon)
        logger.info("Got icon for fleet type {}".format(fleet_type))
        return icon

    def set_icon(self, agent, icon, default=None):
        if icon:
            if icon.startswith("data:image"):
                agent.set_icon(icon)
            else:
                agent.set_icon(self.assigning_fleet_icon(icon, default))
        else:
            agent.set_icon(self.assigning_fleet_icon(default))

    def set_directory(self, agent):
        self.directory_agent = agent

    def get_directory(self):
        return self.directory_agent

    def is_simulation_finished(self):
        """
        Checks if the simulation is finished.
        A simulation is finished if the max simulation time has been reached or when the fleetmanager says it.

        Returns:
            bool: whether the simulation is finished or not.
        """
        if self.config.max_time is None:
            return False
        return self.time_is_out() or self.all_customers_in_destination()

    def time_is_out(self):
        """
        Checks if the max simulation time has been reached.

        Returns:
            bool: whether the max simulation time has been reached or not.
        """
        return self.get_simulation_time() > self.config.max_time

    def run(self):
        """
        Starts the simulation
        """
        #  self.clear_stopped_agents()
        if not self.simulation_running:
            self.kill_simulator.clear()
            with self.simulation_mutex:
                for manager in self.manager_agents.values():
                    manager.run_strategy()
                    logger.debug(f"Running strategy {self.fleetmanager_strategy} to manager {manager.name}")
                for transport in self.transport_agents.values():
                    transport.run_strategy()
                    logger.debug(f"Running strategy {self.transport_strategy} to transport {transport.name}")
                for customer in self.customer_agents.values():
                    customer.run_strategy()
                    logger.debug(f"Running strategy {self.customer_strategy} to customer {customer.name}")
                for station in self.station_agents.values():
                    station.run_strategy()
                    logger.debug(f"Running strategy {self.directory_strategy} to station {station.name}")

            self.simulation_running = True
            self.simulation_init_time = time.time()
            logger.info("Simulation started.")

    def stop(self):
        """
        Finishes the simulation and prints simulation stats.
        Tasks done when a simulation is stopped:
            #. Stop participant agents.
            #. Print stats.
            #. Stop Route agent.
            #. Stop fleetmanager agent.
        """
        self.simulation_time = self.get_simulation_time()

        self.route_agent.stop().result()
        self.directory_agent.stop().result()

        logger.info("Terminating... ({0:.1f} seconds elapsed)".format(self.simulation_time))

        self.stop_agents()

        self.print_stats()

        return super().stop()

    def collect_stats(self):
        """
        Collects stats from all participant agents and from the simulation and stores it in three dataframes.
        """

        df_avg, self.transport_df, self.customer_df, self.manager_df, self.station_df = self.get_stats_dataframes()

        columns = []
        if self.config.simulation_name:
            df_avg["Simulation Name"] = self.config.simulation_name
            columns = ["Simulation Name"]
        columns += ["Avg Waiting Time", "Avg Total Time", "Simulation Time"]
        if self.config.max_time:
            df_avg["Max Time"] = self.config.max_time
            columns += ["Max Time"]
        columns += ["Simulation Finished"]
        self.df_avg = df_avg[columns]

    def print_stats(self):
        """
        Prints the dataframes collected by ``collect_stats``.
        """
        if self.df_avg is None:
            self.collect_stats()

        print("Simulation Results")
        print(tabulate(self.df_avg, headers="keys", showindex=False, tablefmt="fancy_grid"))
        print("FleetManager stats")
        print(tabulate(self.manager_df, headers="keys", showindex=False, tablefmt="fancy_grid"))
        print("Customer stats")
        print(tabulate(self.customer_df, headers="keys", showindex=False, tablefmt="fancy_grid"))
        print("Transport stats")
        print(tabulate(self.transport_df, headers="keys", showindex=False, tablefmt="fancy_grid"))
        print("Station stats")
        print(tabulate(self.station_df, headers="keys", showindex=False, tablefmt="fancy_grid"))

    def write_file(self, filename, fileformat="json"):
        """
        Writes the dataframes collected by ``collect_stats`` in JSON or Excel format.

        Args:
            filename (str): name of the output file to be written.
            fileformat (str): format of the output file. Choices: json or excel
        """
        if self.df_avg is None:
            self.collect_stats()
        if fileformat == "json":
            self.write_json(filename)
        elif fileformat == "excel":
            self.write_excel(filename)

    def write_json(self, filename):
        """
        Writes the collected data by ``collect_stats`` in a json file.

        Args:
            filename (str): name of the json file.
        """
        data = {
            "simulation": json.loads(self.df_avg.to_json(orient="index"))["0"],
            "customers": json.loads(self.customer_df.to_json(orient="index")),
            "transports": json.loads(self.transport_df.to_json(orient="index")),
            "managers": json.loads(self.manager_df.to_json(orient="index")),
            "stations": json.loads(self.station_df.to_json(orient="index"))
        }

        with open(filename, 'w') as f:
            f.seek(0)
            json.dump(data, f, indent=4)

    def write_excel(self, filename):
        """
        Writes the collected data by ``collect_stats`` in an excel file.

        Args:
            filename (str): name of the excel file.
        """
        writer = pd.ExcelWriter(filename)
        self.df_avg.to_excel(writer, 'Simulation')
        self.manager_df.to_excel(writer, 'FleetManagers')
        self.customer_df.to_excel(writer, 'Customers')
        self.transport_df.to_excel(writer, 'Transports')
        writer.save()

    # ////////////////////////////////////////////////////////////

    @property
    def manager_agents(self):
        """
        Gets the dict of registered FleetManager

        Returns:
            dict: a dict of ``FleetManagerAgents`` with the name in the key
        """
        return self.get("manager_agents")

    @property
    def transport_agents(self):
        """
        Gets the dict of registered transports

        Returns:
            dict: a dict of ``TransportAgent`` with the name in the key
        """
        return self.get("transport_agents")

    @property
    def customer_agents(self):
        """
        Gets the dict of registered customers

        Returns:
            dict: a dict of ``CustomerAgent`` with the name in the key
        """
        return self.get("customer_agents")

    @property
    def station_agents(self):
        """
        Gets the dict of registered stations

        Returns:
            dict: a dict of ``StationAgent`` with the name in the key
        """
        return self.get("station_agents")

    async def index_controller(self, request):
        """
        Web controller that returns the index page of the simulator.

        Returns:
            dict: the name of the template, the data to be pre-processed in the template
        """
        return {"port": self.config.http_port, "ip": self.config.http_ip}

    async def init_controller(self, request):
        return {"coords": self.config.coords, "zoom": self.config.zoom}

    async def entities_controller(self, request):
        """
        Web controller that returns a dict with the entities of the simulator and their statuses.

        Example of the entities returned data::

            {
                "customers": [
                    {
                        "status": 24,
                        "transport": "transport2@127.0.0.1",
                        "dest": [ 39.463356, -0.376463 ],
                        "waiting": 3.25,
                        "position": [ 39.460568, -0.352529 ],
                        "id": "michaelstewart"
                    }
                ],
                "transports": [
                    {
                        "status": 11,
                        "customer": "michaelstewart@127.0.0.1",
                        "assignments": 1,
                        "path": [
                                 [ 39.478328, -0.406712 ],
                                 [ 39.478317, -0.406814 ],
                                 [ 39.460568, -0.352529 ]
                                ],
                        "dest": [ 39.460568, -0.352529 ],
                        "position": [ 39.468131, -0.39685 ],
                        "speed": 327.58,
                        "id": "transport2",
                        "distance": "6754.60"
                    }
                ],
                "stats": {
                    "totaltime": "-1.00",
                    "waiting": "3.25",
                    "finished": False,
                    "is_running": True
                },
                "tree": {
                    "name": "Agents",
                    "children": [
                        {
                            "count": "1",
                            "name": "Transports",
                            "children": [ { "status": 11, "name": " transport2", "icon": "fa-transport" } ]
                        },
                        {
                            "count": "1",
                            "name": "Customers",
                            "children": [ { "status": 24, "name": " michaelstewart", "icon": "fa-user" } ]
                        }
                    ]
                },
                "authenticated": False,
                "stations": [
                    {
                        "status": 24,
                        "position": [ 39.460568, -0.352529 ],
                        "id": "michaelstewart"
                    }
                ],
            }

        Returns:
            dict:  no template is returned since this is an AJAX controller, a dict with the list of transports, the list of customers, the tree view to be showed in the sidebar and the stats of the simulation.
        """
        result = {
            "transports": [transport.to_json() for transport in self.transport_agents.values()],
            "customers": [customer.to_json() for customer in self.customer_agents.values()],
            "tree": self.generate_tree(),
            "stats": self.get_stats(),
            "stations": [station.to_json() for station in self.station_agents.values()]
        }
        return result

    def generate_tree(self):
        """
        Generates the tree view in JSON format to be showed in the sidebar.

        Returns:
            dict: a dict with all the agents in the simulator, with their name, status and icon.
        """
        tree = {
            "name": 'Agents',
            "children": [
                {
                    "name": "Transports",
                    "count": "{}".format(len(self.transport_agents)),
                    "children": [
                        {
                            "name": " {}".format(i.name.split("@")[0]),
                            "status": i.status,
                            "icon": "fa-taxi"
                        } for i in self.transport_agents.values()
                    ]
                },
                {
                    "name": "Customers",
                    "count": "{}".format(len(self.customer_agents)),
                    "children": [
                        {
                            "name": " {}".format(i.name.split("@")[0]),
                            "status": i.status,
                            "icon": "fa-user"
                        } for i in self.customer_agents.values()
                    ]
                },

            ]
        }
        return tree

    def get_stats(self):
        """
        Generates the stats of the simulation in JSON format.

        Examples::

            {
                "totaltime": "12.25",
                "waiting": "3.25",
                "finished": False,
                "is_running": True
            }

        Returns:
            dict: a dict with the total time, waiting time, is_running and finished values

        """
        if len(self.customer_agents) > 0:
            waiting = avg([customer.get_waiting_time() for customer in self.customer_agents.values()])
            total = avg(
                [customer.total_time() for customer in self.customer_agents.values() if customer.total_time()])
        else:
            waiting, total = 0, 0

        return {
            "waiting": "{0:.2f}".format(waiting),
            "totaltime": "{0:.2f}".format(total),
            "finished": self.is_simulation_finished(),
            "is_running": self.simulation_running,
        }

    def all_customers_in_destination(self):
        """
        Checks whether the simulation has finished or not.
        A simulation is finished if all customers are at their destinations.
        If there is no customers the simulation is not finished.

        Returns:`
            bool: whether the simulation has finished or not.
        """
        if len(self.customer_agents) > 0:
            return all([customer.is_in_destination() for customer in self.customer_agents.values()])
        else:
            return False

    async def run_controller(self, request):
        """
        Web controller that starts the simulator.

        Returns:
            dict: no template is returned since this is an AJAX controller, an empty data dict is returned
        """
        self.run()
        return {"status": "ok"}

    async def clean_controller(self, request):
        """
        Web controller that resets the simulator to a clean state.

        Returns:
            dict: no template is returned since this is an AJAX controller, a dict with status=done
        """
        logger.info("Stopping simulation...")
        coroutines = self.stop_agents()
        await asyncio.gather(*coroutines)
        self.clear_agents()
        return {"status": "done"}

    async def stop_agents_controller(self, request):
        """
        Web controller that stops all the customer and transport agents.

        Returns:
            dict: no template is returned since this is an AJAX controller, a dict with status=done
        """
        coroutines = self.stop_agents()
        await asyncio.gather(*coroutines)
        return {"status": "done"}

    async def download_stats_excel_controller(self, request):
        """
        Web controller that returns an Excel file with the simulation results.

        Returns:
            Response: a Response of type "attachment" with the file content.
        """
        headers = {
            "Content-Disposition": "Attachment; filename=simulation.xlsx"
        }

        output = io.BytesIO()

        # Use a temp filename to keep pandas happy.
        writer = pd.ExcelWriter(output, engine='xlsxwriter')

        # Write the data frame to the StringIO object.
        df_avg, transport_df, customer_df, manager_df, stations_df = self.get_stats_dataframes()
        df_avg.to_excel(writer, sheet_name='Simulation')
        customer_df.to_excel(writer, sheet_name='Customers')
        transport_df.to_excel(writer, sheet_name='Transports')
        manager_df.to_excel(writer, sheet_name='FleetManagers')
        stations_df.to_excel(writer, sheet_name='Stations')
        writer.save()
        xlsx_data = output.getvalue()

        return aioweb.Response(
            body=xlsx_data,
            headers=headers
        )

    async def download_stats_json_controller(self, request):
        """
        Web controller that returns a JSON file with the simulation results.

        Returns:
            Response: a Response of type "attachment" with the file content.
        """
        headers = {
            "Content-Disposition": "Attachment; filename=simulation.json"
        }

        output = io.StringIO()

        # Write the data frame to the StringIO object.
        df_avg, transport_df, customer_df, manager_df, stations_df = self.get_stats_dataframes()

        data = {
            "simulation": json.loads(df_avg.to_json(orient="index"))["0"],
            "customers": json.loads(customer_df.to_json(orient="index")),
            "transports": json.loads(transport_df.to_json(orient="index")),
            "fleetmanagers": json.loads(manager_df.to_json(orient="index")),
            "stations": json.loads(stations_df.to_json(orient="index"))
        }

        json.dump(data, output, indent=4)

        return aioweb.Response(
            body=output.getvalue(),
            headers=headers
        )

    def clear_agents(self):
        """
        Resets the set of transports and customers. Resets the simulation clock.
        """
        self.set("manager_agents", {})
        self.set("transport_agents", {})
        self.set("customer_agents", {})
        self.set("station_agents", {})
        self.simulation_time = None
        self.simulation_init_time = None

    def clear_stopped_agents(self):
        """
        Removes from the transport and customer sets every agent that is stopped.
        """
        agents = self.get("manager_agents")
        self.set("manager_agents", {jid: agent for jid, agent in agents.items() if not agent.stopped})
        agents = self.get("transport_agents")
        self.set("transport_agents", {jid: agent for jid, agent in agents.items() if not agent.stopped})
        agents = self.get("customer_agents")
        self.set("customer_agents", {jid: agent for jid, agent in agents.items() if not agent.stopped})
        agents = self.get("station_agents")
        self.set("station_agents", {jid: agent for jid, agent in agents.items() if not agent.stopped})
        self.simulation_time = None
        self.simulation_init_time = None

    def stop_agents(self):
        """
        Stops the simulator and all the agents
        """
        self.kill_simulator.set()
        self.simulation_running = False
        results = []
        if not self.simulation_time:
            self.simulation_time = time.time() - self.simulation_init_time if self.simulation_init_time else 0
        with self.lock:
            for name, agent in self.manager_agents.items():
                logger.debug("Stopping manager {}".format(name))
                results.append(agent.stop())
                agent.stopped = True
        with self.lock:
            for name, agent in self.transport_agents.items():
                logger.debug("Stopping transport {}".format(name))
                results.append(agent.stop())
                agent.stopped = True
        with self.lock:
            for name, agent in self.customer_agents.items():
                logger.debug("Stopping customer {}".format(name))
                results.append(agent.stop())
                agent.stopped = True
        with self.lock:
            for name, agent in self.station_agents.items():
                logger.debug("Stopping station {}".format(name))
                results.append(agent.stop())
                agent.stopped = True
        return results

    def get_manager_stats(self):
        """
        Creates a dataframe with the simulation stats of the customers
        The dataframe includes for each customer its name, waiting time, total time and status.

        Returns:
            ``pandas.DataFrame``: the dataframe with the customers stats.
        """
        try:
            names, quantities, types = zip(*[(manager.name,
                                              manager.transports_in_fleet, manager.fleet_type)
                                             for manager in self.manager_agents.values()])
        except ValueError:
            names, quantities, types = [], [], []

        df = pd.DataFrame.from_dict(
            {"fleet_name": names, "transports_in_fleet": quantities, "type": types})
        return df

    def get_customer_stats(self):
        """
        Creates a dataframe with the simulation stats of the customers
        The dataframe includes for each customer its name, waiting time, total time and status.

        Returns:
            ``pandas.DataFrame``: the dataframe with the customers stats.
        """
        try:
            names, waitings, totals, statuses = zip(*[(p.name, p.get_waiting_time(),
                                                       p.total_time(), status_to_str(p.status))
                                                      for p in self.customer_agents.values()])
        except ValueError:
            names, waitings, totals, statuses = [], [], [], []

        df = pd.DataFrame.from_dict({"name": names, "waiting_time": waitings, "total_time": totals, "status": statuses})
        return df

    def get_transport_stats(self):
        """
        Creates a dataframe with the simulation stats of the transports
        The dataframe includes for each transport its name, assignments, traveled distance and status.

        Returns:
            ``pandas.DataFrame``: the dataframe with the transports stats.
        """
        try:
            names, assignments, distances, statuses = zip(*[(t.name, t.num_assignments,
                                                             "{0:.2f}".format(sum(t.distances)),
                                                             status_to_str(t.status))
                                                            for t in self.transport_agents.values()])
        except ValueError:
            names, assignments, distances, statuses = [], [], [], []
        df = pd.DataFrame.from_dict({"name": names,
                                     "assignments": assignments,
                                     "distance": distances,
                                     "status": statuses})
        return df

    def get_station_stats(self):
        """
        Creates a dataframe with the simulation stats of the customers
        The dataframe includes for each customer its name, waiting time, total time and status.

        Returns:
            ``pandas.DataFrame``: the dataframe with the customers stats.
        """
        try:
            names, status, places, power = zip(*[(p.name, p.status,
                                                  p.available_places, p.power)
                                                 for p in self.station_agents.values()])
        except ValueError:
            names, status, places, power = [], [], [], []

        df = pd.DataFrame.from_dict({"name": names, "status": status, "available_places": places, "power": power})
        return df

    def get_stats_dataframes(self):
        """
        Collects simulation stats and returns 3 dataframes with the information:
        A general dataframe with the average information, a dataframe with the transport's information
        and a dataframe with the customer's information.
        Returns:
            pandas.Dataframe, pandas.Dataframe, pandas.Dataframe: avg df, transport df and customer df
        """
        manager_df = self.get_manager_stats()
        manager_df = manager_df[["fleet_name", "transports_in_fleet", "type"]]
        customer_df = self.get_customer_stats()
        customer_df = customer_df[["name", "waiting_time", "total_time", "status"]]
        transport_df = self.get_transport_stats()
        transport_df = transport_df[["name", "assignments", "distance", "status"]]
        station_df = self.get_station_stats()
        station_df = station_df[["name", "status", "available_places", "power"]]
        stats = self.get_stats()
        df_avg = pd.DataFrame.from_dict({"Avg Waiting Time": [stats["waiting"]],
                                         "Avg Total Time": [stats["totaltime"]],
                                         "Simulation Finished": [stats["finished"]],
                                         "Simulation Time": [self.get_simulation_time()]
                                         })
        columns = ["Avg Waiting Time", "Avg Total Time", "Simulation Time", "Simulation Finished"]
        df_avg = df_avg[columns]

        return df_avg, transport_df, customer_df, manager_df, station_df

    async def async_start_agent(self, agent):
        await agent.start()

    def create_directory_agent(self, name, password):
        jid = f"{name}@{self.jid.domain}"
        agent = DirectoryAgent(jid, password)
        logger.debug("Creating Directory agent {}".format(jid))
        agent.set_id(name)

        self.set_directory(agent)

        agent.strategy = self.directory_strategy
        agent.run_strategy()

        agent.start().result()

    def create_fleetmanager_agent(self, name, password, fleet_type, strategy=None, icon=None):
        jid = f"{name}@{self.jid.domain}"
        agent = FleetManagerAgent(jid, password)
        logger.debug("Creating FleetManager {}".format(jid))
        agent.set_id(name)
        agent.set_directory(self.get_directory().jid)
        logger.debug("Assigning type {} to fleet manager {}".format(fleet_type, name))
        agent.set_fleet_type(fleet_type)

        if strategy:
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = self.fleetmanager_strategy

        if self.simulation_running:
            agent.run_strategy()

        self.add_manager(agent)

        self.submit(self.async_start_agent(agent))

        return agent

    def create_transport_agent(self, name, password, fleet_type, fleetmanager, position, strategy=None, speed=None,
                               autonomy=None, current_autonomy=None):
        jid = f"{name}@{self.jid.domain}"
        agent = TransportAgent(jid, password)
        logger.debug("Creating Transport {}".format(jid))
        agent.set_id(name)
        agent.set_directory(self.get_directory().jid)
        logger.debug("Assigning type {} to transport {}".format(fleet_type, name))
        agent.set_fleet_type(fleet_type)
        agent.set_fleetmanager(fleetmanager)
        agent.set_route_agent(self.route_id)
        agent.set_directory(self.get_directory().jid)
        if autonomy:
            agent.set_autonomy(autonomy, current_autonomy=current_autonomy)

        agent.set_initial_position(position)

        if speed:
            agent.set_speed(speed)

        if strategy:
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = self.transport_strategy

        if self.simulation_running:
            agent.run_strategy()

        self.add_transport(agent)

        self.submit(self.async_start_agent(agent))

        return agent

    def create_customer_agent(self, name, password, fleet_type, position, strategy=None, target=None):
        """
        Create a customer agent.

        Args:
            name (str): name of the agent
            password (str): password of the agent
            position (list): initial coordinates of the agent
            fleet_type (str): type of he fleet to be or demand
            target (list, optional): destination coordinates of the agent
            speed (float, optional): speed of the vehicle
        """
        jid = f"{name}@{self.jid.domain}"
        agent = CustomerAgent(jid, password)
        logger.debug("Creating Customer {}".format(jid))
        agent.set_id(name)
        agent.set_directory(self.get_directory().jid)
        logger.debug("Assigning type {} to customer {}".format(fleet_type, name))
        agent.set_fleet_type(fleet_type)
        agent.set_route_agent(self.route_id)
        agent.set_directory(self.get_directory().jid)

        agent.set_position(position)

        agent.set_target_position(target)

        if strategy:
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = self.customer_strategy

        if self.simulation_running:
            agent.run_strategy()

        self.add_customer(agent)

        self.submit(self.async_start_agent(agent))

        return agent

    def create_station_agent(self, name, password, position, power, places, strategy=None):
        """
        Create a customer agent.

        Args:
            name (str): name of the agent
            password (str): password of the agent
            position (list): initial coordinates of the agent
            fleet_type (str): type of he fleet to be or demand
            target (list, optional): destination coordinates of the agent
            speed (float, optional): speed of the vehicle
        """
        jid = f"{name}@{self.jid.domain}"
        agent = StationAgent(jid, password)
        logger.debug("Creating station {}".format(jid))
        agent.set_id(name)
        agent.set_directory(self.get_directory().jid)

        agent.set_directory(self.get_directory().jid)

        agent.set_position(position)

        agent.set_available_places(places)
        agent.set_power(power)

        if strategy:
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = self.station_strategy

        if self.simulation_running:
            agent.run_strategy()

        self.add_station(agent)

        self.submit(self.async_start_agent(agent))

        return agent

    def add_manager(self, agent):
        """
        Adds a new ``FleetManagerAgent`` to the store.

        Args:
            agent (``FleetManagerAgent``): the instance of the FleetManagerAgent to be added
        """
        with self.simulation_mutex:
            self.get("manager_agents")[agent.name] = agent

    def add_transport(self, agent):
        """
        Adds a new ``TransportAgent`` to the store.

        Args:
            agent (``TransportAgent``): the instance of the TransportAgent to be added
        """
        with self.simulation_mutex:
            self.get("transport_agents")[agent.name] = agent

    def add_customer(self, agent):
        """
        Adds a new :class:`CustomerAgent` to the store.

        Args:
            agent (``CustomerAgent``): the instance of the CustomerAgent to be added
        """
        with self.simulation_mutex:
            self.get("customer_agents")[agent.name] = agent

    def add_station(self, agent):
        """
        Adds a new :class:`StationAgent` to the store.

        Args:
            agent (``StationAgent``): the instance of the StationAgent to be added
        """
        with self.simulation_mutex:
            self.get("station_agents")[agent.name] = agent

    def set_default_strategies(self, fleetmanager_strategy, transport_strategy, customer_strategy, directory_strategy,
                               station_strategy):
        """
        Gets the strategy strings and loads their classes. This strategies are prepared to be injected into any
        new transport or customer agent.

        Args:
            fleetmanager_strategy (str): the path to the fleetmanager strategy
            transport_strategy (str): the path to the transport strategy
            customer_strategy (str): the path to the customer strategy
            directory_strategy (str): the path to the directory strategy
            station_strategy (str): the path to the station strategy
        """
        self.fleetmanager_strategy = load_class(fleetmanager_strategy)
        self.transport_strategy = load_class(transport_strategy)
        self.customer_strategy = load_class(customer_strategy)
        self.directory_strategy = load_class(directory_strategy)
        self.station_strategy = load_class(station_strategy)
        logger.debug("Loaded default strategy classes: {}, {}, {}, {} and {}".format(self.fleetmanager_strategy,
                                                                                     self.transport_strategy,
                                                                                     self.customer_strategy,
                                                                                     self.directory_strategy,
                                                                                     self.station_strategy))

    def get_simulation_time(self):
        """
        Returns the elapsed simulation time to the current time.
        If the simulation is not started it returns 0.

        Returns:
            float: the whole simulation time.
        """
        if not self.simulation_init_time:
            return 0
        if self.simulation_running:
            return time.time() - self.simulation_init_time
        return self.simulation_time

    def request_path(self, origin, destination):
        """
        Requests a path to the RouteAgent.

        Args:
            origin (list): the origin coordinates (lon, lat)
            destination (list): the target coordinates (lon, lat)

        Returns:
            list, float, float: the path as a list of points, the distance of the path, the estimated duration of the path
        """
        return async_request_path(self, origin, destination, self.route_id)
