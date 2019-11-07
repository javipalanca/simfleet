import json
from asyncio import CancelledError

from loguru import logger
from spade.agent import Agent
from spade.message import Message
from spade.template import Template

from .protocol import REGISTER_PROTOCOL, INFORM_PERFORMATIVE, ACCEPT_PERFORMATIVE, \
    CANCEL_PERFORMATIVE, REQUEST_PERFORMATIVE, QUERY_PROTOCOL
from .utils import StrategyBehaviour, CyclicBehaviour


class DirectoryAgent(Agent):
    def __init__(self, agentjid, password):
        super().__init__(jid=agentjid, password=password)
        self.strategy = None
        self.agent_id = None

        self.set("service_agents", {})
        self.stopped = False

    def set_id(self, agent_id):
        """
        Sets the agent identifier

        Args:
            agent_id (str): The new agent id
        """
        self.agent_id = agent_id

    def run_strategy(self):
        """
        Runs the strategy for the directory agent.
        """
        template = Template()
        template.set_metadata("protocol", QUERY_PROTOCOL)
        self.add_behaviour(self.strategy(), template)

    async def setup(self):
        logger.info("Directory agent running")
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = RegistrationBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning("Directory {} could not create RegisterBehaviour. Retrying...".format(self.agent_id))
                self.add_behaviour(register_behaviour, template)
        except Exception as e:
            logger.error("EXCEPTION creating RegisterBehaviour in Directory {}: {}".format(self.agent_id, e))


class RegistrationBehaviour(CyclicBehaviour):

    async def on_start(self):
        logger.debug("Strategy {} started in directory".format(type(self).__name__))

    def add_service(self, content):
        """
        Adds a new service to the store.

        Args:
            content (dict): content to be added
        """
        service = self.get("service_agents")
        if content["type"] in service:
            service[content["type"]][content["jid"]] = content
        else:
            service[content["type"]] = {content["jid"]: content}

    def remove_service(self, service_type, agent):
        """
        Erase a service from the store.

        Args:
            service_type (str): the service type to be erased
            agent (str): an str with the jid of the agent to be erased
        """
        del (self.get("service_agents")[service_type][agent])
        logger.debug("Deregistration of the Manager {} for service {}".format(agent, service_type))

    async def send_confirmation(self, agent_id):
        """
        Send a ``spade.message.Message`` with an acceptance to manager/station to register in the dictionary
        """
        reply = Message()
        reply.to = str(agent_id)
        reply.set_metadata("protocol", REGISTER_PROTOCOL)
        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
        await self.send(reply)

    async def run(self):
        try:
            msg = await self.receive(timeout=5)
            if msg:
                agent_id = msg.sender
                performative = msg.get_metadata("performative")
                if performative == REQUEST_PERFORMATIVE:
                    content = json.loads(msg.body)
                    self.add_service(content)
                    logger.debug("Registration in the dictionary {}".format(self.agent.name))
                    await self.send_confirmation(agent_id)
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error("EXCEPTION in DirectoryRegister Behaviour of Directory {}: {}".format(self.agent.name, e))


class DirectoryStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a directory strategy.
    """

    async def on_start(self):
        logger.debug("Strategy {} started in directory".format(type(self).__name__))

    async def send_services(self, agent_id, type_service):
        """
        Send a message to the customer or transport with the current information of the type of service they need.

        Args:
            agent_id (str): the id of the manager/station
            type_service (str): the type of service
        """
        reply = Message()
        reply.to = str(agent_id)
        reply.set_metadata("protocol", QUERY_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        reply.body = json.dumps(self.get("service_agents")[type_service])
        await self.send(reply)

    async def send_negative(self, agent_id):
        """
        Sends a message to the current assigned manager/station to cancel the registration.

        Args:
            agent_id (str): the id of the manager/station
        """
        reply = Message()
        reply.to = str(agent_id)
        reply.set_metadata("protocol", QUERY_PROTOCOL)
        reply.set_metadata("performative", CANCEL_PERFORMATIVE)
        await self.send(reply)

    async def run(self):
        msg = await self.receive(timeout=5)
        if msg:
            performative = msg.get_metadata("performative")
            agent_id = msg.sender
            request = msg.body
            if performative == REQUEST_PERFORMATIVE:
                logger.info("Directory {} received message from customer/transport {}".format(self.agent.name,
                                                                                              agent_id))
                if request in self.get("service_agents"):
                    await self.send_services(agent_id, msg.body)
                else:
                    await self.send_negative(agent_id)
