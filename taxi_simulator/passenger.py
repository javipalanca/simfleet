import json
import logging
import time

from spade.message import Message
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template

from .utils import PASSENGER_WAITING, PASSENGER_IN_DEST, TAXI_MOVING_TO_PASSENGER, PASSENGER_IN_TAXI, \
    TAXI_IN_PASSENGER_PLACE, PASSENGER_LOCATION, StrategyBehaviour, request_path, status_to_str
from .protocol import REQUEST_PROTOCOL, TRAVEL_PROTOCOL, REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE
from .helpers import random_position

logger = logging.getLogger("PassengerAgent")


class PassengerAgent(Agent):
    def __init__(self, agentjid, password, loop=None):
        super().__init__(agentjid, password, loop=loop)
        self.agent_id = None
        self.coordinator_id = None
        self.route_id = None
        self.status = PASSENGER_WAITING
        self.current_pos = None
        self.dest = None
        self.port = None
        self.taxi_assigned = None
        self.init_time = None
        self.waiting_for_pickup_time = None
        self.pickup_time = None
        self.end_time = None
        self.stopped = False

    def setup(self):
        try:
            template = Template()
            template.set_metadata("protocol", TRAVEL_PROTOCOL)
            travel_behaviour = TravelBehaviour()
            self.add_behaviour(travel_behaviour, template)
            while not self.has_behaviour(travel_behaviour):
                logger.warning("Passenger {} could not create TravelBehaviour. Retrying...".format(self.agent_id))
                self.add_behaviour(travel_behaviour, template)
        except Exception as e:
            logger.error("EXCEPTION creating TravelBehaviour in Passenger {}: {}".format(self.agent_id, e))

    def add_strategy(self, strategy_class):
        """
        Sets the strategy for the passenger agent.

        Args:
            strategy_class (``PassengerStrategyBehaviour``): The class to be used. Must inherit from ``PassengerStrategyBehaviour``
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

    async def set_position(self, coords=None):
        """
        Sets the position of the passenger. If no position is provided it is located in a random position.

        Args:
            coords (list): a list coordinates (longitude and latitude)
        """
        if coords:
            self.current_pos = coords
        else:
            self.current_pos = random_position()
        logger.debug("Passenger {} position is {}".format(self.agent_id, self.current_pos))

    def get_position(self):
        """
        Returns the current position of the passenger.

        Returns:
            list: the coordinates of the current position of the passenger (lon, lat)
        """
        return self.current_pos

    def set_target_position(self, coords=None):
        """
        Sets the target position of the passenger (i.e. its destination).
        If no position is provided the destination is setted to a random position.

        Args:
            coords (list): a list coordinates (longitude and latitude)
        """
        if coords:
            self.dest = coords
        else:
            self.dest = random_position()
        logger.debug("Passenger {} target position is {}".format(self.agent_id, self.dest))

    def is_in_destination(self):
        """
        Checks if the passenger has arrived to its destination.

        Returns:
            bool: whether the passenger is at its destination or not
        """
        return self.status == PASSENGER_IN_DEST or self.get_position() == self.dest

    async def request_path(self, origin, destination):
        """
        Requests a path between two points (origin and destination) using the RouteAgent service.

        Args:
            origin (list): the coordinates of the origin of the requested path
            destination (list): the coordinates of the end of the requested path

        Returns:
            list, float, float: A list of points that represent the path from origin to destination, the distance and the estimated duration
        """
        return await request_path(self, origin, destination)

    def total_time(self):
        """
        Returns the time since the passenger was activated until it reached its destination.

        Returns:
            float: the total time of the passenger's simulation.
        """
        if self.init_time and self.end_time:
            return self.end_time - self.init_time
        else:
            return None

    def get_waiting_time(self):
        """
        Returns the time that the agent was waiting for a taxi, from its creation until it gets into a taxi.

        Returns:
            float: The time the passenger was waiting.
        """
        if self.init_time:
            if self.pickup_time:
                t = self.pickup_time - self.init_time
            elif not self.stopped:
                t = time.time() - self.init_time
                self.waiting_for_pickup_time = t
            else:
                t = self.waiting_for_pickup_time
            return t
        return None

    def get_pickup_time(self):
        """
        Returns the time that the passenger was waiting to be picked up since it has been assigned to a taxi.

        Returns:
            float: The time that the passenger was waiting to a taxi since it has been assigned.
        """
        if self.pickup_time:
            return self.pickup_time - self.waiting_for_pickup_time
        return None

    def to_json(self):
        """
        Serializes the main information of a passenger agent to a JSON format.
        It includes the id of the agent, its current position, the destination coordinates of the agent,
        the current status, the taxi that it has assigned (if any) and its waiting time.

        Returns:
            dict: a JSON doc with the main information of the passenger.

            Example::

                {
                    "id": "cphillips",
                    "position": [ 39.461327, -0.361839 ],
                    "dest": [ 39.460599, -0.335041 ],
                    "status": 24,
                    "taxi": "ghiggins@127.0.0.1",
                    "waiting": 13.45
                }
        """
        t = self.get_waiting_time()
        return {
            "id": self.agent_id,
            "position": self.current_pos,
            "dest": self.dest,
            "status": self.status,
            "taxi": self.taxi_assigned,
            "waiting": float("{0:.2f}".format(t)) if t else None
        }


class TravelBehaviour(CyclicBehaviour):
    """
    This is the internal behaviour that manages the movement of the passenger.
    It is triggered when the taxi informs the passenger that it is going to the
    passenger's position until the passenger is droppped in its destination.
    """

    async def on_start(self):
        logger.debug("Passenger {} started TravelBehavior.".format(self.agent.name))

    async def run(self):
        try:
            msg = await self.receive(timeout=5)
            if not msg:
                return
            content = json.loads(msg.body)
            logger.debug("Passenger {} informed of: {}".format(self.agent.name, content))
            if "status" in content:
                status = content["status"]
                if status != PASSENGER_LOCATION:
                    logger.debug("Passenger {} informed of status: {}".format(self.agent.name,
                                                                              status_to_str(status)))
                if status == TAXI_MOVING_TO_PASSENGER:
                    logger.info("Passenger {} waiting for taxi.".format(self.agent.name))
                    self.agent.waiting_for_pickup_time = time.time()
                elif status == TAXI_IN_PASSENGER_PLACE:
                    self.agent.status = PASSENGER_IN_TAXI
                    logger.info("Passenger {} in taxi.".format(self.agent.name))
                    self.agent.pickup_time = time.time()
                elif status == PASSENGER_IN_DEST:
                    self.agent.status = PASSENGER_IN_DEST
                    self.agent.end_time = time.time()
                    logger.info("Passenger {} arrived to destination after {} seconds."
                                .format(self.agent.name, self.agent.total_time()))
                elif status == PASSENGER_LOCATION:
                    coords = content["location"]
                    await self.agent.set_position(coords)
        except Exception as e:
            logger.error("EXCEPTION in Travel Behaviour of Passenger {}: {}".format(self.agent.name, e))


class PassengerStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a taxi strategy.
    You must overload the ``run`` coroutine

    Helper functions:
        * ``send_request``
        * ``accept_taxi``
        * ``refuse_taxi``
    """

    async def on_start(self):
        """
        Initializes the logger and timers. Call to parent method if overloaded.
        """
        self.logger = logging.getLogger("PassengerStrategy")
        self.logger.debug("Strategy {} started in passenger {}".format(type(self).__name__, self.agent.name))
        self.agent.init_time = time.time()

    async def send_request(self, content=None):
        """
        Sends an ``spade.message.Message`` to the coordinator to request a taxi.
        It uses the REQUEST_PROTOCOL and the REQUEST_PERFORMATIVE.
        If no content is set a default content with the passenger_id,
        origin and target coordinates is used.

        Args:
            content (dict): Optional content dictionary
        """
        if content is None or len(content) == 0:
            content = {
                "passenger_id": str(self.agent.jid),
                "origin": self.agent.current_pos,
                "dest": self.agent.dest
            }
        if not self.agent.dest:
            self.agent.dest = random_position()
        msg = Message()
        msg.to = self.agent.coordinator_id
        msg.set_metadata("protocol", REQUEST_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)
        self.logger.info("Passenger {} asked for a taxi to {}.".format(self.agent.name, self.agent.dest))

    async def accept_taxi(self, taxi_id):
        """
        Sends a ``spade.message.Message`` to a taxi to accept a travel proposal.
        It uses the REQUEST_PROTOCOL and the ACCEPT_PERFORMATIVE.

        Args:
            taxi_id (str): The Agent JID of the taxi
        """
        reply = Message()
        reply.to = str(taxi_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
        content = {
            "passenger_id": str(self.agent.jid),
            "origin": self.agent.current_pos,
            "dest": self.agent.dest
        }
        reply.body = json.dumps(content)
        await self.send(reply)
        self.agent.taxi_assigned = str(taxi_id)
        self.logger.info("Passenger {} accepted proposal from taxi {}".format(self.agent.name,
                                                                              taxi_id))

    async def refuse_taxi(self, taxi_id):
        """
        Sends an ``spade.message.Message`` to a taxi to refuse a travel proposal.
        It uses the REQUEST_PROTOCOL and the REFUSE_PERFORMATIVE.

        Args:
            taxi_id (str): The Agent JID of the taxi
        """
        reply = Message()
        reply.to = str(taxi_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", REFUSE_PERFORMATIVE)
        content = {
            "passenger_id": str(self.agent.jid),
            "origin": self.agent.current_pos,
            "dest": self.agent.dest
        }
        reply.body = json.dumps(content)

        await self.send(reply)
        self.logger.info("Passenger {} refused proposal from taxi {}".format(self.agent.name,
                                                                             taxi_id))

    async def run(self):
        raise NotImplementedError
