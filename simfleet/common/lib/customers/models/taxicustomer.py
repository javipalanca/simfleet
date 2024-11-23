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
    Inherits from the `CustomerAgent` class and provides functionalities
    for requesting transportation services and interacting with fleet managers.

    Attributes:
        fleetmanagers (dict): A dictionary containing the JIDs of the fleet manager(s).
        transport_assigned (str): The JID of the transport agent currently assigned to the customer.

    Methods:
        set_fleetmanagers(fleetmanagers):
            Assigns the fleet manager's JIDs to the customer agent.
        get_fleetmanagers():
            Retrieves the fleet managers' JIDs.
        set_transport_assigned(transport_id):
            Sets the currently assigned transport agent.
        clear_transport_assigned():
            Clears the assigned transport agent.
        run_strategy():
            Adds the behavior for handling requests and executes the customer's strategy.
    """
    def __init__(self, agentjid, password):
        CustomerAgent.__init__(self, agentjid, password)

        self.fleetmanagers = None
        self.transport_assigned = None


    def set_fleetmanagers(self, fleetmanagers):
        """
        Sets the fleet manager's JID list for the customer agent.

        Args:
            fleetmanagers (dict): The JID list of the fleet manager(s).
        """
        self.fleetmanagers = fleetmanagers

    def get_fleetmanagers(self):
        """
                Retrieves the fleet managers' JIDs.

                Returns:
                    dict: The dictionary of fleet managers' JIDs.
                """
        return self.fleetmanagers

    def set_transport_assigned(self, transport_id):
        """
                Sets the currently assigned transport agent.

                Args:
                    transport_id (str): The JID of the transport agent.
                """
        self.transport_assigned = transport_id

    def clear_transport_assigned(self):
        """
                Clears the assigned transport agent.
                """
        self.transport_assigned = None


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
    It defines the communication protocol and decision-making processes for requesting,
    accepting, and managing transport services.

    Methods:
        async send_request(content=None):
            Sends a transport request to the fleet manager(s).
        async accept_transport(transport_id):
            Accepts a transport proposal from a transport agent.
        async refuse_transport(transport_id):
            Refuses a transport proposal from a transport agent.
        async inform_transport(transport_id, status, data=None):
            Sends a message to a transport agent to inform about a status update.
        async run():
            Abstract method that must be implemented in a subclass to define behavior.
    """

    async def on_start(self):
        await super().on_start()
        logger.debug(
            "Agent[{}]: Strategy {} started.".format(
                self.agent.name, type(self).__name__
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

        if self.agent.get_fleetmanagers() is not None:
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
                "Agent[{}]: The agent asked for a transport to ({}).".format(
                    self.agent.name, self.agent.customer_dest
                )
            )
        else:
            logger.warning("Agent[{}]: The agent has no fleet managers.".format(self.agent.name))

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
        self.agent.set_transport_assigned(str(transport_id))
        logger.info(
            "Agent[{}]: The agent accepted proposal from transport [{}]".format(
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
            "Agent[{}]: The agent refused proposal from transport [{}]".format(
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
        #self.agent.transport_assigned = str(transport_id)
        if status != "CUSTOMER_IN_DEST":
            self.agent.set_transport_assigned(str(transport_id))
        else:
            self.agent.clear_transport_assigned()
        logger.info(
            "Agent[{}]: The agent informs the transport [{}]".format(
                self.agent.name, transport_id
            )
        )

    async def run(self):
        """
                Abstract method to define the strategy's behavior.
                This method must be implemented in the child class.
        """
        raise NotImplementedError
