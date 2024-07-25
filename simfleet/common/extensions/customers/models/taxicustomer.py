import json
import time

from loguru import logger
from spade.message import Message
from spade.template import Template

from simfleet.utils.helpers import new_random_position
from simfleet.utils.utils_old import (
    CUSTOMER_WAITING,
    CUSTOMER_IN_DEST,
    TRANSPORT_MOVING_TO_CUSTOMER,
    CUSTOMER_IN_TRANSPORT,
    TRANSPORT_IN_CUSTOMER_PLACE,
    CUSTOMER_LOCATION,
    StrategyBehaviour,
    request_path,
    status_to_str,
)

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    TRAVEL_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    QUERY_PROTOCOL,
)

from simfleet.common.agents.customer import CustomerAgent
from simfleet.common.movable import MovableMixin

#class TaxiCustomerAgent(MovableMixin, CustomerAgent):
class TaxiCustomerAgent(CustomerAgent):
    def __init__(self, agentjid, password):
        CustomerAgent.__init__(self, agentjid, password)
        #MovableMixin.__init__(self)

        #self.agent_id = None                    #simfleetagent.py
        self.status = CUSTOMER_WAITING           #customer.py
        self.fleetmanagers = None                #customer.py

    #CustomerAgent
    def set_fleetmanager(self, fleetmanagers):
        """
        Sets the fleetmanager JID address
        Args:
            fleetmanagers (str): the fleetmanager jid

        """
        self.fleetmanagers = fleetmanagers

    def run_strategy(self):
        """import json
        Runs the strategy for the customer agent.
        """
        if not self.running_strategy:
            template1 = Template()
            template1.set_metadata("protocol", REQUEST_PROTOCOL)
            # template2 = Template()
            # template2.set_metadata("protocol", QUERY_PROTOCOL)
            # self.add_behaviour(self.strategy(), template1 | template2)
            self.add_behaviour(self.strategy(), template1)
            self.running_strategy = True


#class CustomerStrategyBehaviour(StrategyBehaviour):
class TaxiCustomerStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a transport strategy.
    You must overload the ``run`` coroutine

    Helper functions:
        * ``send_request``
        * ``accept_transport``
        * ``refuse_transport``
    """

    async def on_start(self):
        """
        Initializes the logger and timers. Call to parent method if overloaded.
        """
        logger.debug(
            "Strategy {} started in customer {}".format(
                type(self).__name__, self.agent.name
            )
        )
        self.agent.init_time = time.time()

    async def send_get_managers(self, content=None):
        """
        Sends an ``spade.message.Message`` to the DirectoryAgent to request a managers.
        It uses the QUERY_PROTOCOL and the REQUEST_PERFORMATIVE.
        If no content is set a default content with the type_service that needs
        Args:
            content (dict): Optional content dictionary
        """
        if content is None or len(content) == 0:
            content = self.agent.fleet_type
        msg = Message()
        msg.to = str(self.agent.directory_id)
        msg.set_metadata("protocol", QUERY_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = content
        await self.send(msg)

        logger.info(
            "Customer {} asked for managers to directory {} for type {}.".format(
                self.agent.name, self.agent.directory_id, self.agent.fleet_type
            )
        )

    async def send_request(self, content=None):
        """
        Sends an ``spade.message.Message`` to the fleetmanager to request a transport.
        It uses the REQUEST_PROTOCOL and the REQUEST_PERFORMATIVE.
        If no content is set a default content with the customer_id,
        origin and target coordinates is used.

        Args:
            content (dict): Optional content dictionary
        """
        if not self.agent.customer_dest:
            #self.agent.dest = random_position()
            self.agent.customer_dest = new_random_position(self.agent.boundingbox, self.agent.route_host)
        if content is None or len(content) == 0:
            content = {
                "customer_id": str(self.agent.jid),
                #"origin": self.agent.current_pos,       #Non-parallel variable
                "origin": self.agent.get("current_pos"),
                "dest": self.agent.customer_dest,
            }

        if self.agent.fleetmanagers is not None:
            for (
                fleetmanager
            ) in self.agent.fleetmanagers.keys():  # Send a message to all FleetManagers
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
        Sends a ``spade.message.Message`` to a transport to accept a travel proposal.
        It uses the REQUEST_PROTOCOL and the ACCEPT_PERFORMATIVE.

        Args:
            transport_id (str): The Agent JID of the transport
        """
        reply = Message()
        reply.to = str(transport_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
        content = {
            "customer_id": str(self.agent.jid),
            #"origin": self.agent.current_pos,               #Non-parallel variable
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
        Sends an ``spade.message.Message`` to a transport to refuse a travel proposal.
        It uses the REQUEST_PROTOCOL and the REFUSE_PERFORMATIVE.

        Args:
            transport_id (str): The Agent JID of the transport
        """
        reply = Message()
        reply.to = str(transport_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", REFUSE_PERFORMATIVE)
        content = {
            "customer_id": str(self.agent.jid),
            #"origin": self.agent.current_pos,              #Non-parallel variable
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
        Sends a ``spade.message.Message`` to a transport to accept a travel proposal.
        It uses the REQUEST_PROTOCOL and the ACCEPT_PERFORMATIVE.

        Args:
            transport_id (str): The Agent JID of the transport
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
        raise NotImplementedError
