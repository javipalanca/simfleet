# -*- coding: utf-8 -*-

"""Main module."""
import json
import logging
import threading
import os

import time
from spade.Agent import Agent
from spade.Behaviour import Behaviour, ACLTemplate, MessageTemplate

from utils import REQUEST_PROTOCOL, load_class

logger = logging.getLogger("CoordinatorAgent")


class CoordinatorAgent(Agent):
    def __init__(self, agentjid, password, debug, http_port, backend_port, debug_level):
        self.simulation_running = False
        self.simulation_time = None
        self.kill_simulator = threading.Event()
        self.kill_simulator.clear()
        self.lock = threading.RLock()
        self.taxi_agents = {}
        self.passenger_agents = {}

        self.coordinator_strategy = None
        self.taxi_strategy = None
        self.passenger_strategy = None

        self.http_port = http_port
        self.backend_port = backend_port
        self.debug_level = debug_level

        Agent.__init__(self, agentjid=agentjid, password=password, debug=debug)

    def _setup(self):
        logger.info("Coordinator agent running")
        self.wui.setPort(self.http_port)
        self.wui.start()
        logger.info("Web interface running at http://127.0.0.1:{}/app".format(self.wui.port))

        self.template_path = os.path.dirname(__file__) + os.sep + "templates"
        self.wui.setTemplatePath(self.template_path)

        self.wui.registerController("app", self.index_controller)
        self.wui.registerController("entities", self.entities_controller)
        self.wui.registerController("run", self.run_controller)
        self.wui.registerController("clean", self.clean_controller)

    def add_taxi(self, agent):
        self.taxi_agents[agent.getName()] = agent

    def add_passenger(self, agent):
        self.passenger_agents[agent.getName()] = agent

    def set_strategies(self, coordinator_strategy, taxi_strategy, passenger_strategy):
        self.coordinator_strategy = load_class(coordinator_strategy)
        self.taxi_strategy = load_class(taxi_strategy)
        self.passenger_strategy = load_class(passenger_strategy)
        logger.debug("Loaded strategy classes: {}, {} and {}".format(self.coordinator_strategy,
                                                                     self.taxi_strategy,
                                                                     self.passenger_strategy))

    def run_simulation(self):
        if not self.simulation_running:
            self.add_strategy(self.coordinator_strategy)
            for taxi in self.taxi_agents.values():
                taxi.add_strategy(self.taxi_strategy)
            for passenger in self.passenger_agents.values():
                passenger.add_strategy(self.passenger_strategy)

            self.simulation_running = True
            self.simulation_time = time.time()
            logger.info("Simulation started.")

    def get_simulation_time(self):
        if not self.simulation_time:
            return 0
        return time.time() - self.simulation_time

    def add_strategy(self, strategy_class):
        tpl = ACLTemplate()
        tpl.setProtocol(REQUEST_PROTOCOL)
        template = MessageTemplate(tpl)
        self.addBehaviour(strategy_class(), template)

    def index_controller(self):
        return "index.html", {"port": self.backend_port}

    def run_controller(self):
        self.run_simulation()
        return None, {}

    def entities_controller(self):
        result = {
            "taxis": [taxi.to_json() for taxi in self.taxi_agents.values()],
            "passengers": [passenger.to_json() for passenger in self.passenger_agents.values()],
            "tree": self.generate_tree(),
            "stats": self.get_stats()
        }
        return None, result

    def clean_controller(self):
        self.stop_agents()
        self.taxi_agents = {}
        self.passenger_agents = {}
        return None, {"status": "done"}

    def stop_agents(self):
        self.kill_simulator.set()
        with self.lock:
            for name, agent in self.taxi_agents.items():
                logger.info("Stopping taxi {}".format(name))
                agent.stop()
        with self.lock:
            for name, agent in self.passenger_agents.items():
                logger.info("Stopping passenger {}".format(name))
                agent.stop()

    def generate_tree(self):
        tree = [
            {
                "text": "Taxis",
                "tags": ["{}".format(len(self.taxi_agents))],
                "nodes": [{
                    "text": " {}".format(i),
                    "icon": "fa fa-taxi"
                } for i in self.taxi_agents.keys()]
            },
            {
                "text": "Passengers",
                "tags": ["{}".format(len(self.passenger_agents))],
                "nodes": [{
                    "text": " {}".format(i),
                    "icon": "fa fa-user"
                } for i in self.passenger_agents.keys()]
            }
        ]
        return tree

    def get_stats(self):
        def avg(array):
            array_wo_nones = filter(None, array)
            return (sum(array_wo_nones, 0.0) / len(array_wo_nones)) if len(array_wo_nones) > 0 else 0.0

        waiting = avg([passenger.get_waiting_time() for passenger in self.passenger_agents.values()])
        total = avg([passenger.total_time() for passenger in self.passenger_agents.values()])
        return {
            "waiting": "{0:.2f}".format(waiting),
            "totaltime": "{0:.2f}".format(total),
            "finished": self.is_simulation_finished()
        }

    def is_simulation_finished(self):
        return all([passenger.is_in_destination() for passenger in self.passenger_agents.values()])


class CoordinatorStrategyBehaviour(Behaviour):
    def onStart(self):
        self.logger = logging.getLogger("CoordinatorAgent")
        self.logger.debug("Strategy {} started in coordinator".format(type(self).__name__))

    def _process(self):
        raise NotImplementedError
