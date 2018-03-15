import json
import logging

from collections import defaultdict
from spade.ACLMessage import ACLMessage
from spade.Agent import Agent
from spade.Behaviour import ACLTemplate, MessageTemplate, PeriodicBehaviour

from utils import TAXI_WAITING, TAXI_MOVING_TO_PASSENGER, TAXI_IN_PASSENGER_PLACE, TAXI_MOVING_TO_DESTINATION, \
    PASSENGER_IN_DEST, PASSENGER_LOCATION, chunk_path, request_path, StrategyBehaviour
from protocol import REQUEST_PROTOCOL, TRAVEL_PROTOCOL, PROPOSE_PERFORMATIVE, CANCEL_PERFORMATIVE, INFORM_PERFORMATIVE
from helpers import build_aid, random_position, distance_in_meters, kmh_to_ms, PathRequestException, \
    AlreadyInDestination

logger = logging.getLogger("TaxiAgent")

ONESECOND_IN_MS = 1000


class TaxiAgent(Agent):
    def __init__(self, agentjid, password, debug):
        Agent.__init__(self, agentjid, password, debug=debug)
        self.knowledge_base = {}
        self.__observers = defaultdict(list)

        self.agent_id = None
        self.status = TAXI_WAITING
        self.store_value("current_pos", None)
        self.dest = None
        self.store_value("path", None)
        self.chunked_path = None
        self.store_value("speed_in_kmh", 2000)
        self.animation_speed = ONESECOND_IN_MS
        self.distances = []
        self.durations = []
        self.port = None
        self.store_value("current_passenger", None)
        self.current_passenger_orig = None
        self.current_passenger_dest = None
        self.store_value("passenger_in_taxi", None)
        self.num_assignments = 0

    def store_value(self, key, value):
        """
        Stores a value (named by a key) in the agent's knowledge base that runs the behaviour.
        This allows the strategy to have persistent values between loops.

        Args:
            key (:obj:`str`): the name of the value.
            value (:obj:`object`): The object to be stored.
        """

        old = self.knowledge_base.get(key)
        self.knowledge_base[key] = value

        if key in self.__observers:
            for cb in self.__observers[key]:
                cb(old, value)

    def get_value(self, key):
        """
        Returns a stored value from the agent's knowledge base.

        Args:
            key (:obj:`str`): the name of the value

        Returns:
            :data:`object`: The object stored with the key

        Raises:
            KeyError: if the key is not in the knowledge base
        """
        return self.knowledge_base.get(key)

    def has_value(self, key):
        """
        Checks if a key is registered in the agent's knowledge base

        Args:
            key (:obj:`str`): the name of the value to be checked

        Returns:
            bool: whether the knowledge base has or not the key
        """
        return key in self.knowledge_base

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
            strategy_class (:class:`TaxiStrategyBehaviour`): The class to be used. Must inherit from :class:`TaxiStrategyBehaviour`
        """
        tpl = ACLTemplate()
        tpl.setProtocol(REQUEST_PROTOCOL)
        template = MessageTemplate(tpl)
        self.addBehaviour(strategy_class(), template)

    def set_id(self, agent_id):
        """
        Sets the agent identifier

        Args:
            agent_id (:obj:`str`): The new Agent Id
        """
        self.agent_id = agent_id

    def arrived_to_destination(self):
        """
        MVC view executed when the taxi has arrived to its destination.
        It recomputes the new destination and path if picking up a passenger
        or drops it and goes to WAITING status again.

        Returns:
            :data:`None`, :obj:`dict`: an empty template and data. This view is a JSON request, so it does not render any new template.
        """
        self.store_value("path", None)
        self.chunked_path = None
        if not self.is_passenger_in_taxi():  # self.status == TAXI_MOVING_TO_PASSENGER:
            try:
                self.move_to(self.current_passenger_dest)
                self.store_value("passenger_in_taxi", self.get_value("current_passenger"))
            except PathRequestException:
                self.cancel_passenger()
                self.status = TAXI_WAITING
            except AlreadyInDestination:
                self.drop_passenger()
            else:
                self.inform_passenger(TAXI_IN_PASSENGER_PLACE)
                self.status = TAXI_MOVING_TO_DESTINATION
                logger.info("Taxi {} has picked up the passenger {}."
                            .format(self.agent_id, self.get_value("current_passenger").getName()))
        else:  # elif self.status == TAXI_MOVING_TO_DESTINATION:
            self.drop_passenger()

        return None, {}

    def is_passenger_in_taxi(self):
        return self.get_value("passenger_in_taxi") is not None

    def is_free(self):
        return self.get_value("current_passenger") is None

    def drop_passenger(self):
        """
        Drops the passenger that the taxi is carring in the current location.
        """
        self.inform_passenger(PASSENGER_IN_DEST)
        self.status = TAXI_WAITING
        logger.info("Taxi {} has dropped the passenger {} in destination.".format(self.agent_id,
                                                                                  self.get_value("current_passenger")
                                                                                  .getName()))
        self.store_value("current_passenger", None)
        self.store_value("passenger_in_taxi", None)

    def request_path(self, origin, destination):
        """
        Requests a path between two points (origin and destination) using the RouteAgent service.

        Args:
            origin (:obj:`list`): the coordinates of the origin of the requested path
            destination (:obj:`list`): the coordinates of the end of the requested path

        Returns:
            list, float, float: A list of points that represent the path from origin to destination, the distance and the estimated duration

        Examples:
            >>> path, distance, duration = self.request_path(origin=[0,0], destination=[1,1])
            >>> print(path)
            [[0,0], [0,1], [1,1]]
            >>> print(distance)
            2.0
            >>> print(duration)
            3.24
        """
        return request_path(self, origin, destination)

    def set_position(self, coords=None):
        """
        Sets the position of the taxi. If no position is provided it is located in a random position.

        Args:
            coords (:obj:`list`): a list coordinates (longitude and latitude)
        """
        if coords:
            self.store_value("current_pos", coords)
        else:
            self.store_value("current_pos", random_position())

        logger.debug("Taxi {} position is {}".format(self.agent_id, self.get_value("current_pos")))
        if self.status == TAXI_MOVING_TO_DESTINATION:
            self.inform_passenger(PASSENGER_LOCATION, {"location": self.get_value("current_pos")})
        if self.is_in_destination():
            logger.info("Taxi {} has arrived to destination.".format(self.agent_id))
            self.arrived_to_destination()

    def get_position(self):
        """
        Returns the current position of the passenger.

        Returns:
            list: the coordinates of the current position of the passenger (lon, lat)
        """
        return self.get_value("current_pos")

    def set_speed(self, speed_in_kmh):
        """
        Sets the speed of the taxi.

        Args:
            speed_in_kmh (float): the speed of the taxi in km per hour
        """
        self.store_value("speed_in_kmh", speed_in_kmh)

    def is_in_destination(self):
        """
        Checks if the taxi has arrived to its destination.

        Returns:
            bool: whether the taxi is at its destination or not
        """
        return self.dest == self.get_position()

    def move_to(self, dest):
        """
        Moves the taxi to a new destination.

        Args:
            dest (:obj:`list`): the coordinates of the new destination (in lon, lat format)

        Raises:
             AlreadyInDestination: if the taxi is already in the destination coordinates.
        """
        if self.get_value("current_pos") == dest:
            raise AlreadyInDestination
        counter = 5
        path = None
        distance, duration = 0, 0
        while counter > 0 and path is None:
            logger.debug("Requesting path from {} to {}".format(self.get_value("current_pos"), dest))
            path, distance, duration = self.request_path(self.get_value("current_pos"), dest)
            counter -= 1
        if path is None:
            raise PathRequestException("Error requesting route.")

        self.store_value("path", path)
        try:
            self.chunked_path = chunk_path(path, self.get_value("speed_in_kmh"))
        except Exception as e:
            logger.error("Exception chunking path {}: {}".format(path, e))
            raise PathRequestException
        self.dest = dest
        self.distances.append(distance)
        self.durations.append(duration)
        behav = self.MovingBehaviour(period=1)
        self.addBehaviour(behav)

    def step(self):
        """
        Advances one step in the simulation
        """
        if self.chunked_path:
            _next = self.chunked_path.pop(0)
            distance = distance_in_meters(self.get_position(), _next)
            self.animation_speed = distance / kmh_to_ms(self.get_value("speed_in_kmh")) * ONESECOND_IN_MS
            self.set_position(_next)

    def inform_passenger(self, status, data=None):
        """
        Sends a message to the current assigned passenger to inform her about a new status.

        Args:
            status (int): The new status code
            data (dict optional): complementary info about the status
        """
        if data is None:
            data = {}
        msg = ACLMessage()
        msg.addReceiver(self.get_value("current_passenger"))
        msg.setProtocol(TRAVEL_PROTOCOL)
        msg.setPerformative(INFORM_PERFORMATIVE)
        data["status"] = status
        msg.setContent(json.dumps(data))
        self.send(msg)

    def cancel_passenger(self, data=None):
        """
        Sends a message to the current assigned passenger to cancel the assignment.

        Args:
            data (dict optional): Complementary info about the cancellation
        """
        logger.error("Taxi {} could not get a path to passenger {}.".format(self.agent_id,
                                                                            self.get_value("current_passenger")
                                                                            .getName()))
        if data is None:
            data = {}
        reply = ACLMessage()
        reply.addReceiver(self.get_value("current_passenger"))
        reply.setProtocol(REQUEST_PROTOCOL)
        reply.setPerformative(CANCEL_PERFORMATIVE)
        reply.setContent(json.dumps(data))
        logger.info("Taxi {} sent cancel proposal to passenger {}".format(self.agent_id,
                                                                          self.get_value("current_passenger")
                                                                          .getName()))
        self.send(reply)

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
            "position": self.get_value("current_pos"),
            "dest": self.dest,
            "status": self.status,
            "speed": float("{0:.2f}".format(self.animation_speed)) if self.animation_speed else None,
            "path": self.get_value("path"),
            "passenger": self.get_value("current_passenger").getName() if self.get_value("current_passenger") else None,
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
        def _onTick(self):
            self.myAgent.step()
            self.setPeriod(self.myAgent.animation_speed / ONESECOND_IN_MS)
            if self.myAgent.is_in_destination():
                self.myAgent.removeBehaviour(self)


class TaxiStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a taxi strategy.
    You must overload the :func:`_process` method

    Helper functions:
        * :func:`pick_up_passenger`
        * :func:`send_proposal`
        * :func:`cancel_proposal`
    """
    def onStart(self):
        self.logger = logging.getLogger("TaxiAgent")
        self.logger.debug("Strategy {} started in taxi {}".format(type(self).__name__, self.myAgent.agent_id))

    def pick_up_passenger(self, passenger_id, origin, dest):
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
        self.logger.info("Taxi {} on route to passenger {}".format(self.myAgent.agent_id, passenger_id))
        passenger_aid = build_aid(passenger_id)
        reply = ACLMessage()
        reply.addReceiver(passenger_aid)
        reply.setPerformative(INFORM_PERFORMATIVE)
        reply.setProtocol(TRAVEL_PROTOCOL)
        content = {
            "status": TAXI_MOVING_TO_PASSENGER
        }
        reply.setContent(json.dumps(content))
        self.myAgent.store_value("current_passenger", passenger_aid)
        self.myAgent.current_passenger_orig = origin
        self.myAgent.current_passenger_dest = dest
        self.myAgent.send(reply)
        self.myAgent.num_assignments += 1
        try:
            self.myAgent.move_to(self.myAgent.current_passenger_orig)
        except AlreadyInDestination:
            self.myAgent.arrived_to_destination()

    def send_proposal(self, passenger_id, content=None):
        """
        Send an :class:`ACLMessage` with a proposal to a passenger to pick up him.
        If the content is empty the proposal is sent without content.

        Args:
            passenger_id (str): the id of the passenger
            content (dict optional): the optional content of the message
        """
        if content is None:
            content = {}
        self.logger.info("Taxi {} sent proposal to passenger {}".format(self.myAgent.agent_id, passenger_id))
        passenger_aid = build_aid(passenger_id)
        reply = ACLMessage()
        reply.addReceiver(passenger_aid)
        reply.setProtocol(REQUEST_PROTOCOL)
        reply.setPerformative(PROPOSE_PERFORMATIVE)
        reply.setContent(content)
        self.myAgent.send(reply)

    def cancel_proposal(self, passenger_id, content=None):
        """
        Send an :class:`ACLMessage` to cancel a proposal.
        If the content is empty the proposal is sent without content.

        Args:
            passenger_id (str): the id of the passenger
            content (dict optional): the optional content of the message
        """
        if content is None:
            content = {}
        self.logger.info("Taxi {} sent cancel proposal to passenger {}".format(self.myAgent.agent_id, passenger_id))
        passenger_aid = build_aid(passenger_id)
        reply = ACLMessage()
        reply.addReceiver(passenger_aid)
        reply.setProtocol(REQUEST_PROTOCOL)
        reply.setPerformative(CANCEL_PERFORMATIVE)
        reply.setContent(json.dumps(content))
        self.myAgent.send(reply)

    def _process(self):
        raise NotImplementedError
