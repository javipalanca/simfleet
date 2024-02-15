import asyncio
import json

from loguru import logger

from spade.message import Message

from simfleet.utils.helpers import (
    #random_position,
    distance_in_meters,
    kmh_to_ms,
    PathRequestException,
    AlreadyInDestination,
)

from simfleet.utils.utils_old import (
    TRANSPORT_WAITING,
    TRANSPORT_MOVING_TO_CUSTOMER,
    TRANSPORT_IN_CUSTOMER_PLACE,
    TRANSPORT_MOVING_TO_DESTINATION,
    TRANSPORT_IN_STATION_PLACE,
    TRANSPORT_CHARGING,
    CUSTOMER_IN_DEST,
    CUSTOMER_LOCATION,
    TRANSPORT_MOVING_TO_STATION,
    chunk_path,
    request_path,
    StrategyBehaviour,
    TRANSPORT_NEEDS_CHARGING,
)

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    TRAVEL_PROTOCOL,
    PROPOSE_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    REGISTER_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
    QUERY_PROTOCOL,
)

from simfleet.common.agents.transport import TransportAgent

MIN_AUTONOMY = 2

class TaxiAgent(TransportAgent):
    def __init__(self, agentjid, password, **kwargs):
        super().__init__(agentjid, password)

        self.current_customer_orig = None

        self.fleetmanager_id = kwargs.get('fleet', None)        # vehicle.py

    # MOD-STRATEGY-04 - Comments
    # MovableMixin - movable.py - ANALIZAR cambiar ubicación
    #async def arrived_to_destination(self):
    #    """
    #    Informs that the transport has arrived to its destination.
    #    It recomputes the new destination and path if picking up a customer
    #    or drops it and goes to WAITING status again.
    #    """
    #    self.set("path", None)
    #    self.chunked_path = None
    #    if (
    #        not self.is_customer_in_transport()
    #    ):  # self.status == TRANSPORT_MOVING_TO_CUSTOMER:
    #        try:
    #            self.set("customer_in_transport", self.get("current_customer"))
    #            await self.move_to(self.current_customer_dest)
    #        except PathRequestException:
    #            await self.cancel_customer()
    #            self.status = TRANSPORT_WAITING
    #        except AlreadyInDestination:
    #            await self.drop_customer()
    #        else:
    #            await self.inform_customer(TRANSPORT_IN_CUSTOMER_PLACE)
    #            self.status = TRANSPORT_MOVING_TO_DESTINATION
    #            logger.info(
    #                "Transport {} has picked up the customer {}.".format(
    #                    self.agent_id, self.get("current_customer")
    #                )
    #            )
    #    else:  # elif self.status == TRANSPORT_MOVING_TO_DESTINATION:
    #        await self.drop_customer()




class TaxiStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a transport strategy.
    You must overload the ```run`` coroutine

    Helper functions:
        * ``pick_up_customer``
        * ``send_proposal``
        * ``cancel_proposal``
    """

    async def on_start(self):
        logger.debug(
            "Strategy {} started in transport {}".format(
                type(self).__name__, self.agent.name
            )
        )
        # self.agent.total_waiting_time = 0.0

    #MOD-STRATEGY-01 - comments
    #async def pick_up_customer(self, customer_id, origin, dest):
    #    """
    #    Starts a TRAVEL_PROTOCOL to pick up a customer and get him to his destination.
    #    It automatically launches all the travelling process until the customer is
    #    delivered. This travelling process includes to update the transport coordinates as it
    #    moves along the path at the specified speed.

    #    Args:
    #        customer_id (str): the id of the customer
    #        origin (list): the coordinates of the current location of the customer
    #        dest (list): the coordinates of the target destination of the customer
    #    """
    #    logger.info(
    #        "Transport {} on route to customer {}".format(self.agent.name, customer_id)
    #    )
    #    reply = Message()
    #    reply.to = customer_id
    #    reply.set_metadata("performative", INFORM_PERFORMATIVE)
        #reply.set_metadata("protocol", TRAVEL_PROTOCOL)
    #    reply.set_metadata("protocol", REQUEST_PROTOCOL)
    #    content = {"status": TRANSPORT_MOVING_TO_CUSTOMER}
    #    reply.body = json.dumps(content)
    #    self.set("current_customer", customer_id)
    #    self.agent.current_customer_orig = origin
    #    self.agent.current_customer_dest = dest
    #    await self.send(reply)
    #    self.agent.num_assignments += 1
    #    try:
    #        await self.agent.move_to(self.agent.current_customer_orig)
    #    except AlreadyInDestination:
    #        await self.agent.arrived_to_destination()
    #    except PathRequestException as e:
    #        logger.error(
    #            "Raising PathRequestException in pick_up_customer for {}".format(
    #                self.agent.name
    #            )
    #        )
    #        raise e

    async def send_confirmation_travel(self, station_id):
        logger.info(
            "Transport {} sent confirmation to station {}".format(
                self.agent.name, station_id
            )
        )
        reply = Message()
        reply.to = station_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
        await self.send(reply)

    async def go_to_the_station(self, station_id, dest):
        """
        Starts a TRAVEL_PROTOCOL to pick up a customer and get him to his destination.
        It automatically launches all the travelling process until the customer is
        delivered. This travelling process includes to update the transport coordinates as it
        moves along the path at the specified speed.

        Args:
            station_id (str): the id of the customer
            dest (list): the coordinates of the target destination of the customer
        """
        logger.info(
            "Transport {} on route to station {}".format(self.agent.name, station_id)
        )
        self.status = TRANSPORT_MOVING_TO_STATION
        reply = Message()
        reply.to = station_id
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        reply.set_metadata("protocol", TRAVEL_PROTOCOL)
        content = {"status": TRANSPORT_MOVING_TO_STATION}
        reply.body = json.dumps(content)
        self.set("current_station", station_id)
        self.agent.current_station_dest = dest
        await self.send(reply)
        # informs the TravelBehaviour of the station that the transport is coming

        self.agent.num_charges += 1
        travel_km = self.agent.calculate_km_expense(self.get("current_pos"), dest)
        self.agent.set_km_expense(travel_km)
        try:
            logger.debug("{} move_to station {}".format(self.agent.name, station_id))
            await self.agent.move_to(self.agent.current_station_dest)
        except AlreadyInDestination:
            logger.debug(
                "{} is already in the stations' {} position. . .".format(
                    self.agent.name, station_id
                )
            )
            await self.agent.arrived_to_station()

    def has_enough_autonomy(self, customer_orig, customer_dest):
        autonomy = self.agent.get_autonomy()
        if autonomy <= MIN_AUTONOMY:
            logger.warning(
                "{} has not enough autonomy ({}).".format(self.agent.name, autonomy)
            )
            return False
        travel_km = self.agent.calculate_km_expense(
            self.get("current_pos"), customer_orig, customer_dest
        )
        logger.debug(
            "Transport {} has autonomy {} when max autonomy is {}"
            " and needs {} for the trip".format(
                self.agent.name,
                self.agent.current_autonomy_km,
                self.agent.max_autonomy_km,
                travel_km,
            )
        )

        if autonomy - travel_km < MIN_AUTONOMY:
            logger.warning(
                "{} has not enough autonomy to do travel ({} for {} km).".format(
                    self.agent.name, autonomy, travel_km
                )
            )
            return False
        return True

    def check_and_decrease_autonomy(self, customer_orig, customer_dest):
        autonomy = self.agent.get_autonomy()
        travel_km = self.agent.calculate_km_expense(
            self.get("current_pos"), customer_orig, customer_dest
        )
        if autonomy - travel_km < MIN_AUTONOMY:
            logger.warning(
                "{} has not enough autonomy to do travel ({} for {} km).".format(
                    self.agent.name, autonomy, travel_km
                )
            )
            return False
        self.agent.set_km_expense(travel_km)
        return True

    async def send_get_stations(self, content=None):

        if content is None or len(content) == 0:
            content = self.agent.request
        msg = Message()
        msg.to = str(self.agent.directory_id)
        msg.set_metadata("protocol", QUERY_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = content
        await self.send(msg)

        logger.info(
            "Transport {} asked for stations to Directory {} for type {}.".format(
                self.agent.name, self.agent.directory_id, self.agent.request
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

    async def cancel_proposal(self, customer_id, content=None):
        """
        Send a ``spade.message.Message`` to cancel a proposal.
        If the content is empty the proposal is sent without content.

        Args:
            customer_id (str): the id of the customer
            content (dict, optional): the optional content of the message
        """
        if content is None:
            content = {}
        logger.info(
            "Transport {} sent cancel proposal to customer {}".format(
                self.agent.name, customer_id
            )
        )
        reply = Message()
        reply.to = customer_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", CANCEL_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def charge_allowed(self):
        self.set("in_station_place", None)  # new
        await self.agent.begin_charging()

    async def run(self):
        raise NotImplementedError
