import asyncio
import json
import time

from loguru import logger

from spade.message import Message
from spade.behaviour import State

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
    #StrategyBehaviour,
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

from simfleet.common.extensions.transports.models.taxi import TaxiAgent
from simfleet.common.chargeable import ChargeableMixin
from simfleet.utils.abstractstrategies import StrategyBehaviour, FSMStrategyBehaviour

class ElectricTaxiAgent(ChargeableMixin, TaxiAgent):
    def __init__(self, agentjid, password, **kwargs):
        ChargeableMixin.__init__(self)
        TaxiAgent.__init__(self, agentjid, password, **kwargs)
        #super().__init__(agentjid, password, **kwargs)

        #self.current_customer_orig = None                      # MOD-STRATEGY-02 - comments
        self.stations = None                                #transport.py
        self.current_station_dest = None                    #transport.py
        self.set("current_station", None)        #transport.py

        # waiting time statistics
        self.waiting_in_queue_time = None
        self.charge_time = None
        self.total_waiting_time = 0.0
        self.total_charging_time = 0.0

        #self.arguments = kwargs.get('args', None)       #ARRAY
        self.arguments = {}

#class ElectricTaxiStrategyBehaviour(StrategyBehaviour):
class ElectricTaxiStrategyBehaviour(State):
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

    #async def go_to_the_station(self, station_id, dest):
    #    """
    #    Starts a TRAVEL_PROTOCOL to pick up a customer and get him to his destination.
    #    It automatically launches all the travelling process until the customer is
    #    delivered. This travelling process includes to update the transport coordinates as it
    #    moves along the path at the specified speed.

    #    Args:
    #        station_id (str): the id of the customer
    #        dest (list): the coordinates of the target destination of the customer
    #    """
    #    logger.info(
    #        "Transport {} on route to station {}".format(self.agent.name, station_id)
    #    )
    #    self.status = TRANSPORT_MOVING_TO_STATION
    #    reply = Message()
    #    reply.to = station_id
    #    reply.set_metadata("performative", INFORM_PERFORMATIVE)
    #    reply.set_metadata("protocol", TRAVEL_PROTOCOL)
    #    content = {"status": TRANSPORT_MOVING_TO_STATION}
    #    reply.body = json.dumps(content)
    #    self.set("current_station", station_id)
    #    self.agent.current_station_dest = dest
    #    await self.send(reply)
        # informs the TravelBehaviour of the station that the transport is coming

    #    self.agent.num_charges += 1
    #    travel_km = self.agent.calculate_km_expense(self.get("current_pos"), dest)
    #    self.agent.set_km_expense(travel_km)
    #    try:
    #        logger.debug("{} move_to station {}".format(self.agent.name, station_id))
    #        await self.agent.move_to(self.agent.current_station_dest)
    #    except AlreadyInDestination:
    #        logger.debug(
    #            "{} is already in the stations' {} position. . .".format(
    #                self.agent.name, station_id
    #            )
    #        )
    #        await self.agent.arrived_to_station()

    async def go_to_the_station(self, station_id, dest):

        logger.info(
            "Transport {} on route to station {}".format(self.agent.name, station_id)
        )
        self.set("current_station", station_id)
        self.agent.current_station_dest = dest
        #self.agent.num_charges += 1            #DUDA ATRIBUTO
        travel_km = self.agent.calculate_km_expense(self.get("current_pos"), dest)
        self.agent.set_km_expense(travel_km)
        #try:
        #    logger.debug("{} move_to station {}".format(self.agent.name, station_id))
        #    await self.agent.move_to(dest)
        #except AlreadyInDestination:
        #    logger.debug(
        #        "{} is already in the stations' {} position. . .".format(
        #            self.agent.name, station_id
        #        )
        #    )
            #await self.agent.arrived_to_station()           #Duda Analizar

    async def request_access_station(self, station_id, content):

        if content is None:
            content = {}
        reply = Message()
        #reply.to = self.get("current_station")
        reply.to = station_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", REQUEST_PERFORMATIVE)
        reply.body = json.dumps(content)
        logger.debug(
            "{} requesting access to {}".format(
                self.agent.name,
                station_id,
                reply.body
            )
        )
        await self.send(reply)

        # time waiting in station queue update
        self.agent.waiting_in_queue_time = time.time()

    # chargeable.py
    #def has_enough_autonomy(self, customer_orig, customer_dest):
    #    autonomy = self.agent.get_autonomy()
    #    if autonomy <= MIN_AUTONOMY:
    #        logger.warning(
    #            "{} has not enough autonomy ({}).".format(self.agent.name, autonomy)
    #        )
    #        return False
    #    travel_km = self.agent.calculate_km_expense(
    #        self.get("current_pos"), customer_orig, customer_dest
    #    )
    #    logger.debug(
    #        "Transport {} has autonomy {} when max autonomy is {}"
    #        " and needs {} for the trip".format(
    #            self.agent.name,
    #            self.agent.current_autonomy_km,
    #            self.agent.max_autonomy_km,
    #            travel_km,
    #        )
    #    )

    #    if autonomy - travel_km < MIN_AUTONOMY:
    #        logger.warning(
    #            "{} has not enough autonomy to do travel ({} for {} km).".format(
    #                self.agent.name, autonomy, travel_km
    #            )
    #        )
    #        return False
    #    return True

    # chargeable.py
    #def check_and_decrease_autonomy(self, customer_orig, customer_dest):
    #    autonomy = self.agent.get_autonomy()
    #    travel_km = self.agent.calculate_km_expense(
    #        self.get("current_pos"), customer_orig, customer_dest
    #    )
    #    if autonomy - travel_km < MIN_AUTONOMY:
    #        logger.warning(
    #            "{} has not enough autonomy to do travel ({} for {} km).".format(
    #                self.agent.name, autonomy, travel_km
    #            )
    #        )
    #        return False
    #    self.agent.set_km_expense(travel_km)
    #    return True

    async def send_get_stations(self, content=None):

        if content is None or len(content) == 0:
            #content = self.agent.request                #CAMBIO1.1 - tiene "station"
            #content = {"service_type": self.agent.service_type}         #vrs2
            content = self.agent.service_type
        msg = Message()
        msg.to = str(self.agent.directory_id)
        msg.set_metadata("protocol", QUERY_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = content
        await self.send(msg)

        logger.info(
            "Transport {} asked for stations to Directory {} for type {}.".format(
                self.agent.name, self.agent.directory_id, self.agent.service_type
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

    async def inform_station(self, data=None):
        """
        Sends a message to the current assigned customer to inform her about a new status.

        Args:
            status (int): The new status code
            data (dict, optional): complementary info about the status
        """
        if data is None:
            data = {}
        msg = Message()
        msg.to = self.get("current_station")
        #msg.set_metadata("protocol", TRAVEL_PROTOCOL)
        #msg.set_metadata("performative", INFORM_PERFORMATIVE)
        msg.set_metadata("protocol", REQUEST_PROTOCOL)
        msg.set_metadata("performative", INFORM_PERFORMATIVE)
        msg.body = json.dumps(data)
        await self.send(msg)

    # Cambiarlo
    async def comunicate_for_charging(self):

        # trigger charging
        self.agent.set("path", None)
        self.agent.chunked_path = None

        data = {
            "need": self.agent.max_autonomy_km - self.agent.current_autonomy_km,        #Calcular al principio - añadir en
        }

        logger.debug(
            "Transport {} with autonomy {} tells {} that it needs to charge "
            "{} km/autonomy".format(
                self.agent.agent_id,
                self.agent.current_autonomy_km,
                self.agent.get("current_station"),
                self.agent.max_autonomy_km - self.agent.current_autonomy_km,
            )
        )

        await self.agent.inform_station(data)

    async def begin_charging(self):

        logger.info(
            "Transport {} has started charging in the station {}.".format(
                self.agent.agent_id, self.get("current_station")
            )
        )

        # time waiting in station queue update
        self.agent.charge_time = time.time()
        elapsed_time = self.agent.charge_time - self.agent.waiting_in_queue_time
        if elapsed_time > 0.1:
            self.agent.total_waiting_time += elapsed_time

    async def drop_station(self):
        """
        Drops the customer that the transport is carring in the current location.
        """

        logger.debug(
            "Transport {} has dropped the station {}.".format(
                self.agent.agent_id, self.agent.get("current_station")
            )
        )
        self.agent.set("current_station", None)

    async def charge_allowed(self):
        self.set("in_station_place", None)  # new
        await self.agent.begin_charging()

    async def run(self):
        raise NotImplementedError
