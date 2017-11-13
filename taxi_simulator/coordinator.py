# -*- coding: utf-8 -*-

"""Main module."""
import json
import logging
import threading
import os

import faker
from spade.ACLMessage import ACLMessage
from spade.Agent import Agent
from spade.Behaviour import Behaviour, ACLTemplate, MessageTemplate

from passenger import PassengerAgent
from taxi import TaxiAgent
from utils import random_position, coordinator_aid, CREATE_PROTOCOL, REQUEST_PROTOCOL, REQUEST_PERFORMATIVE, load_class

logger = logging.getLogger("CoordinatorAgent")


class CoordinatorAgent(Agent):
    def __init__(self, agentjid, password, debug, http_port, backend_port, debug_level):
        self.simulation_running = False
        self.kill_simulator = threading.Event()
        self.kill_simulator.clear()
        self.lock = threading.RLock()
        self.taxi_agents = {}
        self.passenger_agents = {}

        self.coordinator_strategy = None
        self.taxi_strategy = None
        self.passenger_strategy = None

        self.faker = faker.Factory.create()

        self.http_port = http_port
        self.backend_port = backend_port
        self.debug_level = debug_level

        Agent.__init__(self, agentjid=agentjid, password=password, debug=debug)

    def _setup(self):
        logger.info("Coordinator agent running")
        self.wui.setPort(self.http_port)
        self.wui.start()
        logger.info("Web interface running at http://127.0.0.1:{}/app".format(self.wui.port))

        template_path = os.path.dirname(__file__) + os.sep + "templates"
        self.wui.setTemplatePath(template_path)

        self.wui.registerController("app", self.index_controller)
        self.wui.registerController("entities", self.entities_controller)
        self.wui.registerController("generate", self.generate_controller)
        self.wui.registerController("run", self.run_controller)
        self.wui.registerController("clean", self.clean_controller)

        # tpl = ACLTemplate()
        # tpl.setProtocol(CREATE_PROTOCOL)
        # template = MessageTemplate(tpl)
        # self.addBehaviour(CreateAgentBehaviour(), template)

    def set_strategies(self, coordinator_strategy, taxi_strategy, passenger_strategy):
        self.coordinator_strategy = load_class(coordinator_strategy)
        self.taxi_strategy = load_class(taxi_strategy)
        self.passenger_strategy = load_class(passenger_strategy)

    def run_simulation(self):
        if not self.simulation_running:
            self.add_strategy(self.coordinator_strategy)
            for taxi in self.taxi_agents.values():
                taxi.add_strategy(self.taxi_strategy)
            for passenger in self.passenger_agents.values():
                passenger.add_strategy(self.passenger_strategy)

            self.simulation_running = True
            logger.info("Simulation started.")

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
        }
        return None, result

    def generate_controller(self, taxis=1, passengers=1):
        taxis = int(taxis) if taxis is not None else 0
        passengers = int(passengers) if passengers is not None else 0
        logger.info("Creating {} taxis and {} passengers.".format(taxis, passengers))
        self.create_agent("taxi", number=taxis)
        self.create_agent("passenger", number=passengers)
        return None, {"status": "done"}

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

    def create_agent(self, type_, number=1):
        msg = ACLMessage()
        msg.addReceiver(coordinator_aid)
        msg.setProtocol(CREATE_PROTOCOL)
        msg.setPerformative(REQUEST_PERFORMATIVE)
        content = {
            "type": type_,
            "number": number
        }
        msg.setContent(json.dumps(content))
        self.send(msg)


class CreateAgentBehaviour(Behaviour):
    def _process(self):
        msg = self._receive(block=True)
        content = json.loads(msg.content)
        type_ = content["type"]
        number = content["number"]
        if type_ == "taxi":
            cls = TaxiAgent
            store = self.myAgent.taxi_agents
            strategy = self.myAgent.taxi_strategy
        else:  # type_ == "passenger":
            cls = PassengerAgent
            store = self.myAgent.passenger_agents
            strategy = self.myAgent.passenger_strategy

        for _ in range(number):
            with self.myAgent.lock:
                if self.myAgent.kill_simulator.isSet():
                    break
                position = random_position()
                name = self.myAgent.faker.user_name()
                password = self.myAgent.faker.password()
                jid = name + "@127.0.0.1"
                agent = cls(jid, password, debug=self.myAgent.debug_level)
                agent.set_id(name)
                agent.set_position(position)
                store[name] = agent
                agent.start()
                if self.myAgent.simulation_running:
                    agent.add_strategy(strategy)
                logger.debug("Created {} {} at position {}".format(type_, name, position))


class CoordinatorStrategyBehaviour(Behaviour):
    def onStart(self):
        self.logger = logging.getLogger("CoordinatorAgent")
        self.logger.debug("Strategy {} started in coordinator".format(type(self).__name__))

    def _process(self):
        raise NotImplementedError
