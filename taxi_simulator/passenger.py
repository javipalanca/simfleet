import json
import logging
import time

from spade.ACLMessage import ACLMessage
from spade.Agent import Agent
from spade.Behaviour import ACLTemplate, MessageTemplate, Behaviour

from utils import PASSENGER_WAITING, PASSENGER_IN_DEST, TAXI_MOVING_TO_PASSENGER, PASSENGER_IN_TAXI, \
    TAXI_IN_PASSENGER_PLACE, PASSENGER_LOCATION, StrategyBehaviour, request_path, status_to_str
from protocol import REQUEST_PROTOCOL, TRAVEL_PROTOCOL, REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, REFUSE_PERFORMATIVE
from helpers import coordinator_aid, random_position, content_to_json

logger = logging.getLogger("PassengerAgent")


class PassengerAgent(Agent):
    def __init__(self, agentjid, password, debug):
        Agent.__init__(self, agentjid, password, debug=debug)
        self.agent_id = None
        self.status = PASSENGER_WAITING
        self.current_pos = None
        self.dest = None
        self.port = None
        self.taxi_assigned = None
        self.init_time = None
        self.waiting_for_pickup_time = None
        self.pickup_time = None
        self.end_time = None

        self.knowledge_base = {}

    def store_value(self, key, value):
        """
        Stores a value (named by a key) in the agent's knowledge base that runs the behaviour.
        This allows the strategy to have persistent values between loops.

        Args:
            key (:obj:`str`): the name of the value.
            value (:obj:`object`): The object to be stored.
        """
        self.knowledge_base[key] = value

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

    def _setup(self):
        try:
            tpl = ACLTemplate()
            tpl.setProtocol(TRAVEL_PROTOCOL)
            template = MessageTemplate(tpl)
            travel_behaviour = TravelBehaviour()
            self.addBehaviour(travel_behaviour, template)
            while not self.hasBehaviour(travel_behaviour):
                logger.warn("Passenger {} could not create TravelBehaviour. Retrying...".format(self.agent_id))
                self.addBehaviour(travel_behaviour, template)
        except Exception as e:
            logger.error("EXCEPTION creating TravelBehaviour in Passenger {}: {}".format(self.agent_id, e))

    def add_strategy(self, strategy_class):
        """
        Sets the strategy for the passenger agent.

        Args:
            strategy_class (:class:`PassengerStrategyBehaviour`): The class to be used. Must inherit from :class:`PassengerStrategyBehaviour`
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

    def set_position(self, coords=None):
        """
        Sets the position of the passenger. If no position is provided it is located in a random position.

        Args:
            coords (:obj:`list`): a list coordinates (longitude and latitude)
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
            coords (:obj:`list`): a list coordinates (longitude and latitude)
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

    def request_path(self, origin, destination):
        """
        Requests a path between two points (origin and destination) using the RouteAgent service.

        Args:
            origin (:obj:`list`): the coordinates of the origin of the requested path
            destination (:obj:`list`): the coordinates of the end of the requested path

        Returns:
            list, float, float: A list of points that represent the path from origin to destination, the distance and the estimated duration
        """
        return request_path(self, origin, destination)

    def total_time(self):
        """
        Returns the time since the passenger was activated until it reached its destination.

        Returns:
            float: the total time of the passenger's simulation.
        """
        if self.init_time and self.end_time:
            return self.end_time - self.init_time
        else:
            return -1

    def get_waiting_time(self):
        """
        Returns the time that the agent was waiting for a taxi, from its creation until it gets into a taxi.

        Returns:
            float: The time the passenger was waiting.
        """
        if self.init_time:
            if self.pickup_time:
                t = self.pickup_time - self.init_time
            else:
                t = time.time() - self.init_time
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


class TravelBehaviour(Behaviour):
    """
    This is the internal behaviour that manages the movement of the passenger.
    It is triggered when the taxi informs the passenger that it is going to the
    passenger's position until the passenger is droppped in its destination.
    """
    def onStart(self):
        logger.debug("Passenger {} started TravelBehavior.".format(self.myAgent.agent_id))

    def _process(self):
        try:
            msg = self._receive(block=True)
            if msg:
                content = content_to_json(msg)
                logger.debug("Passenger {} informed of: {}".format(self.myAgent.agent_id, content))
                if "status" in content:
                    status = content["status"]
                    if status != 23:
                        logger.info("Passenger {} informed of status: {}".format(self.myAgent.agent_id,
                                                                                 status_to_str(status)))
                    if status == TAXI_MOVING_TO_PASSENGER:
                        logger.info("Passenger {} waiting for taxi.".format(self.myAgent.agent_id))
                        self.myAgent.waiting_for_pickup_time = time.time()
                    elif status == TAXI_IN_PASSENGER_PLACE:
                        self.myAgent.status = PASSENGER_IN_TAXI
                        logger.info("Passenger {} in taxi.".format(self.myAgent.agent_id))
                        self.myAgent.pickup_time = time.time()
                    elif status == PASSENGER_IN_DEST:
                        self.myAgent.status = PASSENGER_IN_DEST
                        self.myAgent.end_time = time.time()
                        logger.info("Passenger {} arrived to destination after {} seconds."
                                    .format(self.myAgent.agent_id, self.myAgent.total_time()))
                    elif status == PASSENGER_LOCATION:
                        coords = content["location"]
                        self.myAgent.set_position(coords)
        except Exception as e:
            logger.error("EXCEPTION in Travel Behaviour of Passenger {}: {}".format(self.myAgent.agent_id, e))


class PassengerStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a taxi strategy.
    You must overload the :func:`_process` method

    Helper functions:
        * :func:`send_request`
        * :func:`accept_taxi`
        * :func:`refuse_taxi`
    """
    def onStart(self):
        """
        Initializes the logger and timers. Call to parent method if overloaded.
        """
        self.logger = logging.getLogger("PassengerAgent")
        self.logger.debug("Strategy {} started in passenger {}".format(type(self).__name__, self.myAgent.agent_id))
        self.myAgent.init_time = time.time()

    def send_request(self, content=None):
        """
        Sends an :class:`ACLMessage` to the coordinator to request a taxi.
        It uses the REQUEST_PROTOCOL and the REQUEST_PERFORMATIVE.
        If no content is set a default content with the passenger_id,
        origin and target coordinates is used.

        Args:
            content (:obj:`dict`): Optional content dictionary
        """
        if content is None or len(content) == 0:
            content = {
                "passenger_id": self.myAgent.agent_id,
                "origin": self.myAgent.current_pos,
                "dest": self.myAgent.dest
            }
        if not self.myAgent.dest:
            self.myAgent.dest = random_position()
        msg = ACLMessage()
        msg.addReceiver(coordinator_aid)
        msg.setProtocol(REQUEST_PROTOCOL)
        msg.setPerformative(REQUEST_PERFORMATIVE)
        msg.setContent(json.dumps(content))
        self.myAgent.send(msg)
        self.logger.info("Passenger {} asked for a taxi to {}.".format(self.myAgent.agent_id, self.myAgent.dest))

    def accept_taxi(self, taxi_aid):
        """
        Sends an :class:`ACLMessage` to a taxi to accept a travel proposal.
        It uses the REQUEST_PROTOCOL and the ACCEPT_PERFORMATIVE.

        Args:
            taxi_aid (:obj:`spade.AID.aid`): The AgentID of the taxi
        """
        reply = ACLMessage()
        reply.addReceiver(taxi_aid)
        reply.setProtocol(REQUEST_PROTOCOL)
        reply.setPerformative(ACCEPT_PERFORMATIVE)
        content = {
            "passenger_id": self.myAgent.agent_id,
            "origin": self.myAgent.current_pos,
            "dest": self.myAgent.dest
        }
        reply.setContent(json.dumps(content))
        self.myAgent.send(reply)
        self.myAgent.taxi_assigned = taxi_aid.getName()
        self.logger.info("Passenger {} accepted proposal from taxi {}".format(self.myAgent.agent_id,
                                                                              taxi_aid.getName()))

    def refuse_taxi(self, taxi_aid):
        """
        Sends an ACLMessage to a taxi to refuse a travel proposal.
        It uses the REQUEST_PROTOCOL and the REFUSE_PERFORMATIVE.

        Args:
            taxi_aid (:class:`spade.AID.aid`): The AgentID of the taxi
        """
        reply = ACLMessage()
        reply.addReceiver(taxi_aid)
        reply.setProtocol(REQUEST_PROTOCOL)
        reply.setPerformative(REFUSE_PERFORMATIVE)
        content = {
            "passenger_id": self.myAgent.agent_id,
            "origin": self.myAgent.current_pos,
            "dest": self.myAgent.dest
        }
        reply.setContent(json.dumps(content))
        self.myAgent.send(reply)
        self.logger.info("Passenger {} refused proposal from taxi {}".format(self.myAgent.agent_id,
                                                                             taxi_aid.getName()))

    def _process(self):
        raise NotImplementedError
