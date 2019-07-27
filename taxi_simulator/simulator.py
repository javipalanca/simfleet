import logging

import pandas as pd
from tabulate import tabulate
import json
import faker

from .customer import CustomerAgent
from .transport import TransportAgent
from .scenario import Scenario
from .fleetmanager import FleetManagerAgent
from .secretary import SecretaryAgent
from .route import RouteAgent
from.station import StationAgent

from spade.agent import Agent
from .helpers import random_position

from itertools import cycle

import os
import threading
import io
import random
import string
from .utils import load_class, status_to_str, request_path, avg
import time
from aiohttp import web as aioweb
import xlsxwriter
faker_factory = faker.Factory.create()

logger = logging.getLogger()


class SimulationConfig(object):
    """
    Dataclass to store the :class:`Simulator` config
    """

    def __init__(self):
        self.host = None
        self.simulation_name = None
        self.max_time = None
        self.transport_strategy = None
        self.customer_strategy = None
        self.fleetmanager_strategy = None
        self.secretary_strategy = None
        self.station_strategy = None
        self.scenario = None
        self.num_transport = None
        self.num_customers = None
        self.num_managers = None
        self.num_secretary = 1
        self.num_stations = None
        self.http_port = None
        self.ip_address = None
        self.fleetmanager_name = None
        self.fleetmanager_password = None
        self.route_name = None
        self.route_password = None
        self.verbose = None


class SimulatorAgent(Agent):
    """
    The Simulator. It manages all the simulation processes.
    Tasks done by the simulator at initialization:
        #. Create the XMPP server
        #. Run the SPADE backend
        #. Run the fleetmanager and route agents.
        #. Create agents passed as parameters (if any).
        #. Create agents defined in scenario (if any).

    After these tasks are done in the Simulator constructor, the simulation is started when the ``run`` method is called.
    """

    def __init__(self, config, agentjid="simulator@localhost", password="simulator123j3"):
        self.config = config

        super().__init__(jid=agentjid, password=password)

        self.pretty_name = "({})".format(self.config.simulation_name) if self.config.simulation_name else ""
        self.verbose = self.config.verbose

        self.host = config.host

        self.secretary_agent = None

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
        self.secretary_strategy = None
        self.station_strategy = None

        self.manager_types = ["Taxi", "Trucking", "Foodtransport"]
        self.type_generator = None

        self.start()

        logger.info("Starting SimFleet {}".format(self.pretty_name))

        self.selection = None
        self.manager_generator = None

        self.set_strategies(config.fleetmanager_strategy, config.transport_strategy, config.customer_strategy,
                            config.secretary_strategy, config.station_strategy)

        self.route_id = "{}@{}".format(config.route_name, self.host)
        self.route_agent = RouteAgent(self.route_id, config.route_password)
        self.route_agent.start()

        logger.info("Creating {} managers, {} transporter, {} customer and {} secretary.".format(config.num_managers,
                                                                                                 config.num_transport,
                                                                                                 config.num_customers,
                                                                                                 config.num_secretary,
                                                                                                 config.num_stations))

        self._icons = None
        self.load_icons('taxi_simulator/img_transports.json')

        self.types_assignment()
        self.create_agents_batch(SecretaryAgent, config.num_secretary)
        self.create_agents_batch(FleetManagerAgent, config.num_managers)
        self.manager_assignment()

        self.create_agents_batch(TransportAgent, config.num_transport)
        self.create_agents_batch(CustomerAgent, config.num_customers)
        self.create_agents_batch(StationAgent, config.num_stations)

        if config.scenario:
            _scenario = Scenario(config.scenario)
            self.load_scenario(_scenario.scenario)

        self.template_path = os.path.dirname(__file__) + os.sep + "templates"
        self.clear_agents()

    async def setup(self):
        logger.info("Simulator agent running")
        self.web.add_get("/app", self.index_controller, "index.html")
        self.web.add_get("/entities", self.entities_controller, None)
        self.web.add_get("/run", self.run_controller, None)
        self.web.add_get("/stop", self.stop_agents_controller, None)
        self.web.add_get("/clean", self.clean_controller, None)
        self.web.add_get("/download/excel/", self.download_stats_excel_controller, None, raw=True)
        self.web.add_get("/download/json/", self.download_stats_json_controller, None, raw=True)
        self.web.add_get("/generate/transports/{ntransports}/customers/{ncustomers}", self.generate_controller, None)

        self.web.app.router.add_static("/assets", os.path.dirname(os.path.realpath(__file__)) + "/templates/assets")

        self.web.start(port=self.config.http_port, templates_path=self.template_path)
        logger.info("Web interface running at http://127.0.0.1:{}/app".format(self.config.http_port))

    def load_scenario(self, scenario):
        '''
        Load the information from the preloaded scenario through the Scenario class

        Args:
             filename (str): name of the json file.
        '''
        logger.info("Loading scenario...")
        for manager in scenario["managers"]:
            password = manager["password"] if "password" in manager else faker_factory.password()
            self.create_agent(FleetManagerAgent, manager["name"], password, position=[0, 0])
        for transport in scenario["transports"]:
            password = transport["password"] if "password" in transport else faker_factory.password()
            speed = transport["speed"] if "speed" in transport else None
            self.create_agent(TransportAgent, transport["name"], password, transport["position"], speed=speed)
        for customer in scenario["customers"]:
            password = customer["password"] if "password" in customer else faker_factory.password()
            self.create_agent(CustomerAgent, customer["name"], password, customer["position"], target=customer["dest"])
        for station in scenario["stations"]:
            password = station["password"] if "password" in station else faker_factory.password()
            self.create_agent(CustomerAgent, station["name"], password, station["position"])

    def load_icons(self, filename):
        with open(filename, 'r') as f:
            logger.info("Reading icons {}".format(filename))
            self._icons = json.load(f)

    def set_secretary(self, agent):
        self.secretary_agent = agent

    def get_secretary(self):
        return self.secretary_agent

    def is_simulation_finished(self):
        """
        Checks if the simulation is finished.
        A simulation is finished if the max simulation time has been reached or when the fleetmanager says it.

        Returns:
            bool: whether the simulation is finished or not.
        """
        if self.config.max_time is None:
            return False
        return self.time_is_out() or self.is_simulation_finish()

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
        self.clear_stopped_agents()
        if not self.simulation_running:
            self.kill_simulator.clear()
            with self.simulation_mutex:
                for manager in self.manager_agents.values():
                    manager.add_strategy(self.fleetmanager_strategy)
                    logger.debug(f"Adding strategy {self.fleetmanager_strategy} to manager {manager.name}")
                for transport in self.transport_agents.values():
                    transport.add_strategy(self.transport_strategy)
                    logger.debug(f"Adding strategy {self.transport_strategy} to transport {transport.name}")
                for customer in self.customer_agents.values():
                    customer.add_strategy(self.customer_strategy)
                    logger.debug(f"Adding strategy {self.customer_strategy} to customer {customer.name}")
                for station in self.station_agents.values():
                    station.add_strategy(self.station_strategy)
                    logger.debug(f"Adding strategy {self.secretary_strategy} to station {station.name}")

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

        logger.info("\nTerminating... ({0:.1f} seconds elapsed)".format(self.simulation_time))

        self.stop_agents()

        self.print_stats()

        self.route_agent.stop()

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
        print("Manager stats")
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
        self.manager_df.to_excel(writer, 'Managers')
        self.customer_df.to_excel(writer, 'Passengers')
        self.transport_df.to_excel(writer, 'Taxis')
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
        return {"port": self.config.http_port, "ip": self.config.ip_address}

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
                            "name": "Taxis",
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

    def is_simulation_finish(self):
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

    async def generate_controller(self, request):
        ntransports = request.match_info["ntransports"]
        ncustomers = request.match_info["ncustomers"]
        self.create_agents_batch(TransportAgent, int(ntransports))
        self.create_agents_batch(CustomerAgent, int(ncustomers))
        self.clear_stopped_agents()
        return {"status": "ok"}

    async def clean_controller(self, request):
        """
        Web controller that resets the simulator to a clean state.

        Returns:
            dict: no template is returned since this is an AJAX controller, a dict with status=done
        """
        logger.info("Stopping simulation...")
        self.stop_agents()
        self.clear_agents()
        return {"status": "done"}

    async def stop_agents_controller(self, request):
        """
        Web controller that stops all the customer and transport agents.

        Returns:
            dict: no template is returned since this is an AJAX controller, a dict with status=done
        """
        self.stop_agents()
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
        df_avg, transport_df, customer_df = self.get_stats_dataframes()
        df_avg.to_excel(writer, sheet_name='Simulation')
        customer_df.to_excel(writer, sheet_name='Passengers')
        transport_df.to_excel(writer, sheet_name='Taxis')
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
        df_avg, manager_df ,transport_df, customer_df = self.get_stats_dataframes()

        data = {
            "simulation": json.loads(df_avg.to_json(orient="index"))["0"],
            "managers": json.loads(manager_df.to_json(orient="index")),
            "customers": json.loads(customer_df.to_json(orient="index")),
            "transports": json.loads(transport_df.to_json(orient="index"))
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
        if not self.simulation_time:
            self.simulation_time = time.time() - self.simulation_init_time if self.simulation_init_time else 0
        '''with self.lock:
            for name, agent in self.manager_agents.items():
                logger.debug("Stopping manager {}".format(name))
                agent.stop()
                agent.stopped = True
        '''
        with self.lock:
            for name, agent in self.transport_agents.items():
                logger.debug("Stopping transport {}".format(name))
                agent.stop()
                agent.stopped = True
        with self.lock:
            for name, agent in self.customer_agents.items():
                logger.debug("Stopping customer {}".format(name))
                agent.stop()
                agent.stop()
                agent.stopped = True
        '''with self.lock:
            for name, agent in self.station_agents.items():
                logger.debug("Stopping station {}".format(name))
                agent.stop()
                agent.stopped = True
        '''

    def get_manager_stats(self):
        """
        Creates a dataframe with the simulation stats of the customers
        The dataframe includes for each customer its name, waiting time, total time and status.

        Returns:
            ``pandas.DataFrame``: the dataframe with the customers stats.
        """
        try:
            names, fleetnames, quantitys, types = zip(*[(p.name, p.fleetName,
                                                       p.quantityFleet, p.type)
                                                      for p in self.manager_agents.values()])
        except ValueError:
            names, fleetnames, quantitys, types = [], [], [], []

        df = pd.DataFrame.from_dict({"name": names, "fleet_name": fleetnames, "quantity_fleet": quantitys, "type": types})
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
            names, status, places, potency = zip(*[(p.name, p.status,
                                                       p.places_available, p.potency)
                                                      for p in self.station_agents.values()])
        except ValueError:
            names, status, places, potency = [], [], [], []

        df = pd.DataFrame.from_dict({"name": names, "status": status, "places_available": places, "potency": potency})
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
        manager_df = manager_df[["name", "fleet_name", "quantity_fleet", "type"]]
        customer_df = self.get_customer_stats()
        customer_df = customer_df[["name", "waiting_time", "total_time", "status"]]
        transport_df = self.get_transport_stats()
        transport_df = transport_df[["name", "assignments", "distance", "status"]]
        station_df = self.get_station_stats()
        station_df = station_df[["name", "status", "places_available", "potency"]]
        stats = self.get_stats()
        df_avg = pd.DataFrame.from_dict({"Avg Waiting Time": [stats["waiting"]],
                                         "Avg Total Time": [stats["totaltime"]],
                                         "Simulation Finished": [stats["finished"]],
                                         "Simulation Time": [self.get_simulation_time()]
                                         })
        columns = ["Avg Waiting Time", "Avg Total Time", "Simulation Time", "Simulation Finished"]
        df_avg = df_avg[columns]

        return df_avg, transport_df, customer_df, manager_df, station_df

    def create_agent(self, cls, name, password, position, target=None, speed=None):
        """
        Create an agent of type ``cls`` (TransportAgent or CustomerAgent).

        Args:
            cls (class): class of the agent (TransportAgent or CustomerAgent)
            name (str): name of the agent
            password (str): password of the agent
            position (list): initial coordinates of the agent
            target (list, optional): destination coordinates of the agent
            speed (float, optional): speed of the vehicle
        """
        self.submit(self.async_create_agent(cls, name, password, position, target, speed))

    async def async_create_agent(self, cls, name, password, position, target, speed):
        """
        Coroutine to create an agent.

        Args:
            cls (class): class of the agent (TransportAgent or CustomerAgent)
            name (str): name of the agent
            password (str): password of the agent
            position (list): initial coordinates of the agent
            target (list, optional): destination coordinates of the agent
            speed (float, optional): speed of the vehicle
        """
        jid = f"{name}@{self.jid.domain}"
        agent = cls(jid, password)
        agent.set_id(name)
        if cls == SecretaryAgent:
            self.set_secretary(agent)
        elif cls == FleetManagerAgent:
            agent.set_secretary(self.get_secretary().jid)
            # agent.set_type(next(self.type_generator))
            agent.set_type("Taxi")
        else:
            if cls == TransportAgent:
                agent.set_fleetmanager(next(self.manager_generator))
            if cls != StationAgent: # if cls == TransportAgent or cls == CustomerAgent
                agent.set_route_agent(self.route_id)
            agent.set_secretary(self.get_secretary().jid)
            await agent.set_position(position)

            if target:
                agent.set_target_position(target)
            if speed:
                agent.set_speed(speed)

        await agent.start(auto_register=True)

        if cls == SecretaryAgent:
            strategy = self.secretary_strategy
            agent.add_strategy(strategy)
        elif cls == StationAgent:
            strategy = self.station_strategy
            self.add_station(agent)
            agent.add_strategy(strategy)
        elif cls == FleetManagerAgent:
            strategy = self.fleetmanager_strategy
            self.add_manager(agent)
        elif cls == TransportAgent:
            strategy = self.transport_strategy
            self.add_transport(agent)
        else: # cls == CustomerAgent:
            strategy = self.customer_strategy
            self.add_customer(agent)

        if self.simulation_running:
            agent.add_strategy(strategy)

    def create_agents_batch(self, cls, number: int):
        """
        Creates a batch of agents.

        Args:
            cls (class): class of the agent to create
            number (int): size of the batch
        """
        number = max(number, 0)
        iterations = [20] * (number // 20)
        iterations.append(number % 20)
        for iteration in iterations:
            for _ in range(iteration):
                suffix = "{}".format("".join(random.sample(string.ascii_letters, 4)))
                with self.lock:
                    if self.kill_simulator.is_set():
                        break
                    position = random_position()
                    name = "{}_{}".format(faker_factory.user_name(), suffix)
                    password = faker_factory.password()
                    self.create_agent(cls, name, password, position, None)

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

    def set_strategies(self, fleetmanager_strategy, transport_strategy, customer_strategy, secretary_strategy, station_strategy):
        """
        Gets the strategy strings and loads their classes. This strategies are prepared to be injected into any
        new transport or customer agent.

        Args:
            fleetmanager_strategy (str): the path to the fleetmanager strategy
            transport_strategy (str): the path to the transport strategy
            customer_strategy (str): the path to the customer strategy
        """
        self.fleetmanager_strategy = load_class(fleetmanager_strategy)
        self.transport_strategy = load_class(transport_strategy)
        self.customer_strategy = load_class(customer_strategy)
        self.secretary_strategy = load_class(secretary_strategy)
        self.station_strategy = load_class(station_strategy)
        logger.debug("Loaded strategy classes: {}, {}, {}, {} and {}".format(self.fleetmanager_strategy,
                                                                             self.transport_strategy,
                                                                             self.customer_strategy,
                                                                             self.secretary_strategy,
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
        return request_path(self, origin, destination)

    def manager_assignment(self):
        """
        assigns a generator to the manager_generator variable for the TransportAgent's record
        """
        if not self.manager_generator:
            self.manager_generator = None
        self.manager_generator = self.managers_generator()

    def managers_generator(self):
        """
        Create a generator of the jid of the FleetManagerAgent created

        Returns:
            generator: the jid of the FleetManagerAgent's
        """
        for manager in cycle(self.manager_agents.values()):
            yield str(manager.jid)

    def types_assignment(self):
        """
        Assigns a generator to the manager_generator variable for the TransportAgent's record
        """
        if not self.types_generator():
            self.type_generator = None
        self.type_generator = self.types_generator()

    def types_generator(self):
        """
        Create a type generator for FleetManagers

        Returns:
            generator: the type of the FleetManagerAgent's
        """
        for type in cycle(self.manager_types):
            yield str(type)

