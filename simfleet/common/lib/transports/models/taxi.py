import json
from loguru import logger

from spade.behaviour import State
from spade.message import Message

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    PROPOSE_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    QUERY_PROTOCOL,
)

from simfleet.common.agents.transport import TransportAgent

MIN_AUTONOMY = 2

class TaxiAgent(TransportAgent):
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
    Class from which to inherit to create a transport strategy.
    You must overload the ```run`` coroutine

    Helper functions:
        * ``pick_up_customer``
        * ``send_proposal``
        * ``cancel_proposal``
    """

    async def on_start(self):
        # await super().on_start()
        logger.debug(
            "Strategy {} started in transport {}".format(
                type(self).__name__, self.agent.name
            )
        )

    async def on_end(self):
        # await super().on_start()
        logger.debug(
            "Strategy {} finished in transport {}".format(
                type(self).__name__, self.agent.name
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
            "Transport {} sent proposal to {}".format(self.agent.name, customer_id)
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
            "Transport {} sent cancel proposal to customer {}".format(
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
