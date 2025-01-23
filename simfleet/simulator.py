import asyncio
import io
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List

import faker
from aiohttp import web as aioweb
from loguru import logger
from spade.agent import Agent
from spade.behaviour import TimeoutBehaviour, OneShotBehaviour, CyclicBehaviour
from spade.template import Template
from spade.message import Message

from simfleet.common.agents.factory.create import CustomerFactory
from simfleet.common.agents.factory.create import DirectoryFactory
from simfleet.common.agents.factory.create import FleetManagerFactory
from simfleet.common.agents.factory.create import StationFactory
from simfleet.common.agents.factory.create import TransportFactory
from simfleet.common.agents.factory.create import VehicleFactory
from simfleet.common.agents.factory.create import TransportStopFactory
from simfleet.utils.routing import request_path as async_request_path

from simfleet.config.settings import set_default_strategies, set_default_metrics

from simfleet.utils.statistics import Log

from simfleet.communications.protocol import (
    REQUEST_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    COORDINATION_PROTOCOL,
)

faker_factory = faker.Factory.create()


class SimulatorAgent(Agent):
    """
    The Simulator. It manages all the simulation processes.
    Tasks done by the simulator at initialization:
        #. Create the XMPP server
        #. Run the SPADE backend
        #. Run the directory agent.
        #. Create agents defined in scenario (if any).

    After these tasks are done in the Simulator constructor, the simulation is started when the ``run`` method is called.
    """

    def __init__(
        self, config, agentjid="simulator@localhost", password="simulator123j3"
    ):
        self.config = config

        super().__init__(jid=agentjid, password=password)

        self.pretty_name = (
            "({})".format(self.config.simulation_name)
            if self.config.simulation_name
            else ""
        )
        self.verbose = self.config.verbose
        self.simulatorjid = agentjid

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

        self.stopped = False

        self.events_log = None
        self.default_strategies = {}
        self.delayed_launch_agents = {}

        logger.info("Starting SimFleet {}".format(self.pretty_name))

        self.default_strategies = set_default_strategies(
                                                config.directory_strategy,
                                                config.fleetmanager_strategy,
                                                config.transport_strategy,
                                                config.customer_strategy,
                                                config.station_strategy,
                                                config.vehicle_strategy
                                                #config.bus_stop_strategy
                                                )

        self.metrics_class = {}

        self.metrics_class = set_default_metrics(config.mobility_metrics)

        self.route_host = config.route_host

        self.clear_agents()

        self.base_path = Path(__file__).resolve().parent

        self._icons = None
        icons_path = self.base_path / "templates" / "data" / "img_transports.json"
        self.load_icons(icons_path)

        logger.info(
            "Creating {} managers, {} transports, {} customers, {} stations, {} stops, and {} vehicles.".format(
                config.num_managers,
                config.num_transport,
                config.num_customers,
                config.num_stations,
                config.num_stops,
                config.num_vehicles,
            )
        )

        self.template_path = self.base_path / "templates"

    async def setup(self):
        logger.info("Simulator agent running")
        self.web.add_get("/app", self.index_controller, "index.html")
        self.web.add_get("/init", self.init_controller, None)
        self.web.add_get("/entities", self.entities_controller, None)
        self.web.add_get("/run", self.run_controller, None)
        self.web.add_get("/stop", self.stop_agents_controller, None)

        self.web.add_get(
            "/download/json/", self.download_events_json_controller, None, raw=True
        )

        self.web.app.router.add_static("/assets", str(self.template_path / "assets"))

        self.web.start(
            hostname=self.config.http_ip,
            port=self.config.http_port,
            templates_path=str(self.template_path),
        )
        logger.info(
            "Web interface running at http://{}:{}/app".format(
                self.config.http_ip, self.config.http_port
            )
        )

        await self.create_directory_agent(name=self.config.directory_name,
                                    password=self.config.directory_password
                                    )

        await self.load_scenario()

        #Comunication template
        template = Template()
        template.set_metadata("protocol", COORDINATION_PROTOCOL)
        template.set_metadata("performative", REQUEST_PERFORMATIVE)

        self.add_behaviour(CoordinationBehaviour(), template)


    async def load_scenario(self):
        """
        Load the information from the preloaded scenario through the SimfleetConfig class
        """
        managers = []

        logger.info("Loading scenario...")
        for manager in self.config["fleets"]:
            name = manager["name"]
            password = (
                manager["password"]
                if "password" in manager
                else faker_factory.password()
            )
            fleet_type = manager["fleet_type"]
            strategy = manager.get("strategy")
            icon = manager.get("icon")
            agent = self.create_fleetmanager_agent(name,
                                                   password,
                                                   fleet_type=fleet_type,
                                                   strategy=strategy
                                                    )

            self.set_icon(agent, icon, default=fleet_type)
            managers.append(agent.start())
        await asyncio.gather(*managers)

        while len(self.manager_agents) < self.config.num_managers:
            time.sleep(0.1)

        # Bus line
        logger.info("Loading lines...")
        for line in self.config["lines"]:
            line_id = line["id"]
            stop_list = line["stops"]
            line_type = line["line_type"]
            self.add_line(line_id, stop_list, line_type)

        all_agents = []
        try:
            all_agents += await self.async_create_agents_batch_transport(self.config["transports"])
        except Exception as e:
            logger.exception("EXCEPTION creating Transport agents batch {}".format(e))
        try:
            all_agents += await self.async_create_agents_batch_customer(self.config["customers"])
        except Exception as e:
            logger.exception("EXCEPTION creating Customer agents batch {}".format(e))
        try:
            all_agents += await self.async_create_agents_batch_station(self.config["stations"])
        except Exception as e:
            logger.exception("EXCEPTION creating Station agents batch {}".format(e))
        try:
            all_agents += await self.async_create_agents_batch_vehicle(self.config["vehicles"])
        except Exception as e:
            logger.exception("EXCEPTION creating Vehicles agents batch {}".format(e))
        try:
            all_agents += await self.async_create_agents_batch_stop(self.config["stops"])
        except Exception as e:
            logger.exception("EXCEPTION creating Stop agents batch {}".format(e))

        assert all([asyncio.iscoroutine(x) for x in all_agents])
        await self.gather_batch(all_agents)

    async def gather_batch(self, all_coroutines):
        agents_batch = 20
        number = max(len(all_coroutines), 0)
        iterations = [agents_batch] * (number // agents_batch)
        if number % agents_batch:
            iterations.append(number % agents_batch)
        current_index = 0
        for iteration in iterations:
            logger.info(
                "Agent Batch Creation. Iteration current_index = {}".format(
                    current_index
                )
            )
            current_coros = all_coroutines[current_index : current_index + iteration]
            current_index += iteration
            await asyncio.sleep(0.1)
            await asyncio.gather(*current_coros)
        logger.success("All agents gathered")

    async def async_create_agents_batch_transport(self, agents: list) -> List:
        coros = []
        for transport in agents:
            name = transport["name"]
            logger.debug("transport creation batch = {}".format(name))
            password = (
                transport["password"]
                if "password" in transport
                else faker_factory.password()
            )

            class_ = transport["class"]
            fleet_type = transport["fleet_type"]
            service = transport.get("service")
            strategy = transport.get("strategy")
            position = transport.get("position")
            autonomy = transport.get("autonomy")
            current_autonomy = transport.get("current_autonomy")
            speed = transport.get("speed")
            optional = transport.get("optional")
            line = transport.get("line")
            capacity = transport.get("capacity")
            icon = transport.get("icon")
            delay = transport["delay"] if "delay" in transport else None

            delayed = False
            if delay is not None:
                delayed = True

            agent = self.create_transport_agent(
                                                name,
                                                password,
                                                class_,
                                                fleet_type,
                                                strategy=strategy,
                                                position=position,
                                                service=service,
                                                autonomy=autonomy,
                                                current_autonomy=current_autonomy,
                                                speed=speed,
                                                optional=optional,
                                                delayed=delayed,
                                                capacity=capacity,
                                                line=line
                                                )
            self.set_icon(agent, icon, default="transport")

            if delay is not None:
                if delay not in self.delayed_launch_agents:
                    self.delayed_launch_agents[delay] = []
                self.delayed_launch_agents[delay].append(agent)
            else:
                coros.append(agent.start())
        return coros

    async def async_create_agents_batch_customer(self, agents: list) -> List:
        coros = []
        for customer in agents:
            name = customer["name"]
            logger.debug("customer creation batch = {}".format(name))
            password = (
                customer["password"]
                if "password" in customer
                else faker_factory.password()
            )

            class_ = customer["class"]
            fleet_type = customer["fleet_type"]
            position = customer.get("position")
            speed = customer.get("speed")
            target = customer.get("destination")
            strategy = customer.get("strategy")
            line = customer.get("line")
            icon = customer.get("icon")
            delay = customer["delay"] if "delay" in customer else None

            delayed = False
            if delay is not None:
                delayed = True

            agent = self.create_customer_agent(
                                                name,
                                                password,
                                                class_,
                                                fleet_type,
                                                position=position,
                                                target=target,
                                                strategy=strategy,
                                                delayed=delayed,
                                                speed=speed,
                                                line=line
                                                )

            self.set_icon(agent, icon, default="customer")

            if delay is not None:
                if delay not in self.delayed_launch_agents:
                    self.delayed_launch_agents[delay] = []
                self.delayed_launch_agents[delay].append(agent)
            else:
                coros.append(agent.start())
        return coros

    async def async_create_agents_batch_station(self, agents: list) -> List:
        coros = []
        for station in agents:
            logger.debug("station creation batch = {}".format(station["name"]))
            password = (
                station["password"]
                if "password" in station
                else faker_factory.password()
            )
            class_ = station["class"]
            strategy = station.get("strategy")
            position = station.get("position")
            services = station.get("services")
            icon = station.get("icon")
            agent = self.create_station_agent(
                                                name=station["name"],
                                                password=password,
                                                position=position,
                                                class_=class_,
                                                services=services,
                                                strategy=strategy,
                                            )
            self.set_icon(agent, icon, default="electric_station")

            coros.append(agent.start())
        return coros


    async def async_create_agents_batch_stop(self, agents: list) -> List:
        coros = []
        for stop in agents:
            logger.debug("stop creation batch = {}".format(stop["name"]))
            password = (
                stop["password"]
                if "password" in stop
                else faker_factory.password()
            )
            strategy = stop.get("strategy")
            icon = stop.get("icon")
            position = stop.get("position")
            class_ = stop["class"]
            lines = stop["lines"]

            agent = self.create_bus_stop_agent(
                                                id=stop["id"],
                                                name=stop["name"],
                                                password=password,
                                                position=position,
                                                class_=class_,
                                                lines=lines,
                                                strategy=strategy,
                                            )

            self.set_icon(agent, icon, default="solar_station")

            coros.append(agent.start())
        return coros


    async def async_create_agents_batch_vehicle(self, agents: list) -> List:
        coros = []
        for transport in agents:
            name = transport["name"]
            logger.debug("vehicle creation batch = {}".format(name))
            password = (
                transport["password"]
                if "password" in transport
                else faker_factory.password()
            )

            position = transport.get("position")
            fleet_type = transport.get("fleet_type")
            speed = transport.get("speed")
            target = transport.get("destination")
            strategy = transport.get("strategy")
            icon = transport.get("icon")
            delay = transport["delay"] if "delay" in transport else None

            delayed = False
            if delay is not None:
                delayed = True

            agent = self.create_vehicle_agent(
                                                name,
                                                password,
                                                position=position,
                                                speed=speed,
                                                fleet_type=fleet_type,
                                                strategy=strategy,
                                                delayed=delayed,
                                                target=target,
                                            )
            self.set_icon(agent, icon, default="drone")

            if delay is not None:
                if delay not in self.delayed_launch_agents:
                    self.delayed_launch_agents[delay] = []
                self.delayed_launch_agents[delay].append(agent)
            else:
                coros.append(agent.start())
        return coros

    def load_icons(self, filename):
        with filename.open() as f:
            logger.info("Reading icons {}".format(filename))
            self._icons = json.load(f)

    def assigning_fleet_icon(self, fleet_type, default=None):
        if fleet_type not in self._icons:
            fleet_type = "default" if default is None else default
        icon = self._icons[fleet_type].pop(0)
        self._icons[fleet_type].append(icon)
        logger.debug("Got icon for fleet type {}".format(fleet_type))
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
        return self.time_is_out() or self.stopped

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

        class RunBehaviour(OneShotBehaviour):
            async def run(self):
                #  self.clear_stopped_agents()
                if not self.agent.simulation_running:
                    self.agent.kill_simulator.clear()
                    with self.agent.simulation_mutex:
                        all_agents = (
                            list(self.agent.manager_agents.values())
                            + list(self.agent.transport_agents.values())
                            + list(self.agent.customer_agents.values())
                            + list(self.agent.station_agents.values())
                            + list(self.agent.vehicle_agents.values())
                            + list(self.agent.bus_stop_agents.values())
                        )
                        while not all([agent.is_ready() for agent in all_agents]):
                            logger.debug("Waiting for all agents to be ready")
                            await asyncio.sleep(0.5)
                        for manager in self.agent.manager_agents.values():
                            manager.run_strategy()
                            logger.debug(
                                f"Running strategy {self.agent.default_strategies['fleetmanager']} to manager {manager.name}"
                            )
                        for transport in self.agent.transport_agents.values():
                            transport.run_strategy()
                            logger.debug(
                                f"Running strategy {self.agent.default_strategies['transport']} to transport {transport.name}"
                            )
                        for customer in self.agent.customer_agents.values():
                            customer.run_strategy()
                            logger.debug(
                                f"Running strategy {self.agent.default_strategies['customer']} to customer {customer.name}"
                            )
                        for station in self.agent.station_agents.values():
                            station.run_strategy()
                            logger.debug(
                                f"Running strategy {self.agent.default_strategies['station']} to station {station.name}"
                            )
                        for vehicle in self.agent.vehicle_agents.values():
                            vehicle.run_strategy()
                            logger.debug(
                                f"Running strategy {self.agent.default_strategies['vehicle']} to vehicle {vehicle.name}"
                            )
                        #for stop in self.agent.bus_stop_agents.values():
                        #    stop.run_strategy()
                        #    logger.debug(
                        #        f"Running strategy {self.agent.default_strategies['stop']} to stop {stop.name}"
                        #    )

                    self.agent.simulation_running = True
                    self.agent.simulation_init_time = time.time()

                    for delay in self.agent.delayed_launch_agents:
                        agents = self.agent.delayed_launch_agents[delay]
                        start_time = datetime.fromtimestamp(
                            self.agent.simulation_init_time + delay
                        )
                        self.agent.add_behaviour(
                            DelayedLaunchBehaviour(agents, start_at=start_time)
                        )

                    logger.success("Simulation started.")

        self.add_behaviour(RunBehaviour())

    async def stop(self):
        """
        Finishes the simulation and prints simulation stats.
        Tasks done when a simulation is stopped:
            #. Stop participant agents.
            #. Print stats.
            #. Stop fleetmanager agent.
        """
        self.simulation_time = self.get_simulation_time()
        await self.directory_agent.stop()

        logger.info("Stopping simulation...")

        logger.info(
            "Terminating... ({0:.1f} seconds elapsed)".format(self.simulation_time)
        )

        coroutines = await self.stop_agents()

        await asyncio.gather(*coroutines)

        await self.generate_metrics()

        await super().stop()


    async def generate_metrics(self):

        self.generate_all_events()

        statistics = self.metrics_class['mobility_metrics']

        #Create a instance
        statistics = statistics()

        the_log = self.events_log

        statistics.run(events_log=the_log)

    def generate_all_events(self):

        self.events_log = Log()

        if len(self.customer_agents) > 0:

            for customer in self.customer_agents.values():

                event_storen = customer.events_store

                partial_log = event_storen.generate_partial_log()

                self.events_log.add_events(partial_log)

        if len(self.transport_agents) > 0:

            for transport in self.transport_agents.values():

                event_storen = transport.events_store

                partial_log = event_storen.generate_partial_log()

                self.events_log.add_events(partial_log)

        if len(self.station_agents) > 0:

            for station in self.station_agents.values():

                event_storen = station.events_store

                partial_log = event_storen.generate_partial_log()

                self.events_log.add_events(partial_log)

        if len(self.manager_agents) > 0:

            for manager in self.manager_agents.values():

                event_storen = manager.events_store

                partial_log = event_storen.generate_partial_log()

                self.events_log.add_events(partial_log)

        self.events_log.adjust_timestamps(simulator_timestamp=str(self.simulation_init_time))

        self.events_log.sort_by_timestamp(reverse=False)

    async def write_file(self, filename):
        """
        Writes the dataframes collected by ``collect_stats`` in JSON or Excel format.

        Args:
            filename (str): name of the output file to be written.
            fileformat (str): format of the output file. Choices: json or excel
        """

        self.generate_all_events()
        log_events = self.events_log.all_events()

        with open(filename, "w") as f:
            f.seek(0)
            json.dump(log_events, f, indent=4)



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

    # New vehicle
    @property
    def vehicle_agents(self):
        """
        Gets the dict of registered stations

        Returns:
            dict: a dict of ``StationAgent`` with the name in the key
        """
        return self.get("vehicle_agents")

    # Bus line
    @property
    def bus_stop_agents(self):
        return self.get("bus_stop_agents")

    @property
    def bus_lines(self):
        return self.get("bus_lines")

    async def index_controller(self, request):
        """
        Web controller that returns the index page of the simulator.

        Returns:
            dict: the name of the template, the data to be pre-processed in the template
        """
        return {"port": self.config.http_port, "ip": self.config.http_ip}

    async def init_controller(self, request):
        return {"coords": self.config.coords[0], "zoom": self.config.zoom}

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
                            "children": [ { "status": 24, "name": " michaelstewart", "icon": "fa-lib" } ]
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
            "transports": [
                transport.to_json()
                for transport in self.transport_agents.values()
                if transport.is_launched
            ],
            "customers": [
                customer.to_json()
                for customer in self.customer_agents.values()
                if customer.is_launched
            ],
            "vehicles": [
                vehicle.to_json()
                for vehicle in self.vehicle_agents.values()
                if vehicle.is_launched
            ],
            "tree": self.generate_tree(),
            "stats": self.get_stats(),
            "stations": [station.to_json() for station in self.station_agents.values()] + [stop.to_json() for stop in self.bus_stop_agents.values()],
            # Bus line
            #"stops": [stop.to_json() for stop in self.bus_stop_agents.values()],
        }
        return result

    def generate_tree(self):
        """
        Generates the tree view in JSON format to be showed in the sidebar.

        Returns:
            dict: a dict with all the agents in the simulator, with their name, status and icon.
        """
        tree = {
            "name": "Agents",
            "children": [
                {
                    "name": "Transports",
                    "count": "{}".format(len(self.transport_agents)),
                    "children": [
                        {
                            "name": " {}".format(i.name.split("@")[0]),
                            #"status": i.status,
                            "icon": "fa-taxi",
                        }
                        for i in self.transport_agents.values()
                    ],
                },
                {
                    "name": "Customers",
                    "count": "{}".format(len(self.customer_agents)),
                    "children": [
                        {
                            "name": " {}".format(i.name.split("@")[0]),
                            #"status": i.status,
                            "icon": "fa-lib",
                        }
                        for i in self.customer_agents.values()
                    ],
                },
                {
                    "name": "Vehicles",
                    "count": "{}".format(len(self.vehicle_agents)),
                    "children": [
                        {
                            "name": " {}".format(i.name.split("@")[0]),
                            #"status": i.status,
                            "icon": "fa-vehicle",
                        }
                        for i in self.vehicle_agents.values()
                    ],
                },
                {
                    "name": "Stations",
                    "count": "{}".format(len(self.station_agents)),
                    "children": [
                        {
                            "name": " {}".format(i.name.split("@")[0]),
                            # "status": i.status,
                            "icon": "fa-station",
                        }
                        for i in self.station_agents.values()
                    ],
                },
            ],
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

        totaltime = self.get_simulation_time()

        return {
            "totaltime": "{0:.2f}".format(totaltime if totaltime is not None else 0.0),
            "finished": self.is_simulation_finished(),
            "is_running": self.simulation_running,
        }

    async def run_controller(self, request):
        """
        Web controller that starts the simulator.

        Returns:
            dict: no template is returned since this is an AJAX controller, an empty data dict is returned
        """
        self.run()
        return {"status": "ok"}

    async def stop_agents_controller(self, request):
        """
        Web controller that stops all the customer and transport agents.

        Returns:
            dict: no template is returned since this is an AJAX controller, a dict with status=done
        """
        self.stopped = True
        return {"status": "done"}

    async def download_events_json_controller(self, request):
        """
        Web controller that returns a JSON file with the simulation events.

        Returns:
            Response: a Response of type "attachment" with the file content.
        """
        headers = {"Content-Disposition": "Attachment; filename=events_simulation.json"}

        output = io.StringIO()

        self.generate_all_events()

        log_events = self.events_log.all_events()

        json.dump(log_events, output, indent=4)

        return aioweb.Response(body=output.getvalue(), headers=headers)

    def clear_agents(self):
        """
        Resets the set of transports and customers. Resets the simulation clock.
        """
        self.set("manager_agents", {})
        self.set("transport_agents", {})
        self.set("customer_agents", {})
        self.set("station_agents", {})
        self.set("vehicle_agents", {})
        self.set("bus_stop_agents", {})
        self.set("bus_lines", {})
        self.simulation_time = None
        self.simulation_init_time = None

    def clear_stopped_agents(self):
        """
        Removes from the transport and customer sets every agent that is stopped.
        """
        agents = self.get("manager_agents")
        self.set(
            "manager_agents",
            {jid: agent for jid, agent in agents.items() if not agent.stopped},
        )
        agents = self.get("transport_agents")
        self.set(
            "transport_agents",
            {jid: agent for jid, agent in agents.items() if not agent.stopped},
        )
        agents = self.get("customer_agents")
        self.set(
            "customer_agents",
            {jid: agent for jid, agent in agents.items() if not agent.stopped},
        )
        agents = self.get("station_agents")
        self.set(
            "station_agents",
            {jid: agent for jid, agent in agents.items() if not agent.stopped},
        )
        # Bus line
        agents = self.get("bus_stop_agents")
        self.set(
            "bus_stop_agents",
            {jid: agent for jid, agent in agents.items() if not agent.stopped},
        )
        self.simulation_time = None
        self.simulation_init_time = None

    #New and compact
    async def stop_agents(self):
        self.kill_simulator.set()
        self.simulation_running = False

        categories = {
            "manager": self.manager_agents,
            "transport": self.transport_agents,
            "customer": self.customer_agents,
            "station": self.station_agents,
            "vehicle": self.vehicle_agents,
            "bus_stop": self.bus_stop_agents,
        }

        async def stop_agent(agent):
            try:
                return await agent.stop()
            except Exception as e:
                logger.error(f"Error stopping agent {agent.name}: {e}")
                return None

        coroutines = [
            stop_agent(agent)
            for agents in categories.values()
            for agent in agents.values()
        ]

        return coroutines

    async def async_start_agent(self, agent):
        await agent.start()

    async def create_directory_agent(self, name, password):
        agent = DirectoryFactory.create_agent(domain=self.jid.domain,
                                              name=name,
                                              password=password,
                                              default_strategy=self.default_strategies['directory'],
                                              )
        self.set_directory(agent)
        agent.run_strategy()
        await agent.start()

    def create_fleetmanager_agent(
        self, name, password, fleet_type, strategy=None, icon=None
    ):
        agent = FleetManagerFactory.create_agent(domain=self.jid.domain,
                                                name=name,
                                                password=password,
                                                default_strategy=self.default_strategies['fleetmanager'],
                                                strategy=strategy,
                                                jid_directory=self.get_directory().jid,
                                                fleet_type=fleet_type,
                                                )
        if self.simulation_time:
            agent.run_strategy()

        self.add_manager(agent)

        agent.is_launched = True

        return agent

    def create_transport_agent(self,
                               name,
                               password,
                               class_,
                               fleet_type,
                               position,
                               service,
                               strategy=None,
                               autonomy=None,
                               current_autonomy=None,
                               speed=None,
                               optional=None,
                               delayed=False,
                               capacity=None,
                               line=None
                               ):

        agent = TransportFactory.create_agent(domain=self.jid.domain,
                                              jid_directory=self.get_directory().jid,
                                              route_host=self.route_host,
                                              bbox=self.config.coords[1],
                                              name=name,
                                              password=password,
                                              class_=class_,
                                              fleet_type=fleet_type,
                                              strategy=strategy,
                                              default_strategy=self.default_strategies['transport'],
                                              position=position,
                                              services=service,
                                              autonomy=autonomy,
                                              current_autonomy=current_autonomy,
                                              speed=speed,
                                              optional=optional,
                                              capacity=capacity,
                                              line=line,
                                              lines=self.bus_lines
                                              )

        if self.simulation_running:
            agent.run_strategy()

        self.add_transport(agent)

        if not delayed:
            agent.is_launched = True  # TODO

        return agent

    def create_customer_agent(
        self,
        name,
        password,
        class_,
        fleet_type,
        position=None,
        strategy=None,
        target=None,
        delayed=False,
        speed=None,
        line=None
    ):
        agent = CustomerFactory.create_agent(domain=self.jid.domain,
                                            name=name,
                                            password=password,
                                            class_=class_,
                                            default_strategy=self.default_strategies['customer'],
                                            strategy=strategy,
                                            jid_directory=self.get_directory().jid,
                                            fleet_type=fleet_type,
                                            route_host=self.route_host,
                                            bbox=self.config.coords[1],
                                            position=position,
                                            speed=speed,
                                            target=target,
                                            line=line,
                                            )

        if self.simulation_running:
            agent.run_strategy()

        self.add_customer(agent)

        if not delayed:
            agent.is_launched = True  # TODO

        return agent

    def create_station_agent(
        self, name, password, position, class_, services, strategy=None
    ):

        agent = StationFactory.create_agent(domain=self.jid.domain,
                                            name=name,
                                            password=password,
                                            default_strategy=self.default_strategies['station'],
                                            class_=class_,
                                            simulatorjid=self.simulatorjid,
                                            strategy=strategy,
                                            jid_directory=self.get_directory().jid,
                                            route_host=self.route_host,
                                            bbox=self.config.coords[1],
                                            position=position,
                                            services=services,
                                            )
        if self.simulation_running:
            agent.run_strategy()

        self.add_station(agent)

        agent.is_launched = True  # TODO

        return agent

    def create_vehicle_agent(self,
                            name,
                            password,
                            position,
                            fleet_type=None,
                            strategy=None,
                            speed=None,
                            delayed=False,
                            target=None,
                            ):

        agent = VehicleFactory.create_agent(domain=self.jid.domain,
                                            name=name,
                                            password=password,
                                            default_strategy=self.default_strategies['vehicle'],
                                            strategy=strategy,
                                            jid_directory=self.get_directory().jid,
                                            bbox=self.config.coords[1],
                                            fleet_type=fleet_type,
                                            route_host=self.route_host,
                                            position=position,
                                            speed=speed,
                                            target=target,
                                            )

        if self.simulation_running:
            agent.run_strategy()

        self.add_vehicle(agent)

        if not delayed:
            agent.is_launched = True

        return agent

    # bus line
    def create_bus_stop_agent(
        self, id, name, password, class_, position, lines, strategy=None, services=None,
    ):
        """
        Create a customer agent.

        Args:
            name (str): name of the agent
            password (str): password of the agent
            position (list): initial coordinates of the agent
            power (int): power of the station agent in kW
            places (int): destination coordinates of the agent
            strategy (class, optional): strategy class of the agent
        """
        name = (id, name)
        agent = TransportStopFactory.create_agent(domain=self.jid.domain,
                                                name=name,
                                                password=password,
                                                #default_strategy=self.default_strategies['stop'],
                                                class_=class_,
                                                simulatorjid=self.simulatorjid,
                                                strategy=strategy,
                                                jid_directory=self.get_directory().jid,
                                                route_host=self.route_host,
                                                bbox=self.config.coords[1],
                                                position=position,
                                                services=services,
                                                lines=lines,
                                                )

        if self.simulation_running:
            agent.run_strategy()

        self.add_bus_stop(agent)

        agent.is_launched = True

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

    def add_vehicle(self, agent):
        """
        Adds a new :class:`VehicleAgent` to the store.

        Args:
            agent (``VehicleAgent``): the instance of the VehicleAgent to be added
        """
        with self.simulation_mutex:
            self.get("vehicle_agents")[agent.name] = agent

    # Bus line
    def add_bus_stop(self, agent):
        """
        Adds a new :class:`BusStopAgent` to the store.

        Args:
            agent (``BusStopAgent``): the instance of the BusStopAgent to be added
        """
        with self.simulation_mutex:
            self.get("bus_stop_agents")[agent.name] = agent

    def add_line(self, line_id, stop_list, line_type):
        with self.simulation_mutex:
            self.get("bus_lines")[line_id] = {"stop_list": stop_list, "line_type": line_type}

    def get_simulation_time(self):
        """
        Returns the elapsed simulation time to the current time.
        If the simulation is not started it returns 0.

        Returns:
            float: the whole simulation time.
        """
        if not self.simulation_init_time:
            self.simulation_init_time = 0
            return 0
        if self.simulation_running:
            return time.time() - self.simulation_init_time
        return self.simulation_time


    def request_path(self, origin, destination):
        """
        Requests a path to the route server.

        Args:
            origin (list): the origin coordinates (lon, lat)
            destination (list): the target coordinates (lon, lat)

        Returns:
            list, float, float: the path as a list of points, the distance of the path, the estimated duration of the path
        """
        return async_request_path(self, origin, destination, self.route_host)


class DelayedLaunchBehaviour(TimeoutBehaviour):
    def __init__(self, agents, *args, **kwargs):
        self.agents = agents
        super().__init__(*args, **kwargs)

    async def run(self):
        for agent in self.agents:
            agent.is_launched = True
            await agent.start()


class CoordinationBehaviour(CyclicBehaviour):
    def __init__(self):
        super().__init__()

    async def inform_agent_position(self, agent_id, content):
        reply = Message()
        reply.to = str(agent_id)
        reply.set_metadata("protocol", COORDINATION_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)


    async def run(self):

        msg = await self.receive(timeout=5)
        logger.warning(
            "Agent[{}]: The agent has a mailbox size of ({})".format(
                self.agent.name, self.mailbox_size()
            )
        )
        if msg:
            performative = msg.get_metadata("performative")
            agent_id = msg.sender
            user_agent_id = json.loads(msg.body)["user_agent_id"].split('@')[0]
            host = json.loads(msg.body)["user_agent_id"].split('@')[1]
            object_type = json.loads(msg.body)["object_type"]


            if performative == REQUEST_PERFORMATIVE:

                logger.info(
                    "Agent[{}]: The agent received message from agent [{}]".format(
                        self.agent.name, agent_id
                    )
                )

                if object_type == "transport":

                    for transport in self.agent.transport_agents.values():
                        if transport.get_id() == user_agent_id:
                            agent_position = transport.get_position()
                            send_agent_id = user_agent_id + "@" + host

                            content = {"agent_position": agent_position, "user_agent_id": send_agent_id}
                            await self.inform_agent_position(agent_id, content)

                if object_type == "customer":

                    for customer in self.agent.customer_agents.values():

                        if customer.get_id() == user_agent_id:
                            agent_position = customer.get_position()
                            send_agent_id = user_agent_id + "@" + host

                            content = {"agent_position": agent_position, "user_agent_id": send_agent_id}
                            await self.inform_agent_position(agent_id, content)

                            logger.debug(
                                "Agent[{}]: The agent send msg to [{}]".format(
                                    self.agent.name, agent_id
                                )
                            )
