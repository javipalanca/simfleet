# -*- coding: utf-8 -*-

import logging
import json

import faker
from spade.agent import Agent
from spade.template import Template
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from .utils import StrategyBehaviour
from .protocol import REQUEST_PROTOCOL, REGISTER_PROTOCOL, PROPOSE_PERFORMATIVE, CANCEL_PERFORMATIVE, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE

logger = logging.getLogger("FleetManagerAgent")
faker_factory = faker.Factory.create()


class FleetManagerAgent(Agent):
    """
    FleetManager agent that manages the requests between transports and customers
    """

    def __init__(self, agentjid, password):

        super().__init__(jid=agentjid, password=password)
        self.strategy = None
        self.fleetName = None
        self.quantityFloat = None
        self.agent_id = None

        self.stopped = False
        self.clear_agents()

    def clear_agents(self):
        """
        Resets the set of transports and customers. Resets the simulation clock.
        """
        self.set("transport_agents", {})

    async def setup(self):
        logger.info("FleetManager agent running")
        self.fleetName = faker_factory.user_name()
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = RegisterBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning("Manager {} could not create RegisterBehaviour. Retrying...".format(self.agent_id))
                self.add_behaviour(register_behaviour, template)
        except Exception as e:
            logger.error("EXCEPTION creating RegisterBehaviour in Manager {}: {}".format(self.agent_id, e))

    def set_id(self, agent_id):
        """
        Sets the agent identifier

        Args:
            agent_id (str): The new Agent Id
        """
        self.agent_id = agent_id

    def add_strategy(self, strategy_class):
        """
        Sets the strategy for the transport agent.

        Args:
            strategy_class (``TaxiStrategyBehaviour``): The class to be used. Must inherit from ``TaxiStrategyBehaviour``
        """
        template = Template()
        template.set_metadata("protocol", REQUEST_PROTOCOL)
        self.add_behaviour(strategy_class(), template)


class RegisterBehaviour(CyclicBehaviour):

    async def on_start(self):
        self.logger = logging.getLogger("RegisterStrategy")
        self.logger.debug("Strategy {} started in manager".format(type(self).__name__))

    def add_transport(self, agent):
        """
        Adds a new ``TransportAgent`` to the store.

        Args:
            agent (``TransportAgent``): the instance of the TransportAgent to be added
        """
        self.get("transport_agents")[agent["name"]] = agent
        logger.info("Registration in the fleet {}".format(self.agent.fleetName))

    def get_out_transport(self, key):
        """
        Erase a ``TransportAgent`` to the store.

        Args:
            agent (``TransportAgent``): the instance of the TransportAgent to be erased
        """
        if key in self.get("transport_agents"):
            del(self.get("transport_agents")[key])
            self.logger.debug("Deregistration of the TransporterAgent {}".format(key))
        else:
            self.logger.debug("Cancelation of the registration in the Fleet")

    async def run(self):
        try:
            msg = await self.receive(timeout=5)
            if msg:
                performative = msg.get_metadata("performative")
                content = json.loads(msg.body)
                if performative == PROPOSE_PERFORMATIVE:
                    self.add_transport(content)
                elif performative == CANCEL_PERFORMATIVE:
                    self.get_out_transport(content["name"])
                    logger.debug("No registration in the fleet {}".format(self.agent.fleetName))
        except Exception as e:
            logger.error("EXCEPTION in Register Behaviour of Manager {}: {}".format(self.agent.name, e))


class CoordinatorStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a coordinator strategy.
    You must overload the :func:`_process` method

    Helper functions:
        * :func:`get_transport_agents`
    """

    async def on_start(self):
        self.logger = logging.getLogger("CoordinatorStrategy")
        self.logger.debug("Strategy {} started in manager".format(type(self).__name__))

    def get_transport_agents(self):
        """
        Gets the list of registered transports

        Returns:
            list: a list of ``TransportAgent``
        """
        return self.get("transport_agents")

    async def run(self):
        raise NotImplementedError
