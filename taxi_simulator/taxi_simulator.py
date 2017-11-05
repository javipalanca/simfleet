# -*- coding: utf-8 -*-

"""Main module."""
import json
import logging

from spade.Agent import Agent
from spade.Behaviour import Behaviour, ACLTemplate, MessageTemplate

from structs import REGISTER_PROTOCOL

logger = logging.getLogger("SimulatorAgent")


class SimulatorAgent(Agent):
    def _setup(self):
        logger.info("Simulator agent running")
        self.wui.setPort(9000)
        self.wui.start()
        logger.info("Web interface running at http://localhost:{}".format(self.wui.port))
        self.taxis = {}
        self.passengers = {}

        self.wui.setTemplatePath("taxi_simulator/templates")

        tpl = ACLTemplate()
        tpl.setProtocol(REGISTER_PROTOCOL)
        template = MessageTemplate(tpl)
        self.addBehaviour(RegisterTaxiBehaviour(), template)

        self.wui.registerController("app", self.index_controller)
        self.wui.registerController("entities", self.entities_controller)

    def index_controller(self):
        return "index.html", {}

    def entities_controller(self):
        result = {
            "taxis": self.taxis,
            "passengers": self.passengers
        }
        return None, result


class RegisterTaxiBehaviour(Behaviour):
    def _process(self):
        msg = self._receive(block=True)
        newmsg = msg.createReply()
        content = json.load(msg.content)
        taxi_id = content["taxi_id"]
        if content["action"] == "register":
            self.myAgent.taxis[taxi_id] = content
            msg.content = '{"action": "registered"}'
        elif content["action"] == "deregister":
            if taxi_id in self.myAgent.taxis.keys():
                del self.myAgent.taxis[taxi_id]
                msg.content = '{"action": "deregistered"}'
        self.myAgent.send(newmsg)
