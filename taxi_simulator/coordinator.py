# -*- coding: utf-8 -*-
import io
import json
import logging
import random
import string
import threading
import os

import pandas as pd
import time
from aiohttp import web as aioweb
import xlsxwriter

import faker
from spade.agent import Agent
from spade.template import Template

from .helpers import random_position
from .passenger import PassengerAgent
from .taxi import TaxiAgent
from .utils import load_class, StrategyBehaviour, status_to_str, request_path, avg
from .protocol import REQUEST_PROTOCOL

logger = logging.getLogger("CoordinatorAgent")
faker_factory = faker.Factory.create()


class CoordinatorAgent(Agent):
    """
    Coordinator agent that manages the requests between taxis and passengers
    """

    def __init__(self, agentjid, password, http_port, ip_address):

        super().__init__(jid=agentjid, password=password)

        self.simulation_mutex = threading.Lock()
        self.simulation_running = False
        self.simulation_time = None
        self.simulation_init_time = None
        self.kill_simulator = threading.Event()
        self.kill_simulator.clear()
        self.lock = threading.RLock()
        self.route_id = None

        self.strategy = None
        self.coordinator_strategy = None
        self.taxi_strategy = None
        self.passenger_strategy = None

        self.http_port = http_port
        self.ip_address = ip_address
        self.template_path = os.path.dirname(__file__) + os.sep + "templates"

        self.clear_agents()

    def setup(self):
        logger.info("Coordinator agent running")
        self.web.add_get("/app", self.index_controller, "index.html")
        self.web.add_get("/entities", self.entities_controller, None)
        self.web.add_get("/run", self.run_controller, None)
        self.web.add_get("/stop", self.stop_agents_controller, None)
        self.web.add_get("/clean", self.clean_controller, None)
        self.web.add_get("/download/excel/", self.download_stats_excel_controller, None, raw=True)
        self.web.add_get("/download/json/", self.download_stats_json_controller, None, raw=True)
        self.web.add_get("/generate/taxis/{ntaxis}/passengers/{npassengers}", self.generate_controller, None)

        self.web.app.router.add_static("/assets", os.path.dirname(os.path.realpath(__file__)) + "/templates/assets")

        self.web.start(port=self.http_port, templates_path=self.template_path)
        logger.info("Web interface running at http://127.0.0.1:{}/app".format(self.http_port))

    @property
    def taxi_agents(self):
        """
        Gets the dict of registered taxis

        Returns:
            dict: a dict of ``TaxiAgent`` with the name in the key
        """
        return self.get("taxi_agents")

    @property
    def passenger_agents(self):
        """
        Gets the dict of registered passengers

        Returns:
            dict: a dict of ``PassengerAgent`` with the name in the key
        """
        return self.get("passenger_agents")

    def add_taxi(self, agent):
        """
        Adds a new ``TaxiAgent`` to the store.

        Args:
            agent (``TaxiAgent``): the instance of the TaxiAgent to be added
        """
        with self.simulation_mutex:
            self.get("taxi_agents")[agent.name] = agent

    def add_passenger(self, agent):
        """
        Adds a new :class:`PassengerAgent` to the store.

        Args:
            agent (``PassengerAgent``): the instance of the PassengerAgent to be added
        """
        with self.simulation_mutex:
            self.get("passenger_agents")[agent.name] = agent

    def set_strategies(self, coordinator_strategy, taxi_strategy, passenger_strategy):
        """
        Gets the strategy strings and loads their classes. This strategies are prepared to be injected into any
        new taxi or passenger agent.

        Args:
            coordinator_strategy (str): the path to the coordinator strategy
            taxi_strategy (str): the path to the taxi strategy
            passenger_strategy (str): the path to the passenger strategy
        """
        self.coordinator_strategy = load_class(coordinator_strategy)
        self.taxi_strategy = load_class(taxi_strategy)
        self.passenger_strategy = load_class(passenger_strategy)
        logger.debug("Loaded strategy classes: {}, {} and {}".format(self.coordinator_strategy,
                                                                     self.taxi_strategy,
                                                                     self.passenger_strategy))

    def run_simulation(self):
        """
        Starts the simulation
        """
        self.clear_stopped_agents()
        if not self.simulation_running:
            self.kill_simulator.clear()
            if not self.strategy:
                self.add_strategy(self.coordinator_strategy)
            with self.simulation_mutex:
                for taxi in self.taxi_agents.values():
                    taxi.add_strategy(self.taxi_strategy)
                    logger.debug(f"Adding strategy {self.taxi_strategy} to taxi {taxi.name}")
                for passenger in self.passenger_agents.values():
                    passenger.add_strategy(self.passenger_strategy)
                    logger.debug(f"Adding strategy {self.passenger_strategy} to passenger {passenger.name}")

            self.simulation_running = True
            self.simulation_init_time = time.time()
            logger.info("Simulation started.")

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

    def add_strategy(self, strategy_class):
        """
        Injects the strategy by instantiating the ``strategy_class``.
        Since the ``strategy_class`` inherits from ``spade.Behaviour.Behaviour``,
        the new strategy is added as a behaviour to the agent.

        Args:
            strategy_class (class): the class to be instantiated.
        """
        template = Template()
        template.set_metadata("protocol", REQUEST_PROTOCOL)
        self.strategy = strategy_class()
        self.add_behaviour(self.strategy, template)

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

    async def index_controller(self, request):
        """
        Web controller that returns the index page of the simulator.

        Returns:
            dict: the name of the template, the data to be pre-processed in the template
        """
        return {"port": self.http_port, "ip": self.ip_address}

    async def run_controller(self, request):
        """
        Web controller that starts the simulator.

        Returns:
            dict: no template is returned since this is an AJAX controller, an empty data dict is returned
        """
        self.run_simulation()
        return {"status": "ok"}

    async def generate_controller(self, request):
        ntaxis = request.match_info["ntaxis"]
        npassengers = request.match_info["npassengers"]
        self.create_agents_batch(TaxiAgent, int(ntaxis))
        self.create_agents_batch(PassengerAgent, int(npassengers))
        self.clear_stopped_agents()
        return {"status": "ok"}

    async def entities_controller(self, request):
        """
        Web controller that returns a dict with the entities of the simulator and their statuses.

        Example of the entities returned data::

            {
                "passengers": [
                    {
                        "status": 24,
                        "taxi": "taxi2@127.0.0.1",
                        "dest": [ 39.463356, -0.376463 ],
                        "waiting": 3.25,
                        "position": [ 39.460568, -0.352529 ],
                        "id": "michaelstewart"
                    }
                ],
                "taxis": [
                    {
                        "status": 11,
                        "passenger": "michaelstewart@127.0.0.1",
                        "assignments": 1,
                        "path": [
                                 [ 39.478328, -0.406712 ],
                                 [ 39.478317, -0.406814 ],
                                 [ 39.460568, -0.352529 ]
                                ],
                        "dest": [ 39.460568, -0.352529 ],
                        "position": [ 39.468131, -0.39685 ],
                        "speed": 327.58,
                        "id": "taxi2",
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
                            "children": [ { "status": 11, "name": " taxi2", "icon": "fa-taxi" } ]
                        },
                        {
                            "count": "1",
                            "name": "Passengers",
                            "children": [ { "status": 24, "name": " michaelstewart", "icon": "fa-user" } ]
                        }
                    ]
                },
                "authenticated": False
            }

        Returns:
            dict:  no template is returned since this is an AJAX controller, a dict with the list of taxis, the list of passengers, the tree view to be showed in the sidebar and the stats of the simulation.
        """
        result = {
            "taxis": [taxi.to_json() for taxi in self.taxi_agents.values()],
            "passengers": [passenger.to_json() for passenger in self.passenger_agents.values()],
            "tree": self.generate_tree(),
            "stats": self.get_stats()
        }
        return result

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
        Web controller that stops all the passenger and taxi agents.

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
        df_avg, taxi_df, passenger_df = self.get_stats_dataframes()
        df_avg.to_excel(writer, sheet_name='Simulation')
        passenger_df.to_excel(writer, sheet_name='Passengers')
        taxi_df.to_excel(writer, sheet_name='Taxis')
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
        df_avg, taxi_df, passenger_df = self.get_stats_dataframes()

        data = {
            "simulation": json.loads(df_avg.to_json(orient="index"))["0"],
            "passengers": json.loads(passenger_df.to_json(orient="index")),
            "taxis": json.loads(taxi_df.to_json(orient="index"))
        }

        json.dump(data, output, indent=4)

        return aioweb.Response(
            body=output.getvalue(),
            headers=headers
        )

    def clear_agents(self):
        """
        Resets the set of taxis and passengers. Resets the simulation clock.
        """
        self.set("taxi_agents", {})
        self.set("passenger_agents", {})
        self.simulation_time = None
        self.simulation_init_time = None

    def clear_stopped_agents(self):
        """
        Removes from the taxi and passenger sets every agent that is stopped.
        """
        agents = self.get("taxi_agents")
        self.set("taxi_agents", {jid: agent for jid, agent in agents.items() if not agent.stopped})
        agents = self.get("passenger_agents")
        self.set("passenger_agents", {jid: agent for jid, agent in agents.items() if not agent.stopped})
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
        with self.lock:
            for name, agent in self.taxi_agents.items():
                logger.debug("Stopping taxi {}".format(name))
                agent.stop()
                agent.stopped = True
        with self.lock:
            for name, agent in self.passenger_agents.items():
                logger.debug("Stopping passenger {}".format(name))
                agent.stop()
                agent.stopped = True

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
                    "name": "Taxis",
                    "count": "{}".format(len(self.taxi_agents)),
                    "children": [
                        {
                            "name": " {}".format(i.name.split("@")[0]),
                            "status": i.status,
                            "icon": "fa-taxi"
                        } for i in self.taxi_agents.values()
                    ]
                },
                {
                    "name": "Passengers",
                    "count": "{}".format(len(self.passenger_agents)),
                    "children": [
                        {
                            "name": " {}".format(i.name.split("@")[0]),
                            "status": i.status,
                            "icon": "fa-user"
                        } for i in self.passenger_agents.values()
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
        if len(self.passenger_agents) > 0:
            waiting = avg([passenger.get_waiting_time() for passenger in self.passenger_agents.values()])
            total = avg(
                [passenger.total_time() for passenger in self.passenger_agents.values() if passenger.total_time()])
        else:
            waiting, total = 0, 0

        return {
            "waiting": "{0:.2f}".format(waiting),
            "totaltime": "{0:.2f}".format(total),
            "finished": self.is_simulation_finished(),
            "is_running": self.simulation_running,
        }

    def get_passenger_stats(self):
        """
        Creates a dataframe with the simulation stats of the passengers
        The dataframe includes for each passenger its name, waiting time, total time and status.

        Returns:
            ``pandas.DataFrame``: the dataframe with the passengers stats.
        """
        try:
            names, waitings, totals, statuses = zip(*[(p.name, p.get_waiting_time(),
                                                       p.total_time(), status_to_str(p.status))
                                                      for p in self.passenger_agents.values()])
        except ValueError:
            names, waitings, totals, statuses = [], [], [], []

        df = pd.DataFrame.from_dict({"name": names, "waiting_time": waitings, "total_time": totals, "status": statuses})
        return df

    def get_taxi_stats(self):
        """
        Creates a dataframe with the simulation stats of the taxis
        The dataframe includes for each taxi its name, assignments, traveled distance and status.

        Returns:
            ``pandas.DataFrame``: the dataframe with the taxis stats.
        """
        try:
            names, assignments, distances, statuses = zip(*[(t.name, t.num_assignments,
                                                             "{0:.2f}".format(sum(t.distances)),
                                                             status_to_str(t.status))
                                                            for t in self.taxi_agents.values()])
        except ValueError:
            names, assignments, distances, statuses = [], [], [], []
        df = pd.DataFrame.from_dict({"name": names,
                                     "assignments": assignments,
                                     "distance": distances,
                                     "status": statuses})
        return df

    def get_stats_dataframes(self):
        """
        Collects simulation stats and returns 3 dataframes with the information:
        A general dataframe with the average information, a dataframe with the taxi's information
        and a dataframe with the passenger's information.
        Returns:
            pandas.Dataframe, pandas.Dataframe, pandas.Dataframe: avg df, taxi df and passenger df
        """
        passenger_df = self.get_passenger_stats()
        passenger_df = passenger_df[["name", "waiting_time", "total_time", "status"]]
        taxi_df = self.get_taxi_stats()
        taxi_df = taxi_df[["name", "assignments", "distance", "status"]]
        stats = self.get_stats()
        df_avg = pd.DataFrame.from_dict({"Avg Waiting Time": [stats["waiting"]],
                                         "Avg Total Time": [stats["totaltime"]],
                                         "Simulation Finished": [stats["finished"]],
                                         "Simulation Time": [self.get_simulation_time()]
                                         })
        columns = ["Avg Waiting Time", "Avg Total Time", "Simulation Time", "Simulation Finished"]
        df_avg = df_avg[columns]

        return df_avg, taxi_df, passenger_df

    def is_simulation_finished(self):
        """
        Checks whether the simulation has finished or not.
        A simulation is finished if all passengers are at their destinations.

        Returns:
            bool: whether the simulation has finished or not.
        """
        return all([passenger.is_in_destination() for passenger in self.passenger_agents.values()])

    def create_agent(self, cls, name, password, position, target=None, speed=None):
        """
        Create an agent of type ``cls`` (TaxiAgent or PassengerAgent).

        Args:
            cls (class): class of the agent (TaxiAgent or PassengerAgent)
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
            cls (class): class of the agent (TaxiAgent or PassengerAgent)
            name (str): name of the agent
            password (str): password of the agent
            position (list): initial coordinates of the agent
            target (list, optional): destination coordinates of the agent
            speed (float, optional): speed of the vehicle
        """
        jid = f"{name}@{self.jid.domain}"
        agent = cls(jid, password, loop=self.loop)
        agent.set_id(name)
        agent.set_coordinator(str(self.jid))
        agent.set_route_agent(self.route_id)
        await agent.set_position(position)

        if target:
            agent.set_target_position(target)
        if speed:
            agent.set_speed(speed)

        await agent.async_start(auto_register=True)

        if cls == TaxiAgent:
            strategy = self.taxi_strategy
            self.add_taxi(agent)
        else:  # cls == PassengerAgent:
            strategy = self.passenger_strategy
            self.add_passenger(agent)

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


class CoordinatorStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a coordinator strategy.
    You must overload the :func:`_process` method

    Helper functions:
        * :func:`get_taxi_agents`
        * :func:`get_passenger_agents`
    """

    async def on_start(self):
        self.logger = logging.getLogger("CoordinatorStrategy")
        self.logger.debug("Strategy {} started in coordinator".format(type(self).__name__))

    def get_taxi_agents(self):
        """
        Gets the list of registered taxis

        Returns:
            list: a list of ``TaxiAgent``
        """
        return self.get("taxi_agents").values()

    def get_passenger_agents(self):
        """
        Gets the list of registered passengers

        Returns:
            list: a list of ``PassengerAgent``
        """
        return self.get("passenger_agents").values()

    async def run(self):
        raise NotImplementedError
