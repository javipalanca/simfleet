# -*- coding: utf-8 -*-

import logging

import faker
from spade.agent import Agent
from spade.template import Template

from .utils import StrategyBehaviour
from .protocol import REQUEST_PROTOCOL

logger = logging.getLogger("FleetManagerAgent")
faker_factory = faker.Factory.create()


class FleetManagerAgent(Agent):
    """
    FleetManager agent that manages the requests between taxis and passengers
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
        Resets the set of taxis and passengers. Resets the simulation clock.
        """
        self.set("taxi_agents", {})

    async def setup(self):
        logger.info("FleetManager agent running")
        self.fleetName = faker_factory.user_name()

    def set_id(self, agent_id):
        """
        Sets the agent identifier

        Args:
            agent_id (str): The new Agent Id
        """
        self.agent_id = agent_id

    def add_strategy(self, strategy_class):
        """
        Sets the strategy for the taxi agent.

        Args:
            strategy_class (``TaxiStrategyBehaviour``): The class to be used. Must inherit from ``TaxiStrategyBehaviour``
        """
        template = Template()
        template.set_metadata("protocol", REQUEST_PROTOCOL)
        self.add_behaviour(strategy_class(), template)


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
        self.logger.debug("Strategy {} started in manager".format(type(self).__name__))

    def add_taxi(self, agent):
        """
        Adds a new ``TaxiAgent`` to the store.

        Args:
            agent (``TaxiAgent``): the instance of the TaxiAgent to be added
        """
        # with self.simulation_mutex:
        self.get("taxi_agents")[agent["name"]] = agent

    def get_out_taxi(self, key):
        """
        Erase a ``TaxiAgent`` to the store.

        Args:
            agent (``TaxiAgent``): the instance of the TaxiAgent to be erased
        """
        del(self.get("taxi_agents")[key])
        self.logger.debug("Deregistration of the TransporterAgent {}".format(key))

    def get_taxi_agents(self):
        """
        Gets the list of registered taxis

        Returns:
            list: a list of ``TaxiAgent``
        """
        return self.get("taxi_agents")

    def get_passenger_agents(self):
        """
        Gets the list of registered passengers

        Returns:
            list: a list of ``PassengerAgent``
        """
        return self.get("passenger_agents").values()

    async def run(self):
        raise NotImplementedError
