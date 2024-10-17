import asyncio
import json
import time
from asyncio import CancelledError
from collections import defaultdict

from spade.behaviour import CyclicBehaviour
from spade.template import Template
from spade.message import Message
from loguru import logger

from simfleet.utils.helpers import new_random_position
from simfleet.utils.utils_old import (
    CUSTOMER_LOCATION,
    StrategyBehaviour,
    status_to_str,
)

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    QUERY_PROTOCOL,
)

from simfleet.common.extensions.customers.models.pedestrian import PedestrianAgent

class BusCustomerAgent(PedestrianAgent):
    """
        Represents a customer agent using a bus service. It manages the interaction
        with the transport system including setting stops, waiting times, and registering
        to stops along the bus line.

        Attributes:
            __observers (dict): Observers for value changes.
            current_stop (list): The current bus stop of the customer.
            destination_stop (list): The destination bus stop of the customer.
            type_service (str): The type of service the customer is using.
            registered_in (str): The bus stop where the customer is registered.
            stop_dic (dict): Dictionary of available stops.
            in_transport_time (float): Time the customer spends in transport.
            total_sim_time (float): Total simulation time for the customer.
            alternative_transports (list): Alternative transport options.
            line (str): The bus line assigned to the customer.
            arguments (dict): Additional arguments for the customer.
        """
    def __init__(self, agentjid, password):
        super().__init__(agentjid, password)

        # Bus line attributes
        self.__observers = defaultdict(list)
        self.current_stop = None
        self.destination_stop = None
        self.type_service = "stops"
        self.registered_in = None
        self.stop_dic = None
        self.in_transport_time = None
        self.total_sim_time = None
        self.alternative_transports = []

        # Additional attribute
        self.line = None
        self.arguments = {}

        # Event for tracking when the customer arrives at the destination
        self.set("arrived_to_destination", None)
        self.customer_arrived_to_destination_event = asyncio.Event(loop=self.loop)

        def customer_arrived_to_destination_callback(old, new):
            if not self.customer_arrived_to_destination_event.is_set() and new is True:
                self.customer_arrived_to_destination_event.set()

        self.customer_arrived_to_destination_callback = customer_arrived_to_destination_callback

    def set_line(self, line):
        """
            Sets the bus line the customer is using.

            Args:
                line (str): The bus line identifier.
        """
        self.line = line

    def run_strategy(self):
        """
        Runs the strategy for the customer agent. Initializes the behavior
        for handling requests and messages related to the bus service.
        """
        if not self.running_strategy:
            template1 = Template()
            template1.set_metadata("protocol", REQUEST_PROTOCOL)
            self.add_behaviour(self.strategy(), template1)
            self.running_strategy = True

    def get_waiting_time_bus(self):
        """
            Calculates the waiting time for the customer before boarding the bus.

            Returns:
                float: The time the customer has been waiting for pickup.
        """
        if self.waiting_for_pickup_time is not None:
            return self.waiting_for_pickup_time
        elif self.init_time is not None:
            if self.pickup_time is not None:
                return self.pickup_time - self.init_time
            else:
                return time.time() - self.init_time
        else:
            return None

    def in_transport_time_bus(self):
        """
            Calculates the time the customer has been in transport.

            Returns:
                float: The time the customer has spent in transport.
        """
        if self.pickup_time:
            if self.end_time:
                return self.end_time - self.pickup_time
            else:
                return time.time() - self.pickup_time
        else:
            return None

    def get_waiting_for_pickup_time(self):
        return self.waiting_for_pickup_time

    def get_in_transport_time(self):
        return self.in_transport_time

    def get_total_sim_time(self):
        return self.total_sim_time

    def get_pickup_time(self):
        """
        Returns the time the customer waited to be picked up after being assigned to a transport.

        Returns:
            float: The waiting time for pickup, or None if not yet picked up.
        """
        if self.pickup_time:
            return self.pickup_time - self.waiting_for_pickup_time
        return None

    async def set_position(self, coords=None):
        """
        Sets the position of the customer. If no position is provided, assigns a random one.

        Args:
            coords (list): Coordinates (longitude and latitude) where the customer is located.
        """
        await super().set_position(coords)
        self.set("current_pos", coords)

        if self.destination_stop[1] == self.get_position():

            logger.success("Customer {} arrived to its destination {}".format(self.name, self.destination_stop[1]))
            self.set("arrived_to_destination", True)  # launch callback, awake FSMStrategyBehaviour
            self.end_time = time.time()

    async def setup(self):
        """
        Sets up the customer agent by configuring behaviors and templates (TravelBehaviour).
        """
        await super().setup()



class BusCustomerStrategyBehaviour(StrategyBehaviour):
    """
    Strategy behavior for a bus customer. This class manages the logic for customer requests,
    accepting or refusing transport offers, and interacting with stops.

    Helper methods:
        - send_request
        - accept_transport
        - refuse_transport
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
        # Bus line
        # self.agent.init_time = time.time()

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
                self.agent.name, self.agent.directory_id, self.agent.type_service
            )
        )

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
            "origin": self.agent.get("current_pos"),
            "dest": self.agent.dest,
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
            "origin": self.agent.get("current_pos"),
            "dest": self.agent.dest,
        }
        reply.body = json.dumps(content)

        await self.send(reply)
        logger.info(
            "Customer {} refused proposal from transport {}".format(
                self.agent.name, transport_id
            )
        )

    def setup_stops(self):
        """
        Sets up the current and destination bus stops for the customer based on the nearest available stops.
        """
        if self.agent.current_stop is None and self.agent.destination_stop is None:
            self.agent.current_stop = self.agent.nearst_agent(self.agent.stop_dic, self.agent.get_position())
            self.agent.destination_stop = self.agent.nearst_agent(self.agent.stop_dic, self.agent.customer_dest)

            logger.debug("Customer {} set current_stop {} and destination_stop {}".format(self.agent.name,
                                                                                      self.agent.current_stop[0],
                                                                                      self.agent.destination_stop[0]))

    async def register_to_stop(self, content):  # ANALIZAR Y REDISEÑO
        """
            Registers the customer at the current bus stop.

            Args:
                content (dict, optional): Information needed for registration.
        """
        if content is None:
            content = {}
        msg = Message()
        msg.to = self.agent.current_stop[0]
        msg.set_metadata("protocol", REQUEST_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        logger.debug("Customer {} asked to register to stop {} with destination {}".format(self.agent.name,
                                                                                           self.agent.current_stop[0],
                                                                                           self.agent.destination_stop[
                                                                                               1]))
        await self.send(msg)

    async def board_transport(self, transport):
        """
            Sends a message to board a transport.

            Args:
                transport (str): The transport agent ID.
        """
        content = {
            "customer_id": str(self.agent.jid),
            "origin": self.agent.get("current_pos"),
            "dest": self.agent.destination_stop[1],
        }
        msg = Message()
        msg.body = json.dumps(content)
        msg.to = str(transport)
        msg.set_metadata("protocol", REQUEST_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        await self.send(msg)

    async def inform_stop(self, content):
        """
            Informs the stop of the customer's status.

            Args:
                content (dict, optional): Information needed for the message.
        """

        if content is None:
            content = {}
        msg = Message()
        msg.to = self.agent.current_stop[0]
        msg.set_metadata("protocol", REQUEST_PROTOCOL)
        msg.set_metadata("performative", INFORM_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

    async def run(self):
        """
            Abstract method to define the behavior strategy. This must be implemented in derived classes.
        """
        raise NotImplementedError
