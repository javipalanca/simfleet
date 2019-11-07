import json
from asyncio import CancelledError
from collections import defaultdict

from loguru import logger
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template

from .helpers import random_position, distance_in_meters, kmh_to_ms, PathRequestException, \
    AlreadyInDestination
from .protocol import REQUEST_PROTOCOL, TRAVEL_PROTOCOL, PROPOSE_PERFORMATIVE, CANCEL_PERFORMATIVE, INFORM_PERFORMATIVE, \
    REGISTER_PROTOCOL, REQUEST_PERFORMATIVE, \
    ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE, QUERY_PROTOCOL
from .utils import TRANSPORT_WAITING, TRANSPORT_MOVING_TO_CUSTOMER, TRANSPORT_IN_CUSTOMER_PLACE, \
    TRANSPORT_MOVING_TO_DESTINATION, TRANSPORT_IN_STATION_PLACE, TRANSPORT_CHARGING, \
    CUSTOMER_IN_DEST, CUSTOMER_LOCATION, TRANSPORT_MOVING_TO_STATION, chunk_path, request_path, StrategyBehaviour, \
    TRANSPORT_NEEDS_CHARGING

MIN_AUTONOMY = 2
ONESECOND_IN_MS = 1000


class TransportAgent(Agent):
    def __init__(self, agentjid, password):
        super().__init__(agentjid, password)

        self.fleetmanager_id = None
        self.route_id = None
        self.strategy = None
        self.running_strategy = False

        self.__observers = defaultdict(list)
        self.agent_id = None
        self.status = TRANSPORT_WAITING
        self.icon = None
        self.set("current_pos", None)
        self.dest = None
        self.set("path", None)
        self.chunked_path = None
        self.set("speed_in_kmh", 3000)
        self.animation_speed = ONESECOND_IN_MS
        self.distances = []
        self.durations = []
        self.port = None
        self.set("current_customer", None)
        self.current_customer_orig = None
        self.current_customer_dest = None
        self.set("customer_in_transport", None)
        self.num_assignments = 0
        self.stopped = False
        self.registration = False

        self.directory_id = None
        self.fleet_type = None

        self.request = "station"
        self.stations = None
        self.current_autonomy_km = 2000
        self.max_autonomy_km = 2000
        self.num_charges = 0
        self.set("current_station", None)
        self.current_station_dest = None

    async def setup(self):
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = RegistrationBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning("Transport {} could not create RegisterBehaviour. Retrying...".format(self.agent_id))
                self.add_behaviour(register_behaviour, template)
        except Exception as e:
            logger.error("EXCEPTION creating RegisterBehaviour in Transport {}: {}".format(self.agent_id, e))

    def set_registration(self, status, content=None):
        """
        Sets the status of registration
        Args:
            status (boolean): True if the transport agent has registered or False if not
            content (dict):
        """
        if content is not None:
            self.icon = content["icon"] if self.icon is None else self.icon
            self.fleet_type = content["fleet_type"]
        self.registration = status

    def set_directory(self, directory_id):
        """
        Sets the directory JID address
        Args:
            directory_id (str): the DirectoryAgent jid

        """
        self.directory_id = directory_id

    def watch_value(self, key, callback):
        """
        Registers an observer callback to be run when a value is changed

        Args:
            key (str): the name of the value
            callback (function): a function to be called when the value changes. It receives two arguments: the old and the new value.
        """
        self.__observers[key].append(callback)

    def run_strategy(self):
        """
        Sets the strategy for the transport agent.

        Args:
            strategy_class (``TransportStrategyBehaviour``): The class to be used. Must inherit from ``TransportStrategyBehaviour``
        """
        if not self.running_strategy:
            template1 = Template()
            template1.set_metadata("protocol", REQUEST_PROTOCOL)
            template2 = Template()
            template2.set_metadata("protocol", QUERY_PROTOCOL)
            self.add_behaviour(self.strategy(), template1 | template2)
            self.running_strategy = True

    def set_id(self, agent_id):
        """
        Sets the agent identifier

        Args:
            agent_id (str): The new Agent Id
        """
        self.agent_id = agent_id

    def set_icon(self, icon):
        self.icon = icon

    def set_fleetmanager(self, fleetmanager_id):
        """
        Sets the fleetmanager JID address
        Args:
            fleetmanager_id (str): the fleetmanager jid

        """
        logger.info("Setting fleet {} for agent {}".format(fleetmanager_id.split("@")[0], self.name))
        self.fleetmanager_id = fleetmanager_id

    def set_fleet_type(self, fleet_type):
        self.fleet_type = fleet_type

    def set_route_agent(self, route_id):
        """
        Sets the route agent JID address
        Args:
            route_id (str): the route agent jid

        """
        self.route_id = route_id

    async def send(self, msg):
        if not msg.sender:
            msg.sender = str(self.jid)
            logger.debug(f"Adding agent's jid as sender to message: {msg}")
        aioxmpp_msg = msg.prepare()
        await self.client.send(aioxmpp_msg)
        msg.sent = True
        self.traces.append(msg, category=str(self))

    def is_customer_in_transport(self):
        return self.get("customer_in_transport") is not None

    def is_free(self):
        return self.get("current_customer") is None

    async def arrived_to_destination(self):
        """
        Informs that the transport has arrived to its destination.
        It recomputes the new destination and path if picking up a customer
        or drops it and goes to WAITING status again.
        """
        self.set("path", None)
        self.chunked_path = None
        if not self.is_customer_in_transport():  # self.status == TRANSPORT_MOVING_TO_CUSTOMER:
            try:
                self.set("customer_in_transport", self.get("current_customer"))
                await self.move_to(self.current_customer_dest)
            except PathRequestException:
                await self.cancel_customer()
                self.status = TRANSPORT_WAITING
            except AlreadyInDestination:
                await self.drop_customer()
            else:
                await self.inform_customer(TRANSPORT_IN_CUSTOMER_PLACE)
                self.status = TRANSPORT_MOVING_TO_DESTINATION
                logger.info("Transport {} has picked up the customer {}.".format(self.agent_id,
                                                                                 self.get("current_customer")))
        else:  # elif self.status == TRANSPORT_MOVING_TO_DESTINATION:
            await self.drop_customer()

    async def arrived_to_station(self):
        """
        Informs that the transport has arrived to its destination.
        It recomputes the new destination and path if picking up a customer
        or drops it and goes to WAITING status again.
        """
        self.status = TRANSPORT_IN_STATION_PLACE

        self.set("path", None)
        self.chunked_path = None

        data = {
            "status": TRANSPORT_IN_STATION_PLACE,
            "need": self.max_autonomy_km - self.current_autonomy_km
        }
        await self.inform_station(data)
        self.status = TRANSPORT_CHARGING
        logger.info("Transport {} has started charging in the station {}.".format(self.agent_id,
                                                                                  self.get("current_station")))

    def needs_charging(self):
        return (self.status == TRANSPORT_NEEDS_CHARGING) or \
               (self.get_autonomy() <= MIN_AUTONOMY and self.status in [TRANSPORT_WAITING])

    def transport_charged(self):
        self.current_autonomy_km = self.max_autonomy_km

    async def drop_customer(self):
        """
        Drops the customer that the transport is carring in the current location.
        """
        await self.inform_customer(CUSTOMER_IN_DEST)
        self.status = TRANSPORT_WAITING
        logger.debug("Transport {} has dropped the customer {} in destination.".format(self.agent_id,
                                                                                       self.get("current_customer")))
        self.set("current_customer", None)
        self.set("customer_in_transport", None)

    async def drop_station(self):
        """
        Drops the customer that the transport is carring in the current location.
        """
        # data = {"status": TRANSPORT_LOADED}
        # await self.inform_station(data)
        self.status = TRANSPORT_WAITING
        logger.debug("Transport {} has dropped the station {}.".format(self.agent_id,
                                                                       self.get("current_station")))
        self.set("current_station", None)

    async def move_to(self, dest):
        """
        Moves the transport to a new destination.

        Args:
            dest (list): the coordinates of the new destination (in lon, lat format)

        Raises:
             AlreadyInDestination: if the transport is already in the destination coordinates.
        """
        if self.get("current_pos") == dest:
            raise AlreadyInDestination
        counter = 5
        path = None
        distance, duration = 0, 0
        while counter > 0 and path is None:
            logger.debug("Requesting path from {} to {}".format(self.get("current_pos"), dest))
            path, distance, duration = await self.request_path(self.get("current_pos"), dest)
            counter -= 1
        if path is None:
            raise PathRequestException("Error requesting route.")

        self.set("path", path)
        try:
            self.chunked_path = chunk_path(path, self.get("speed_in_kmh"))
        except Exception as e:
            logger.error("Exception chunking path {}: {}".format(path, e))
            raise PathRequestException
        self.dest = dest
        self.distances.append(distance)
        self.durations.append(duration)
        behav = self.MovingBehaviour(period=1)
        self.add_behaviour(behav)

    async def step(self):
        """
        Advances one step in the simulation
        """
        if self.chunked_path:
            _next = self.chunked_path.pop(0)
            distance = distance_in_meters(self.get_position(), _next)
            self.animation_speed = distance / kmh_to_ms(self.get("speed_in_kmh")) * ONESECOND_IN_MS
            await self.set_position(_next)

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
        msg.set_metadata("protocol", TRAVEL_PROTOCOL)
        msg.set_metadata("performative", INFORM_PERFORMATIVE)
        msg.body = json.dumps(data)
        await self.send(msg)

    async def inform_customer(self, status, data=None):
        """
        Sends a message to the current assigned customer to inform her about a new status.

        Args:
            status (int): The new status code
            data (dict, optional): complementary info about the status
        """
        if data is None:
            data = {}
        msg = Message()
        msg.to = self.get("current_customer")
        msg.set_metadata("protocol", TRAVEL_PROTOCOL)
        msg.set_metadata("performative", INFORM_PERFORMATIVE)
        data["status"] = status
        msg.body = json.dumps(data)
        await self.send(msg)

    async def cancel_customer(self, data=None):
        """
        Sends a message to the current assigned customer to cancel the assignment.

        Args:
            data (dict, optional): Complementary info about the cancellation
        """
        logger.error("Transport {} could not get a path to customer {}.".format(self.agent_id,
                                                                                self.get("current_customer")))
        if data is None:
            data = {}
        reply = Message()
        reply.to = self.get("current_customer")
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", CANCEL_PERFORMATIVE)
        reply.body = json.dumps(data)
        logger.debug("Transport {} sent cancel proposal to customer {}".format(self.agent_id,
                                                                               self.get("current_customer")))
        await self.send(reply)

    async def request_path(self, origin, destination):
        """
        Requests a path between two points (origin and destination) using the RouteAgent service.

        Args:
            origin (list): the coordinates of the origin of the requested path
            destination (list): the coordinates of the end of the requested path

        Returns:
            list, float, float: A list of points that represent the path from origin to destination, the distance and the estimated duration

        Examples:
            >>> path, distance, duration = await self.request_path(origin=[0,0], destination=[1,1])
            >>> print(path)
            [[0,0], [0,1], [1,1]]
            >>> print(distance)
            2.0
            >>> print(duration)
            3.24
        """
        return await request_path(self, origin, destination, self.route_id)

    def set_initial_position(self, coords):
        self.set("current_pos", coords)

    async def set_position(self, coords=None):
        """
        Sets the position of the transport. If no position is provided it is located in a random position.

        Args:
            coords (list): a list coordinates (longitude and latitude)
        """
        if coords:
            self.set("current_pos", coords)
        else:
            self.set("current_pos", random_position())

        logger.debug("Transport {} position is {}".format(self.agent_id, self.get("current_pos")))
        if self.status == TRANSPORT_MOVING_TO_DESTINATION:
            await self.inform_customer(CUSTOMER_LOCATION, {"location": self.get("current_pos")})
        if self.is_in_destination():
            logger.info("Transport {} has arrived to destination.".format(self.agent_id))
            if self.status == TRANSPORT_MOVING_TO_STATION:
                await self.arrived_to_station()
            else:
                await self.arrived_to_destination()

    def get_position(self):
        """
        Returns the current position of the customer.

        Returns:
            list: the coordinates of the current position of the customer (lon, lat)
        """
        return self.get("current_pos")

    def set_speed(self, speed_in_kmh):
        """
        Sets the speed of the transport.

        Args:
            speed_in_kmh (float): the speed of the transport in km per hour
        """
        self.set("speed_in_kmh", speed_in_kmh)

    def is_in_destination(self):
        """
        Checks if the transport has arrived to its destination.

        Returns:
            bool: whether the transport is at its destination or not
        """
        return self.dest == self.get_position()

    def set_km_expense(self, expense=0):
        self.current_autonomy_km -= expense

    def set_autonomy(self, autonomy, current_autonomy=None):
        self.max_autonomy_km = autonomy
        self.current_autonomy_km = current_autonomy if current_autonomy is not None else autonomy

    def get_autonomy(self):
        return self.current_autonomy_km

    def calculate_km_expense(self, origin, start, dest=None):
        fir_distance = distance_in_meters(origin, start)
        sec_distance = distance_in_meters(start, dest)
        if dest is None:
            sec_distance = 0
        return (fir_distance + sec_distance) // 1000

    def to_json(self):
        """
        Serializes the main information of a transport agent to a JSON format.
        It includes the id of the agent, its current position, the destination coordinates of the agent,
        the current status, the speed of the transport (in km/h), the path it is following (if any), the customer that it
        has assigned (if any), the number of assignments if has done and the distance that the transport has traveled.

        Returns:
            dict: a JSON doc with the main information of the transport.

            Example::

                {
                    "id": "cphillips",
                    "position": [ 39.461327, -0.361839 ],
                    "dest": [ 39.460599, -0.335041 ],
                    "status": 24,
                    "speed": 1000,
                    "path": [[0,0], [0,1], [1,0], [1,1], ...],
                    "customer": "ghiggins@127.0.0.1",
                    "assignments": 2,
                    "distance": 3481.34
                }
        """
        return {
            "id": self.agent_id,
            "position": [float("{0:.6f}".format(coord)) for coord in self.get("current_pos")],
            "dest": [float("{0:.6f}".format(coord)) for coord in self.dest] if self.dest else None,
            "status": self.status,
            "speed": float("{0:.2f}".format(self.animation_speed)) if self.animation_speed else None,
            "path": self.get("path"),
            "customer": self.get("current_customer").split("@")[0] if self.get("current_customer") else None,
            "assignments": self.num_assignments,
            "distance": "{0:.2f}".format(sum(self.distances)),
            "autonomy": self.current_autonomy_km,
            "max_autonomy": self.max_autonomy_km,
            "service": self.fleet_type,
            "fleet": self.fleetmanager_id.split("@")[0],
            "icon": self.icon
        }

    class MovingBehaviour(PeriodicBehaviour):
        """
        This is the internal behaviour that manages the movement of the transport.
        It is triggered when the transport has a new destination and the periodic tick
        is recomputed at every step to show a fine animation.
        This moving behaviour includes to update the transport coordinates as it
        moves along the path at the specified speed.
        """

        async def run(self):
            await self.agent.step()
            self.period = self.agent.animation_speed / ONESECOND_IN_MS
            if self.agent.is_in_destination():
                self.agent.remove_behaviour(self)


class RegistrationBehaviour(CyclicBehaviour):
    async def on_start(self):
        logger.debug("Strategy {} started in transport".format(type(self).__name__))

    async def send_registration(self):
        """
        Send a ``spade.message.Message`` with a proposal to manager to register.
        """
        logger.info(
            "Transport {} sent proposal to register to manager {}".format(self.agent.name, self.agent.fleetmanager_id))
        content = {
            "name": self.agent.name,
            "jid": str(self.agent.jid),
            "fleet_type": self.agent.fleet_type
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
                    logger.info("[{}] Registration in the fleet manager accepted: {}.".format(self.agent.name,
                                                                                              self.agent.fleetmanager_id))
                    self.kill(exit_code="Fleet Registration Accepted")
                elif performative == REFUSE_PERFORMATIVE:
                    logger.warning("Registration in the fleet manager was rejected (check fleet type).")
                    self.kill(exit_code="Fleet Registration Rejected")
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error("EXCEPTION in RegisterBehaviour of Transport {}: {}".format(self.agent.name, e))


class TransportStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a transport strategy.
    You must overload the ```run`` coroutine

    Helper functions:
        * ``pick_up_customer``
        * ``send_proposal``
        * ``cancel_proposal``
    """

    async def on_start(self):
        logger.debug("Strategy {} started in transport {}".format(type(self).__name__, self.agent.name))

    async def pick_up_customer(self, customer_id, origin, dest):
        """
        Starts a TRAVEL_PROTOCOL to pick up a customer and get him to his destination.
        It automatically launches all the travelling process until the customer is
        delivered. This travelling process includes to update the transport coordinates as it
        moves along the path at the specified speed.

        Args:
            customer_id (str): the id of the customer
            origin (list): the coordinates of the current location of the customer
            dest (list): the coordinates of the target destination of the customer
        """
        logger.info("Transport {} on route to customer {}".format(self.agent.name, customer_id))
        reply = Message()
        reply.to = customer_id
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        reply.set_metadata("protocol", TRAVEL_PROTOCOL)
        content = {
            "status": TRANSPORT_MOVING_TO_CUSTOMER
        }
        reply.body = json.dumps(content)
        self.set("current_customer", customer_id)
        self.agent.current_customer_orig = origin
        self.agent.current_customer_dest = dest
        await self.send(reply)
        self.agent.num_assignments += 1
        try:
            await self.agent.move_to(self.agent.current_customer_orig)
        except AlreadyInDestination:
            await self.agent.arrived_to_destination()

    async def send_confirmation_travel(self, station_id):
        logger.info("Transport {} sent confirmation to station {}".format(self.agent.name, station_id))
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
            customer_id (str): the id of the customer
            origin (list): the coordinates of the current location of the customer
            dest (list): the coordinates of the target destination of the customer
        """
        logger.info("Transport {} on route to station {}".format(self.agent.name, station_id))
        reply = Message()
        reply.to = station_id
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        reply.set_metadata("protocol", TRAVEL_PROTOCOL)
        content = {
            "status": TRANSPORT_MOVING_TO_STATION
        }
        reply.body = json.dumps(content)
        self.set("current_station", station_id)
        self.agent.current_station_dest = dest
        await self.send(reply)
        self.agent.num_charges += 1
        travel_km = self.agent.calculate_km_expense(self.get("current_pos"), dest)
        self.agent.set_km_expense(travel_km)
        try:
            logger.info("{} going to station {}".format(self.agent.name, station_id))
            await self.agent.move_to(self.agent.current_station_dest)
        except AlreadyInDestination:
            await self.agent.arrived_to_station()

    def has_enough_autonomy(self, customer_orig, customer_dest):
        autonomy = self.agent.get_autonomy()
        if autonomy <= MIN_AUTONOMY:
            logger.warning("{} has not enough autonomy ({}).".format(self.agent.name, autonomy))
            return False
        travel_km = self.agent.calculate_km_expense(self.get("current_pos"), customer_orig, customer_dest)
        if autonomy - travel_km < MIN_AUTONOMY:
            logger.warning("{} has not enough autonomy to do travel ({} for {} km).".format(self.agent.name,
                                                                                            autonomy, travel_km))
            return False
        self.agent.set_km_expense(travel_km)  # TODO
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
        logger.info("Transport {} asked for stations to Directory {} for type {}.".format(self.agent.name,
                                                                                          self.agent.directory_id,
                                                                                          self.agent.request))

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
        logger.info("Transport {} sent proposal to {}".format(self.agent.name, customer_id))
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
        logger.info("Transport {} sent cancel proposal to customer {}".format(self.agent.name, customer_id))
        reply = Message()
        reply.to = customer_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", CANCEL_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def run(self):
        raise NotImplementedError
