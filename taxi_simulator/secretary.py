
import logging
import json
from spade.agent import Agent
from spade.template import Template
from spade.message import Message

from .utils import StrategyBehaviour, CyclicBehaviour
from .protocol import REQUEST_PROTOCOL, REGISTER_PROTOCOL, INFORM_PERFORMATIVE, ACCEPT_PERFORMATIVE, CANCEL_PERFORMATIVE, REQUEST_PERFORMATIVE

logger = logging.getLogger("StrategyAgent")


class SecretaryAgent(Agent):
    def __init__(self, agentjid, password):
        super().__init__(jid=agentjid, password=password)
        self.strategy = None
        self.agent_id = None

        self.set("manager_agents", {})
        self.stopped = False

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

    async def setup(self):
        logger.info("Secretary agent running")
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = RegistrationBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning("Secretary {} could not create RegisterBehaviour. Retrying...".format(self.agent_id))
                self.add_behaviour(register_behaviour, template)
        except Exception as e:
            logger.error("EXCEPTION creating RegisterBehaviour in Secretary {}: {}".format(self.agent_id, e))


class RegistrationBehaviour(CyclicBehaviour):

    async def on_start(self):
        self.logger = logging.getLogger("SecretaryRegistrationStrategy")
        self.logger.debug("Strategy {} started in secretary".format(type(self).__name__))

    def add_service(self, agent):
        """
        Adds a new ``FleetManagerAgent`` to the store.

        Args:
            agent (``FleetManagerAgent``): the instance of the FleetManagerAgent to be added
        """
        service = self.get("manager_agents")
        if agent["type"] in service:
            service[agent["type"]].append(agent["jid"])
        else:
            service[agent["type"]] = [agent["jid"]]
        print("Arbol de servicios: ", service)

    def remove_service(self, type, agent):
        """
        Erase a ``FleetManagerAgent`` to the store.

        Args:
            agent (``FleetManagerAgent``): the instance of the FleetManagerAgent to be erased
        """
        del (self.get("manager_agents")[type][agent])
        self.logger.debug("Deregistration of the Manager {} for service {}".format(agent, type))

    async def send_confirmation(self, agent_id):
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
                    logger.info("Registration in the dictionary {}".format(self.agent.name))
                    await self.send_confirmation(agent_id)
        except Exception as e:
            logger.error("EXCEPTION in Secretary Register Behaviour of Manager {}: {}".format(self.agent.name, e))


class SecretaryStrategyBehaviour(StrategyBehaviour):
    """
        Class from which to inherit to create a secretary strategy.
        You must overload the :func:`_process` method

        Helper functions:
            * :func:`get_transport_agents`
        """

    async def on_start(self):
        self.logger = logging.getLogger("SecretaryStrategy")
        self.logger.debug("Strategy {} started in secretary".format(type(self).__name__))

    async def send_services(self, customer_id, type):
        reply = Message()
        reply.to = str(customer_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        reply.body = json.dumps(self.get("manager_agents")[type])
        print(self.get("manager_agents")[type])
        await self.send(reply)

    async def send_negative(self, customer_id):
        reply = Message()
        reply.to = str(customer_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", CANCEL_PERFORMATIVE)
        await self.send(reply)

    async def run(self):
        raise NotImplementedError
