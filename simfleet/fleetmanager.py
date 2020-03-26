# -*- coding: utf-8 -*-

import json
from asyncio import CancelledError

import faker
from loguru import logger
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template

from .protocol import REQUEST_PROTOCOL, REGISTER_PROTOCOL, ACCEPT_PERFORMATIVE, REQUEST_PERFORMATIVE, \
    REFUSE_PERFORMATIVE
from .utils import StrategyBehaviour

faker_factory = faker.Factory.create()


class FleetManagerAgent(Agent):
    """
    FleetManager agent that manages the requests between transports and customers
    """

    def __init__(self, agentjid, password):

        super().__init__(jid=agentjid, password=password)
        self.strategy = None
        self.running_strategy = False
        self.transports_in_fleet = 0
        self.agent_id = None
        self.fleet_type = None
        self.registration = False
        self.directory_id = None
        self.fleet_icon = None
        self.stopped = False
        self.clear_agents()

    def clear_agents(self):
        """
        Resets the set of transports and customers. Resets the simulation clock.
        """
        self.set("transport_agents", {})

    async def setup(self):
        logger.info("FleetManager agent running")
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = TransportRegistrationForFleetBehaviour()
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

    def set_icon(self, icon):
        self.fleet_icon = icon

    def run_strategy(self):
        """
        Runs the strategy for the transport agent.
        """
        if not self.running_strategy:
            template = Template()
            template.set_metadata("protocol", REQUEST_PROTOCOL)
            self.add_behaviour(self.strategy(), template)
            self.running_strategy = True

    def set_registration(self, status):
        """
        Sets the status of registration
        Args:
            status (boolean): True if the transport agent has registered or False if not

        """
        self.registration = status

    def set_directory(self, directory_id):
        """
        Sets the directory JID address
        Args:
            directory_id (str): the DirectoryAgent jid

        """
        self.directory_id = directory_id

    def set_fleet_type(self, fleet_type):
        """
        Sets the type of service to the fleet
        Args:
            type_service (str): type of service

        """
        self.fleet_type = fleet_type


class TransportRegistrationForFleetBehaviour(CyclicBehaviour):

    async def on_start(self):
        logger.debug("Strategy {} started in manager".format(type(self).__name__))

    def add_transport(self, agent):
        """
        Adds a new ``TransportAgent`` to the store.

        Args:
            agent (``TransportAgent``): the instance of the TransportAgent to be added
        """
        self.agent.transports_in_fleet += 1
        self.get("transport_agents")[agent["name"]] = agent

    def remove_transport(self, key):
        """
        Erase a ``TransportAgent`` to the store.

        Args:
            agent (``TransportAgent``): the instance of the TransportAgent to be erased
        """
        if key in self.get("transport_agents"):
            del (self.get("transport_agents")[key])
            logger.debug("Deregistration of the TransporterAgent {}".format(key))
            self.agent.transports_in_fleet -= 1
        else:
            logger.debug("Cancelation of the registration in the Fleet")

    async def accept_registration(self, agent_id):
        """
        Send a ``spade.message.Message`` with an acceptance to transport to register in the fleet.
        """
        reply = Message()
        content = {"icon": self.agent.fleet_icon, "fleet_type": self.agent.fleet_type}
        reply.to = str(agent_id)
        reply.set_metadata("protocol", REGISTER_PROTOCOL)
        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def reject_registration(self, agent_id):
        """
        Send a ``spade.message.Message`` with an acceptance to transport to register in the fleet.
        """
        reply = Message()
        reply.to = str(agent_id)
        reply.set_metadata("protocol", REGISTER_PROTOCOL)
        reply.set_metadata("performative", REFUSE_PERFORMATIVE)
        reply.body = ""
        await self.send(reply)

    async def run(self):
        try:
            msg = await self.receive(timeout=5)
            if msg:
                performative = msg.get_metadata("performative")
                if performative == REQUEST_PERFORMATIVE:
                    content = json.loads(msg.body)
                    if content["fleet_type"] == self.agent.fleet_type:
                        self.add_transport(content)
                        await self.accept_registration(msg.sender)
                        logger.debug("Registration in the fleet {}".format(self.agent.name))
                    else:
                        await self.reject_registration(msg.sender)

                if performative == ACCEPT_PERFORMATIVE:
                    self.agent.set_registration(True)
                    logger.info("Registration in the dictionary of services")
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error("EXCEPTION in RegisterBehaviour of Manager {}: {}".format(self.agent.name, e))


class FleetManagerStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a coordinator strategy.
    You must overload the :func:`_process` method

    Helper functions:
        * :func:`get_transport_agents`
    """

    async def on_start(self):
        logger.debug("Strategy {} started in manager".format(type(self).__name__))

    def get_transport_agents(self):
        """
        Gets the list of registered transports

        Returns:
            list: a list of ``TransportAgent``
        """
        return self.get("transport_agents")

    async def send_registration(self):
        """
        Send a ``spade.message.Message`` with a proposal to directory to register.
        """
        logger.info("Manager {} sent proposal to register to directory {}".format(self.agent.name,
                                                                                  self.agent.directory_id))
        content = {
            "jid": str(self.agent.jid),
            "type": self.agent.fleet_type
        }
        msg = Message()
        msg.to = str(self.agent.directory_id)
        msg.set_metadata("protocol", REGISTER_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

    async def run(self):
        raise NotImplementedError
