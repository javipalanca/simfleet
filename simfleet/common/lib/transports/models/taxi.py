import json
from loguru import logger

from spade.behaviour import State
from spade.message import Message

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    PROPOSE_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
)

from simfleet.common.agents.transport import TransportAgent

class TaxiAgent(TransportAgent):
    """
        Represents a taxi agent, inheriting from `TransportAgent`. This class provides
        functionalities specific to taxis, such as managing assigned customers.

        Attributes:
            fleetmanager_id (str): The ID of the fleet manager the taxi belongs to.
            assigned_customer (dict): A dictionary storing the currently assigned customer's
                                      ID, origin, and destination.

        Methods:
            async add_assigned_taxicustomer(customer_id, origin=None, dest=None):
                Adds a customer to the taxi's assigned customer list.
            async remove_assigned_taxicustomer():
                Removes all assigned customers from the taxi's customer list.
        """
    def __init__(self, agentjid, password, **kwargs):
        super().__init__(agentjid, password)

        self.set("assigned_customer", {})
        self.fleetmanager_id = kwargs.get('fleet', None)


    async def add_assigned_taxicustomer(self, customer_id, origin=None, dest=None):
        customers = self.get("assigned_customer")
        customers[customer_id] = {"origin": origin, "destination": dest}
        self.set("assigned_customer", customers)

    async def remove_assigned_taxicustomer(self):
        self.set("assigned_customer", {})

class TaxiStrategyBehaviour(State):
    """
    Base class to define the transport strategy for a taxi.
    This class should be inherited and extended to create custom strategies.
    Subclasses must override the `run` coroutine to define specific behaviors.

    Methods:
        async on_start():
            Logs the beginning of the strategy execution.
        async on_end():
            Logs the end of the strategy execution.
        async send_proposal(customer_id, content=None):
            Sends a transport proposal to a customer.
        async cancel_proposal(agent_id, content=None):
            Cancels a previously sent proposal to a customer.
        async run():
            Abstract method that must be implemented by subclasses.
    """

    async def on_start(self):
        # await super().on_start()
        logger.debug(
            "Agent[{}]: Strategy {} started.".format(
                self.agent.name, type(self).__name__
            )
        )

    async def on_end(self):
        # await super().on_start()
        logger.debug(
            "Agent[{}]: Strategy {} finished.".format(
                self.agent.name, type(self).__name__
            )
        )

    async def send_proposal(self, customer_id, content=None):
        """
        Send a ``spade.message.Message`` with a proposal to a customer to pick up him.
        If the content is empty the proposal is sent without content.

        Args:
            customer_id (str): the id of the customer
            content (dict, optional): the optional content of the message
        """
        if content is None:
            content = {}
        logger.info(
            "Agent[{}]: The agent sent proposal to [{}]".format(self.agent.name, customer_id)
        )
        reply = Message()
        reply.to = customer_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", PROPOSE_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def cancel_proposal(self, agent_id, content=None):
        """
        Send a ``spade.message.Message`` to cancel a proposal.
        If the content is empty the proposal is sent without content.

        Args:
            agent_id (str): the id of the customer
            content (dict, optional): the optional content of the message
        """
        if content is None:
            content = {}
        logger.info(
            "Agent[{}]: The agent sent cancel proposal to [{}]".format(
                self.agent.name, agent_id
            )
        )
        reply = Message()
        reply.to = agent_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", CANCEL_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def run(self):
        raise NotImplementedError
