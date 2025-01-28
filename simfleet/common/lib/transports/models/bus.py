import asyncio
import json
import sys

from loguru import logger
from asyncio import CancelledError
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template
from spade.behaviour import State

from simfleet.utils.helpers import (
    PathRequestException,
    AlreadyInDestination,
)

from simfleet.utils.status import TRANSPORT_MOVING_TO_STATION, CUSTOMER_IN_DEST

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    INFORM_PERFORMATIVE,
    REGISTER_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
)

from simfleet.common.agents.transport import TransportAgent

MIN_AUTONOMY = 2

class BusAgent(TransportAgent):
    """
        Represents a bus agent in the transport system. Manages the bus line, stops,
        capacity, and interactions with customers.

        Attributes:
            stop_list (list): List of stops in the bus line.
            line (str): The bus line identifier.
            line_type (str): The type of bus line (e.g., circular).
            stop_dic (dict): Dictionary of stops with additional details.
            current_stop (list): The current stop the bus is at.
            type_service (str): The type of service the bus offers (default: "stops").
            capacity (int): Maximum capacity of the bus.
            current_capacity (int): Current number of available seats.
            rounds (int): Number of rounds the bus has completed.
        """
    def __init__(self, agentjid, password, **kwargs):
        super().__init__(agentjid, password)

        self.fleetmanager_id = kwargs.get('fleet', None)

        # Bus line attributes
        self.stop_list = []
        self.line = None
        self.line_type = None
        self.stop_dic = None
        self.current_stop = None
        self.type_service = "stops"
        self.capacity = None
        self.current_capacity = None
        self.rounds = 0
        # For movement
        self.set("origin_stop", None)
        self.set("destination_stop", None)

        # Transport in stop event
        self.set("arrived_to_stop", None)  # new
        self.transport_arrived_to_stop_event = asyncio.Event()

        def transport_arrived_to_stop_callback(old, new):
            if not self.transport_arrived_to_stop_event.is_set() and new is True:
                self.transport_arrived_to_stop_event.set()

        self.transport_arrived_to_stop_callback = transport_arrived_to_stop_callback

    # Bus line
    def set_line(self, line):
        """
            Sets the bus line identifier for the agent.

            Args:
                line (str): The bus line identifier.
        """
        logger.info("Setting line {} for transport {}".format(line, self.name))
        self.line = line

    def set_line_type(self, line_type):
        """
            Sets the type of line for the transport.

            Args:
                line_type (str): The type of bus line.
        """
        logger.info("Setting line type {} for transport {}".format(line_type, self.name))
        self.line_type = line_type

    def set_stop_list(self, stop_list):
        """
            Sets the list of stops for the bus line.

            Args:
                stop_list (list): List of stops.
        """
        self.stop_list = stop_list

    def set_capacity(self, capacity):
        """
            Sets the capacity of the bus and initializes the current capacity.

            Args:
                capacity (int): The total capacity of the bus.
        """
        self.capacity = capacity
        self.current_capacity = capacity

    async def setup(self):
        """
            Sets up the transport agent with the registration behavior.
        """
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = RegistrationBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning(
                    "Transport {} could not create RegisterBehaviour. Retrying...".format(
                        self.agent_id
                    )
                )
                self.add_behaviour(register_behaviour, template)
            self.ready = True
        except Exception as e:
            logger.error(
                "EXCEPTION creating RegisterBehaviour in Transport {}: {}".format(
                    self.agent_id, e
                )
            )

    def run_strategy(self):
        """
        Sets the strategy for the transport agent.

        Args: strategy_class (``BusStrategyBehaviour``): The class to be used. Must inherit from
        ``BusStrategyBehaviour``
        """
        if not self.running_strategy:
            template1 = Template()
            template1.set_metadata("protocol", REQUEST_PROTOCOL)
            self.add_behaviour(self.strategy(), template1)
            self.running_strategy = True


    async def set_position(self, coords=None):
        """
        Sets the position of the transport. If no position is provided it is located in a random position.

        Args:
            coords (list): a list coordinates (longitude and latitude)
        """

        await super().set_position(coords)
        self.set("current_pos", coords)

        if self.is_in_destination():
            logger.info(
                "Transport {} has arrived to destination. Status: {}".format(
                    self.agent_id, self.status
                )
            )

            if self.status != TRANSPORT_MOVING_TO_STATION:
                await self.arrived_to_stop()

    def setup_current_stop(self):
        """
            Sets the current stop based on the transport's position.
        """
        for jid in self.stop_dic.keys():
            stop_info = self.stop_dic.get(jid)
            if stop_info.get("position") == self.get("current_pos"):
                self.current_stop = stop_info

    async def arrived_to_stop(self):
        """
            Marks the current stop as arrived and triggers the event.
        """

        # Setup the stop the transport just arrived to as the current stop
        self.setup_current_stop()
        logger.info(
            "Transport {} arrived to stop {}".format(
                self.agent_id, self.current_stop.get("jid")
            )
        )
        self.set("arrived_to_stop", True)


class RegistrationBehaviour(CyclicBehaviour):
    """
        Manages the registration process for the bus agent in the fleet.

        Methods:
            on_start(): Initializes the registration behavior.
            send_registration(): Sends a registration proposal to the fleet manager.
            run(): Executes the behavior, handling registration acceptance or rejection.
        """
    async def on_start(self):
        logger.debug("Strategy {} started in transport".format(type(self).__name__))

    async def send_registration(self):
        """
        Sends a registration proposal message to the fleet manager.
        """
        logger.debug(
            "Transport {} sent proposal to register to manager {}".format(
                self.agent.name, self.agent.fleetmanager_id
            )
        )
        content = {
            "name": self.agent.name,
            "jid": str(self.agent.jid),
            "fleet_type": self.agent.fleet_type,
        }
        msg = Message()
        msg.to = str(self.agent.fleetmanager_id)
        msg.set_metadata("protocol", REGISTER_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

    async def run(self):
        try:
            if not self.agent.registration:
                await self.send_registration()
            msg = await self.receive(timeout=10)
            if msg:
                performative = msg.get_metadata("performative")
                if performative == ACCEPT_PERFORMATIVE:
                    content = json.loads(msg.body)
                    self.agent.set_registration(True, content)
                    logger.info(
                        "[{}] Registration in the fleet manager accepted: {}.".format(
                            self.agent.name, self.agent.fleetmanager_id
                        )
                    )
                    self.kill(exit_code="Fleet Registration Accepted")
                elif performative == REFUSE_PERFORMATIVE:
                    logger.warning(
                        "Registration in the fleet manager was rejected (check fleet type)."
                    )
                    self.kill(exit_code="Fleet Registration Rejected")
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error(
                "EXCEPTION in RegisterBehaviour of Transport {}: {}".format(
                    self.agent.name, e
                )
            )

class BusStrategyBehaviour(State):
    """
    Class to define a transport strategy for the bus agent. Inherit from this class to implement custom strategies.

    Helper functions:
        - send_get_stops
        - get_subsequent_stop
        - move_to_next_stop
        - drop_customers
        - begin_boarding
        - accept_customer
        - reject_customer
    """

    async def on_start(self):
        logger.debug(
            "Strategy {} started in transport {}".format(
                type(self).__name__, self.agent.name
            )
        )

    # Bus line functions
    def get_subsequent_stop(self):
        """
            Gets the next stop in the list for the transport agent.

            Returns:
                The coordinates of the next stop.
        """
        try:
            index_current = self.agent.stop_list.index(self.agent.get("current_pos"))
        except ValueError:
            index_current = None
        if index_current is None:
            logger.critical("Transport {} current pos ({}) is not in its stop_list {}".format(self.agent.name,
                                                                                              self.agent.get(
                                                                                                  "current_pos"),
                                                                                              self.agent.stop_list))
            sys.exit()
        next_destination = None
        if index_current + 1 < len(self.agent.stop_list):
            next_destination = self.agent.stop_list[index_current + 1]
        return next_destination

    async def move_to_next_stop(self, next_destination):
        """
            Moves the bus to the next stop.

            Args:
                next_destination (tuple): Coordinates of the next stop.
        """
        logger.info("Transport {} in route to {}".format(self.agent.name, next_destination))
        dest = next_destination
        # set current destination as next destination
        self.agent.set("next_pos", dest)
        # Invoke move_to
        try:
            await self.agent.move_to(dest)
        except AlreadyInDestination:
            self.agent.dest = dest
            await self.agent.arrived_to_stop()
        except PathRequestException as e:
            logger.error(
                "Raising PathRequestException in pick_up_customer for {}".format(
                    self.agent.name
                )
            )
            raise e

    async def drop_customers(self):
        """
            Drops off customers at their destination stops if the current stop is their destination.
        """
        current_position = self.agent.get("current_pos")
        # Inform passengers (tuples with agent name, destination stop)
        inform_to = self.get_customers_from_stop(current_position)
        while len(inform_to) > 0:
            customer = inform_to[0]
            logger.info("Transport {} informing customer {} their destination stop has been reached".format(
                self.agent.name, customer))
            inform_to = inform_to[1:]
            msg = Message()
            msg.to = str(customer)
            msg.set_metadata("protocol", REQUEST_PROTOCOL)
            msg.set_metadata("performative", INFORM_PERFORMATIVE)
            msg.status = CUSTOMER_IN_DEST
            await self.send(msg)
            # Update capacity
            self.agent.current_capacity += 1
            # Delete customer from current customers
            self.agent.remove_customer_in_transport(customer)

    def get_customers_from_stop(self, current_position):
        """
            Retrieves a list of customers who have their destination at the current stop.

            Args:
                current_position (list): The coordinates of the current stop.

            Returns:
                list: List of customer IDs who have this stop as their destination.
        """
        customer_list = []
        for customer_id in self.agent.get("current_customer").keys():
            customer_dest = self.agent.get("current_customer").get(customer_id).get("dest")
            if customer_dest == current_position:
                customer_list.append(customer_id)
        return customer_list

    async def begin_boarding(self, content):
        """
            Notifies the current stop that boarding may begin.

            Args:
                content (dict, optional): Information needed for boarding.
        """
        logger.info("Transport {} informing stop {} that boarding may begin".format(self.agent.name,
                                                                                    self.agent.current_stop.get(
                                                                                        "jid")))
        if content is None:
            content = {}
        msg = Message()
        msg.to = str(self.agent.current_stop.get("jid"))
        msg.set_metadata("protocol", REQUEST_PROTOCOL)
        msg.set_metadata("performative", INFORM_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

    async def accept_customer(self, customer_id, content):
        """
        Send a ``spade.message.Message`` with accepting the boarding of a customer.
        If the content is empty the proposal is sent without content.

        Args:
            customer_id (str): the id of the customer
            content (dict, optional): the optional content of the message
        """
        customer_origin = content.get("origin")
        customer_dest = content.get("dest")
        logger.info(
            "Transport {} accepted customer {} with origin {} and dest {}".format(self.agent.name, customer_id,
                                                                                  customer_origin, customer_dest)
        )
        # Add customer to the current customers dict
        self.agent.add_customer_in_transport(customer_id, customer_origin, customer_dest)

        # Send message accepting the boarding
        reply = Message()
        reply.to = str(customer_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def reject_customer(self, customer_id, content):
        """
        Send a ``spade.message.Message`` with accepting the boarding of a customer.
        If the content is empty the proposal is sent without content.

        Args:
            customer_id (str): the id of the customer
            content (dict, optional): the optional content of the message
        """
        logger.info("Transport {} rejected customer {}".format(self.agent.name, customer_id))

        # Send message rejecting the boarding
        reply = Message()
        reply.to = str(customer_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", REFUSE_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)
