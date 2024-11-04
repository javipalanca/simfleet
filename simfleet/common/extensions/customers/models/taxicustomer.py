import json

from loguru import logger
from spade.message import Message
from spade.template import Template

from simfleet.utils.helpers import new_random_position

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
    INFORM_PERFORMATIVE,
)

from simfleet.common.agents.customer import CustomerAgent
from simfleet.utils.abstractstrategies import StrategyBehaviour

class TaxiCustomerAgent(CustomerAgent):

    """
        Represents a customer agent in the taxi fleet system.
        Inherits from the `CustomerAgent` class and implements
        customer-specific behaviors and interactions with the fleet manager.

        Attributes:
            status (str): The current status of the customer (e.g., waiting).
            fleetmanagers (str): The fleet manager's JID.
        """
    def __init__(self, agentjid, password):
        CustomerAgent.__init__(self, agentjid, password)

        self.fleetmanagers = None
        self.transport_assigned = None


    def set_fleetmanager(self, fleetmanagers):
        """
        Sets the fleet manager's JID list for the customer agent.

        Args:
            fleetmanagers (dict): The JID list of the fleet manager(s).
        """
        self.fleetmanagers = fleetmanagers

    def run_strategy(self):
        """
        Runs the strategy associated with the customer agent.
        Adds the behavior responsible for handling requests to the agent.
        """
        if not self.running_strategy:
            template1 = Template()
            template1.set_metadata("protocol", REQUEST_PROTOCOL)
            self.add_behaviour(self.strategy(), template1)
            self.running_strategy = True


class TaxiCustomerStrategyBehaviour(StrategyBehaviour):
    """
    Represents the strategy behavior for the TaxiCustomerAgent.
    It defines the communication protocol and decision-making for requesting and accepting transports.

    This class should be inherited and the `run` coroutine must be implemented by the user.

    Helper Methods:
        - `send_request`: Sends a request for transport.
        - `accept_transport`: Accepts a transport proposal.
        - `refuse_transport`: Refuses a transport proposal.
        - `inform_transport`: Inform a transport proposal.
    """

    async def on_start(self):
        await super().on_start()
        logger.debug(
            "Strategy {} started in agent {}".format(
                type(self).__name__, self.agent.name
            )
        )

    async def send_request(self, content=None):
        """
        Sends a transport request to the fleet manager(s).
        Uses the REQUEST_PROTOCOL and REQUEST_PERFORMATIVE.

        Args:
            content (dict): Optional dictionary containing request details.
                            If not provided, a default content with customer ID,
                            origin, and destination will be used.
        """
        if not self.agent.customer_dest:
            self.agent.customer_dest = new_random_position(self.agent.boundingbox, self.agent.route_host)

        if content is None or len(content) == 0:
            content = {
                "customer_id": str(self.agent.jid),
                "origin": self.agent.get("current_pos"),
                "dest": self.agent.customer_dest,
            }

        if self.agent.fleetmanagers is not None:
            for (
                fleetmanager
            ) in self.agent.fleetmanagers.keys():
                msg = Message()
                msg.to = str(fleetmanager)
                msg.set_metadata("protocol", REQUEST_PROTOCOL)
                msg.set_metadata("performative", REQUEST_PERFORMATIVE)
                msg.body = json.dumps(content)
                await self.send(msg)
            logger.info(
                "Customer {} asked for a transport to {}.".format(
                    self.agent.name, self.agent.customer_dest
                )
            )
        else:
            logger.warning("Customer {} has no fleet managers.".format(self.agent.name))

    async def accept_transport(self, transport_id):
        """
        Sends a message to a transport agent to accept a travel proposal.
        Uses the REQUEST_PROTOCOL and ACCEPT_PERFORMATIVE.

        Args:
            transport_id (str): The JID of the transport agent to accept.
        """
        reply = Message()
        reply.to = str(transport_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
        content = {
            "customer_id": str(self.agent.jid),
            "origin": self.agent.get("current_pos"),
            "dest": self.agent.customer_dest,
        }
        reply.body = json.dumps(content)
        await self.send(reply)
        self.agent.transport_assigned = str(transport_id)
        logger.info(
            "Customer {} accepted proposal from transport {}".format(
                self.agent.name, transport_id
            )
        )

    async def refuse_transport(self, transport_id):
        """
        Sends a message to a transport agent to refuse a travel proposal.
        Uses the REQUEST_PROTOCOL and REFUSE_PERFORMATIVE.

        Args:
            transport_id (str): The JID of the transport agent to refuse.
        """
        reply = Message()
        reply.to = str(transport_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", REFUSE_PERFORMATIVE)
        content = {
            "customer_id": str(self.agent.jid),
            "origin": self.agent.get("current_pos"),
            "dest": self.agent.customer_dest,
        }
        reply.body = json.dumps(content)

        await self.send(reply)
        logger.info(
            "Customer {} refused proposal from transport {}".format(
                self.agent.name, transport_id
            )
        )

    async def inform_transport(self, transport_id, status, data=None):
        """
        Sends a message to a transport agent to inform it of a status update.
        Uses the REQUEST_PROTOCOL and INFORM_PERFORMATIVE.

        Args:
            transport_id (str): The JID of the transport agent.
            status (str): The status to be informed.
            data (dict): Optional additional data to be included in the message.
        """
        if data is None:
            data = {}
        reply = Message()
        reply.to = str(transport_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        data["status"] = status
        reply.body = json.dumps(data)
        await self.send(reply)
        self.agent.transport_assigned = str(transport_id)
        logger.info(
            "Customer {} informs the transport {}".format(
                self.agent.name, transport_id
            )
        )

    async def run(self):
        """
                Abstract method to define the strategy's behavior.
                This method must be implemented in the child class.
        """
        raise NotImplementedError
