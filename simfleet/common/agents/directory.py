import json
from asyncio import CancelledError

from loguru import logger
from spade.agent import Agent
from spade.agent import CyclicBehaviour
from spade.message import Message
from spade.template import Template

from simfleet.communications.protocol import (
    REGISTER_PROTOCOL,
    INFORM_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    REQUEST_PERFORMATIVE,
    QUERY_PROTOCOL,
)

from simfleet.utils.abstractstrategies import StrategyBehaviour

class DirectoryAgent(Agent):
    """
        DirectoryAgent is responsible for managing the registration of services and handling queries about available services in the system.

        Attributes:
            strategy (StrategyBehaviour): The strategy that dictates how the agent behaves.
            agent_id (str): Identifier of the agent.
            service_agents (dict): A dictionary to store the available services and agents that provide them.
            stopped (bool): A flag indicating if the agent has been stopped.
    """
    def __init__(self, agentjid, password):
        """
            Initializes the DirectoryAgent with its JID and password.
        """
        super().__init__(jid=agentjid, password=password)
        self.strategy = None
        self.agent_id = None

        self.set("service_agents", {})
        self.stopped = False

    def set_id(self, agent_id):
        """
        Sets the agent identifier.

        Args:
            agent_id (str): The new agent id.
        """
        self.agent_id = agent_id

    def run_strategy(self):
        """
        Runs the strategy assigned to the directory agent for managing the services.
        """
        template = Template()
        template.set_metadata("protocol", QUERY_PROTOCOL)
        self.add_behaviour(self.strategy(), template)

    async def setup(self):
        """
            Initializes the DirectoryAgent and adds the RegistrationBehaviour to handle service registrations.
        """
        logger.info("Directory agent {} running".format(self.name))
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = RegistrationBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning(
                    "Directory {} could not create RegisterBehaviour. Retrying...".format(
                        self.agent_id
                    )
                )
                self.add_behaviour(register_behaviour, template)
        except Exception as e:
            logger.error(
                "EXCEPTION creating RegisterBehaviour in Directory {}: {}".format(
                    self.agent_id, e
                )
            )


class RegistrationBehaviour(CyclicBehaviour):
    """
        Handles the registration process for agents (e.g., transport services, managers) to the directory.
        It manages the storage and removal of services offered by agents.
    """
    async def on_start(self):
        """
            Logs when the strategy starts running.
        """
        logger.debug("Strategy {} started in directory".format(type(self).__name__))

    def add_service(self, content):
        """
        Adds a new service to the directory’s service store.

        Args:
            content (dict): Information about the service to be added.
        """
        service = self.get("service_agents")
        if content["type"] in service:
            service[content["type"]][content["jid"]] = content
        else:
            service[content["type"]] = {content["jid"]: content}

    def remove_service(self, service_type, agent):
        """
        Removes a service from the directory’s store.

        Args:
            service_type (str): The type of service to be removed.
            agent (str): The JID of the agent whose service should be removed.
        """
        del self.get("service_agents")[service_type][agent]
        logger.debug(
            "Deregistration of the Manager {} for service {}".format(
                agent, service_type
            )
        )

    async def send_confirmation(self, agent_id):
        """
        Sends a message confirming the acceptance of the service registration.

        Args:
            agent_id (str): The JID of the agent to be confirmed.
        """
        reply = Message()
        reply.to = str(agent_id)
        reply.set_metadata("protocol", REGISTER_PROTOCOL)
        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
        await self.send(reply)

    async def run(self):
        """
            Handles the reception of registration requests and processes them accordingly.
        """
        try:
            msg = await self.receive(timeout=5)
            if msg:
                agent_id = msg.sender
                performative = msg.get_metadata("performative")
                if performative == REQUEST_PERFORMATIVE:
                    content = json.loads(msg.body)
                    services = content["type"]

                    if isinstance(services, list):
                        for service in services:
                            service_content = content.copy()
                            del service_content["type"]
                            service_content["type"] = service
                            self.add_service(service_content)
                            logger.debug(
                                "Registration in the dictionary: {} with service: {}".format(content["jid"], service)
                            )
                    else:
                        self.add_service(content)
                        logger.debug(
                            "Registration in the dictionary: {}".format(content["jid"])
                        )

                    await self.send_confirmation(agent_id)
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error(
                "EXCEPTION in DirectoryRegister Behaviour of Directory {}: {}".format(
                    self.agent.name, e
                )
            )


class DirectoryStrategyBehaviour(StrategyBehaviour):
    """
    Class to define and implement a custom strategy for the DirectoryAgent.
    """

    async def on_start(self):
        logger.debug("Strategy {} started in directory".format(type(self).__name__))

    async def send_services(self, agent_id, type_service):
        """
        Sends a message to the requesting agent (customer/transport) with the list of available services.

        Args:
            agent_id (str): The JID of the requesting agent.
            type_service (str): The type of service the agent is requesting.
        """
        reply = Message()
        reply.to = str(agent_id)
        reply.set_metadata("protocol", QUERY_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        reply.body = json.dumps(self.get("service_agents")[type_service])
        await self.send(reply)

    async def send_negative(self, agent_id):
        """
        Sends a cancellation message to the requesting agent (customer/transport) if no services are available.

        Args:
            agent_id (str): The JID of the requesting agent.
        """
        reply = Message()
        reply.to = str(agent_id)
        reply.set_metadata("protocol", QUERY_PROTOCOL)
        reply.set_metadata("performative", CANCEL_PERFORMATIVE)
        await self.send(reply)

    async def run(self):
        """
            Handles requests for services from customers or transport agents.
        """
        msg = await self.receive(timeout=5)
        logger.debug(
            "Directory {} has a mailbox size of {}".format(
                self.agent.name, self.mailbox_size()
            )
        )
        if msg:
            performative = msg.get_metadata("performative")
            agent_id = msg.sender
            request = msg.body
            if performative == REQUEST_PERFORMATIVE:

                logger.info(
                    "Directory {} received message from customer/transport {}".format(
                        self.agent.name, agent_id
                    )
                )

                if request in self.get("service_agents"):
                    await self.send_services(agent_id, msg.body)
                else:
                    await self.send_negative(agent_id)
