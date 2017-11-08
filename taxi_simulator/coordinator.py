# -*- coding: utf-8 -*-

"""Main module."""
import json
import faker
import logging

from spade.ACLMessage import ACLMessage
from spade.Agent import Agent
from spade.Behaviour import Behaviour, ACLTemplate, MessageTemplate

from taxi import TaxiAgent
from passenger import PassengerAgent
from utils import random_position, simulator_aid, CREATE_PROTOCOL

logger = logging.getLogger("CoordinatorAgent")


class CoordinatorAgent(Agent):
    def __init__(self, agentjid, password, debug):
        self.taxi_agents = {}
        self.passenger_agents = {}

        self.faker = faker.Factory.create()

        Agent.__init__(self, agentjid=agentjid, password=password, debug=debug)

    def _setup(self):
        logger.info("Coordinator agent running")
        self.wui.setPort(9000)
        self.wui.start()
        logger.info("Web interface running at http://127.0.0.1:{}/app".format(self.wui.port))

        self.wui.setTemplatePath("taxi_simulator/templates")

        tpl = ACLTemplate()
        tpl.setProtocol(CREATE_PROTOCOL)
        template = MessageTemplate(tpl)
        self.addBehaviour(CreateAgent(), template)

        self.wui.registerController("app", self.index_controller)
        self.wui.registerController("entities", self.entities_controller)
        self.wui.registerController("generate", self.generate_controller)
        self.wui.registerController("move", self.move_random_controller)

    def index_controller(self):
        return "index.html", {}

    def entities_controller(self):
        result = {
            "taxis": [taxi.to_json() for taxi in self.taxi_agents.values()],
            "passengers": [passenger.to_json() for passenger in self.passenger_agents.values()],
        }
        return None, result

    def generate_controller(self):
        logger.info("Creating taxis.")
        self.create_agent("taxi", 3)
        logger.info("Creating passengers.")
        self.create_agent("passenger", 3)
        return None, {"status": "done"}

    def move_random_controller(self):
        taxi = self.taxi_agents.values()[0]
        dest = random_position()
        logger.info("Moving taxi {} from {} to {}".format(taxi.agent_id, taxi.current_pos, dest))
        taxi.move_to(dest)
        return None, {"status": "done"}

    def stop_agents(self):
        for name, agent in self.taxi_agents.items():
            logger.info("Stopping taxi {}".format(name))
            agent.stop()
        del self.taxi_agents
        for name, agent in self.passenger_agents.items():
            logger.info("Stopping passenger {}".format(name))
            agent.stop()
        del self.passenger_agents

    def create_agent(self, type_, number=1):
        msg = ACLMessage()
        msg.addReceiver(simulator_aid)
        msg.setProtocol(CREATE_PROTOCOL)
        content = {
            "type": type_,
            "number": number
        }
        msg.setContent(json.dumps(content))
        self.send(msg)


class CreateAgent(Behaviour):
    def _process(self):
        msg = self._receive(block=True)
        content = json.loads(msg.content)
        type_ = content["type"]
        number = content["number"]
        if type_ == "taxi":
            for _ in range(number):
                position = random_position()
                name = self.myAgent.faker.user_name()
                password = self.myAgent.faker.password()
                jid = name + "@127.0.0.1"
                taxi = TaxiAgent(jid, password, debug=[])
                taxi.set_id(name)
                taxi.set_position(position)
                self.myAgent.taxi_agents[jid] = taxi
                taxi.start()
                logger.info("Created taxi {} at position {}".format(name, position))
        elif type_ == "passenger":
            for _ in range(number):
                position = random_position()
                name = self.myAgent.faker.user_name()
                password = self.myAgent.faker.password()
                jid = name + "@127.0.0.1"
                passenger = PassengerAgent(jid, password, debug=[])
                passenger.set_id(name)
                passenger.set_position(position)
                self.myAgent.passenger_agents[jid] = passenger
                passenger.start()
                logger.info("Created passenger {} at position {}".format(name, position))
