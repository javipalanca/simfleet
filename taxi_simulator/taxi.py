import json
import logging

from collections import defaultdict
from spade.message import Message
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.template import Template

from .utils import TAXI_WAITING, TAXI_MOVING_TO_PASSENGER, TAXI_IN_PASSENGER_PLACE, TAXI_MOVING_TO_DESTINATION, \
    PASSENGER_IN_DEST, PASSENGER_LOCATION, chunk_path, request_path, StrategyBehaviour
from .protocol import REQUEST_PROTOCOL, TRAVEL_PROTOCOL, PROPOSE_PERFORMATIVE, CANCEL_PERFORMATIVE, INFORM_PERFORMATIVE
from .helpers import random_position, distance_in_meters, kmh_to_ms, PathRequestException, \
    AlreadyInDestination

logger = logging.getLogger("TaxiAgent")

ONESECOND_IN_MS = 1000


class TaxiAgent(Agent):
    def __init__(self, agentjid, password, loop=None):
        super().__init__(agentjid, password, loop=loop)

        self.coordinator_id = None
        self.route_id = None

        self.__observers = defaultdict(list)
        self.agent_id = None
        self.status = TAXI_WAITING
        self.set("current_pos", None)
        self.dest = None
        self.set("path", None)
        self.chunked_path = None
        self.set("speed_in_kmh", 2000)
        self.animation_speed = ONESECOND_IN_MS
        self.distances = []
        self.durations = []
        self.port = None
        self.set("current_passenger", None)
        self.current_passenger_orig = None
        self.current_passenger_dest = None
        self.set("passenger_in_taxi", None)
        self.num_assignments = 0
        self.stopped = False

    def watch_value(self, key, callback):
        """
        Registers an observer callback to be run when a value is changed

        Args:
            key (str): the name of the value
            callback (function): a function to be called when the value changes. It receives two arguments: the old and the new value.
        """
        self.__observers[key].append(callback)

    def add_strategy(self, strategy_class):
        """
        Sets the strategy for the taxi agent.

        Args:
            strategy_class (``TaxiStrategyBehaviour``): The class to be used. Must inherit from ``TaxiStrategyBehaviour``
        """
        template = Template()
        template.set_metadata("protocol", REQUEST_PROTOCOL)
        self.add_behaviour(strategy_class(), template)

    def set_id(self, agent_id):
        """
        Sets the agent identifier

        Args:
            agent_id (str): The new Agent Id
        """
        self.agent_id = agent_id

    def set_coordinator(self, coordinator_id):
        """
        Sets the coordinator JID address
        Args:
            coordinator_id (str): the coordinator jid

        """
        self.coordinator_id = coordinator_id

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

    def is_passenger_in_taxi(self):
        return self.get("passenger_in_taxi") is not None

    def is_free(self):
        return self.get("current_passenger") is None

    async def arrived_to_destination(self):
        """
        Informs that the taxi has arrived to its destination.
        It recomputes the new destination and path if picking up a passenger
        or drops it and goes to WAITING status again.
        """
        self.set("path", None)
        self.chunked_path = None
        if not self.is_passenger_in_taxi():  # self.status == TAXI_MOVING_TO_PASSENGER:
            try:
                self.set("passenger_in_taxi", self.get("current_passenger"))
                await self.move_to(self.current_passenger_dest)
            except PathRequestException:
                await self.cancel_passenger()
                self.status = TAXI_WAITING
            except AlreadyInDestination:
                await self.drop_passenger()
            else:
                await self.inform_passenger(TAXI_IN_PASSENGER_PLACE)
                self.status = TAXI_MOVING_TO_DESTINATION
                logger.info("Taxi {} has picked up the passenger {}.".format(self.agent_id,
                                                                             self.get("current_passenger")))
        else:  # elif self.status == TAXI_MOVING_TO_DESTINATION:
            await self.drop_passenger()

    async def drop_passenger(self):
        """
        Drops the passenger that the taxi is carring in the current location.
        """
        await self.inform_passenger(PASSENGER_IN_DEST)
        self.status = TAXI_WAITING
        logger.debug("Taxi {} has dropped the passenger {} in destination.".format(self.agent_id,
                                                                                   self.get(
                                                                                       "current_passenger")))
        self.set("current_passenger", None)
        self.set("passenger_in_taxi", None)

    async def move_to(self, dest):
        """
        Moves the taxi to a new destination.

        Args:
            dest (list): the coordinates of the new destination (in lon, lat format)

        Raises:
             AlreadyInDestination: if the taxi is already in the destination coordinates.
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

    async def inform_passenger(self, status, data=None):
        """
        Sends a message to the current assigned passenger to inform her about a new status.

        Args:
            status (int): The new status code
            data (dict, optional): complementary info about the status
        """
        if data is None:
            data = {}
        msg = Message()
        msg.to = self.get("current_passenger")
        msg.set_metadata("protocol", TRAVEL_PROTOCOL)
        msg.set_metadata("performative", INFORM_PERFORMATIVE)
        data["status"] = status
        msg.body = json.dumps(data)
        await self.send(msg)

    async def cancel_passenger(self, data=None):
        """
        Sends a message to the current assigned passenger to cancel the assignment.

        Args:
            data (dict, optional): Complementary info about the cancellation
        """
        logger.error("Taxi {} could not get a path to passenger {}.".format(self.agent_id,
                                                                            self.get("current_passenger")))
        if data is None:
            data = {}
        reply = Message()
        reply.to = self.get("current_passenger")
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", CANCEL_PERFORMATIVE)
        reply.body = json.dumps(data)
        logger.debug("Taxi {} sent cancel proposal to passenger {}".format(self.agent_id,
                                                                           self.get("current_passenger")))
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

    async def set_position(self, coords=None):
        """
        Sets the position of the taxi. If no position is provided it is located in a random position.

        Args:
            coords (list): a list coordinates (longitude and latitude)
        """
        if coords:
            self.set("current_pos", coords)
        else:
            self.set("current_pos", random_position())

        logger.debug("Taxi {} position is {}".format(self.agent_id, self.get("current_pos")))
        if self.status == TAXI_MOVING_TO_DESTINATION:
            await self.inform_passenger(PASSENGER_LOCATION, {"location": self.get("current_pos")})
        if self.is_in_destination():
            logger.info("Taxi {} has arrived to destination.".format(self.agent_id))
            await self.arrived_to_destination()

    def get_position(self):
        """
        Returns the current position of the passenger.

        Returns:
            list: the coordinates of the current position of the passenger (lon, lat)
        """
        return self.get("current_pos")

    def set_speed(self, speed_in_kmh):
        """
        Sets the speed of the taxi.

        Args:
            speed_in_kmh (float): the speed of the taxi in km per hour
        """
        self.set("speed_in_kmh", speed_in_kmh)

    def is_in_destination(self):
        """
        Checks if the taxi has arrived to its destination.

        Returns:
            bool: whether the taxi is at its destination or not
        """
        return self.dest == self.get_position()

    def to_json(self):
        """
        Serializes the main information of a taxi agent to a JSON format.
        It includes the id of the agent, its current position, the destination coordinates of the agent,
        the current status, the speed of the taxi (in km/h), the path it is following (if any), the passenger that it
        has assigned (if any), the number of assignments if has done and the distance that the taxi has traveled.

        Returns:
            dict: a JSON doc with the main information of the taxi.

            Example::

                {
                    "id": "cphillips",
                    "position": [ 39.461327, -0.361839 ],
                    "dest": [ 39.460599, -0.335041 ],
                    "status": 24,
                    "speed": 1000,
                    "path": [[0,0], [0,1], [1,0], [1,1], ...],
                    "passenger": "ghiggins@127.0.0.1",
                    "assignments": 2,
                    "distance": 3481.34
                }
        """
        return {
            "id": self.agent_id,
            "position": self.get("current_pos"),
            "dest": self.dest,
            "status": self.status,
            "speed": float("{0:.2f}".format(self.animation_speed)) if self.animation_speed else None,
            "path": self.get("path"),
            "passenger": self.get("current_passenger") if self.get("current_passenger") else None,
            "assignments": self.num_assignments,
            "distance": "{0:.2f}".format(sum(self.distances)),
        }

    class MovingBehaviour(PeriodicBehaviour):
        """
        This is the internal behaviour that manages the movement of the taxi.
        It is triggered when the taxi has a new destination and the periodic tick
        is recomputed at every step to show a fine animation.
        This moving behaviour includes to update the taxi coordinates as it
        moves along the path at the specified speed.
        """

        async def run(self):
            await self.agent.step()
            self.period = self.agent.animation_speed / ONESECOND_IN_MS
            if self.agent.is_in_destination():
                self.agent.remove_behaviour(self)


class TaxiStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a taxi strategy.
    You must overload the ```run`` coroutine

    Helper functions:
        * ``pick_up_passenger``
        * ``send_proposal``
        * ``cancel_proposal``
    """

    async def on_start(self):
        self.logger = logging.getLogger("TaxiStrategy")
        self.logger.debug("Strategy {} started in taxi {}".format(type(self).__name__, self.agent.name))

    async def pick_up_passenger(self, passenger_id, origin, dest):
        """
        Starts a TRAVEL_PROTOCOL to pick up a passenger and get him to his destination.
        It automatically launches all the travelling process until the passenger is
        delivered. This travelling process includes to update the taxi coordinates as it
        moves along the path at the specified speed.

        Args:
            passenger_id (str): the id of the passenger
            origin (list): the coordinates of the current location of the passenger
            dest (list): the coordinates of the target destination of the passenger
        """
        logger.info("Taxi {} on route to passenger {}".format(self.agent.name, passenger_id))
        reply = Message()
        reply.to = passenger_id
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        reply.set_metadata("protocol", TRAVEL_PROTOCOL)
        content = {
            "status": TAXI_MOVING_TO_PASSENGER
        }
        reply.body = json.dumps(content)
        self.set("current_passenger", passenger_id)
        self.agent.current_passenger_orig = origin
        self.agent.current_passenger_dest = dest
        await self.send(reply)
        self.agent.num_assignments += 1
        try:
            await self.agent.move_to(self.agent.current_passenger_orig)
        except AlreadyInDestination:
            await self.agent.arrived_to_destination()

    async def send_proposal(self, passenger_id, content=None):
        """
        Send a ``spade.message.Message`` with a proposal to a passenger to pick up him.
        If the content is empty the proposal is sent without content.

        Args:
            passenger_id (str): the id of the passenger
            content (dict, optional): the optional content of the message
        """
        if content is None:
            content = {}
        logger.info("Taxi {} sent proposal to passenger {}".format(self.agent.name, passenger_id))
        reply = Message()
        reply.to = passenger_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", PROPOSE_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def cancel_proposal(self, passenger_id, content=None):
        """
        Send a ``spade.message.Message`` to cancel a proposal.
        If the content is empty the proposal is sent without content.

        Args:
            passenger_id (str): the id of the passenger
            content (dict, optional): the optional content of the message
        """
        if content is None:
            content = {}
        logger.info("Taxi {} sent cancel proposal to passenger {}".format(self.agent.name, passenger_id))
        reply = Message()
        reply.to = passenger_id
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", CANCEL_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def run(self):
        raise NotImplementedError
