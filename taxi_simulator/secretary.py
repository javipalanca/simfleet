
import logging
import json
from spade.agent import Agent
from spade.template import Template
from spade.message import Message

from .utils import StrategyBehaviour, CyclicBehaviour
from .protocol import REQUEST_PROTOCOL, REGISTER_PROTOCOL, PROPOSE_PERFORMATIVE, CANCEL_PERFORMATIVE

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
        logger.info("Agent id: {}".format(self.agent_id))


class ManagerRegistrationBehaviour(CyclicBehaviour):

    async def on_start(self):
        self.logger = logging.getLogger("SecretaryRegistrationStrategy")
        self.logger.debug("Strategy {} started in secretary".format(type(self).__name__))

    def add_manager_service(self, agent):
        """
        Adds a new ``FleetManagerAgent`` to the store.

        Args:
            agent (``FleetManagerAgent``): the instance of the FleetManagerAgent to be added
        """
        # with self.simulation_mutex:
        self.get("manager_agents")[agent["type"]] = agent

    def remove_manager_service(self, key, agent):
        """
        Erase a ``FleetManagerAgent`` to the store.

        Args:
            agent (``FleetManagerAgent``): the instance of the FleetManagerAgent to be erased
        """
        del (self.get("manager_agents")[key][agent])
        self.logger.debug("Deregistration of the TransporterAgent {}".format(key))

    async def run(self):
        try:
            msg = await self.receive(timeout=5)
            if msg:
                performative = msg.get_metadata("performative")
                content = json.loads(msg.body)
                if performative == PROPOSE_PERFORMATIVE:
                    self.add_manager_service(content)
                elif performative == CANCEL_PERFORMATIVE:
                    self.remove_manager_service(content["name"])
                    logger.debug("No registration in the dictionary {}".format(self.agent.fleetName))
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

    async def run(self):
        raise NotImplementedError
