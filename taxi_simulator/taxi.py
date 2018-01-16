import json
import logging

from spade.ACLMessage import ACLMessage
from spade.Agent import Agent
from spade.Behaviour import ACLTemplate, MessageTemplate, PeriodicBehaviour

from utils import TAXI_WAITING, TAXI_MOVING_TO_PASSENGER, TAXI_IN_PASSENGER_PLACE, TAXI_MOVING_TO_DESTINY, \
    PASSENGER_IN_DEST, PASSENGER_LOCATION, chunk_path, StrategyBehaviour
from protocol import REQUEST_PROTOCOL, TRAVEL_PROTOCOL, PROPOSE_PERFORMATIVE, CANCEL_PERFORMATIVE, INFORM_PERFORMATIVE
from helpers import build_aid, random_position, distance_in_meters, request_path, kmh_to_ms, PathRequestException, \
    AlreadyInDestination

logger = logging.getLogger("TaxiAgent")

ONESECOND_IN_MS = 1000


class TaxiAgent(Agent):
    def __init__(self, agentjid, password, debug):
        Agent.__init__(self, agentjid, password, debug=debug)
        self.agent_id = None
        self.status = TAXI_WAITING
        self.current_pos = None
        self.dest = None
        self.path = None
        self.chunked_path = None
        self.speed_in_kmh = 2000
        self.animation_speed = ONESECOND_IN_MS
        self.distances = []
        self.durations = []
        self.port = None
        self.current_passenger = None
        self.current_passenger_orig = None
        self.current_passenger_dest = None
        self.num_assignments = 0

        self.knowledge_base = {}

    def store_value(self, key, value):
        self.knowledge_base[key] = value

    def get_value(self, key):
        return self.knowledge_base.get(key)

    def has_value(self, key):
        return key in self.knowledge_base

    def add_strategy(self, strategy_class):
        tpl = ACLTemplate()
        tpl.setProtocol(REQUEST_PROTOCOL)
        template = MessageTemplate(tpl)
        self.addBehaviour(strategy_class(), template)

    def arrived_to_destination(self):
        self.path = None
        if self.status == TAXI_MOVING_TO_PASSENGER:
            try:
                self.move_to(self.current_passenger_dest)
            except PathRequestException:
                self.cancel_passenger()
                self.status = TAXI_WAITING
            except AlreadyInDestination:
                self.drop_passenger()
            else:
                self.inform_passenger(TAXI_IN_PASSENGER_PLACE)
                self.status = TAXI_MOVING_TO_DESTINY
                logger.info(
                    "Taxi {} has picked up the passenger {}.".format(self.agent_id, self.current_passenger.getName()))
        elif self.status == TAXI_MOVING_TO_DESTINY:
            self.drop_passenger()

        return None, {}

    def drop_passenger(self):
        self.inform_passenger(PASSENGER_IN_DEST)
        self.status = TAXI_WAITING
        logger.info("Taxi {} has dropped the passenger {} in destination.".format(self.agent_id,
                                                                                  self.current_passenger.getName()))
        self.current_passenger = None

    def set_id(self, agent_id):
        self.agent_id = agent_id

    def set_position(self, coords=None):
        if coords:
            self.current_pos = coords
        else:
            self.current_pos = random_position()

        logger.debug("Taxi {} position is {}".format(self.agent_id, self.current_pos))
        if self.status == TAXI_MOVING_TO_DESTINY:
            self.inform_passenger(PASSENGER_LOCATION, {"location": self.current_pos})
        if self.is_in_destination():
            logger.info("Taxi {} has arrived to destination.".format(self.agent_id))
            self.arrived_to_destination()

    def get_position(self):
        return self.current_pos

    def set_speed(self, speed_in_kmh):
        self.speed_in_kmh = speed_in_kmh

    def is_in_destination(self):
        return self.dest == self.get_position()

    def move_to(self, dest):
        if self.current_pos == dest:
            raise AlreadyInDestination
        counter = 5
        path = None
        distance, duration = 0, 0
        while counter > 0 and path is None:
            logger.debug("Requesting path from {} to {}".format(self.current_pos, dest))
            path, distance, duration = request_path(self.current_pos, dest)
            counter -= 1
        if path is None:
            raise PathRequestException

        self.path = path
        try:
            self.chunked_path = chunk_path(path, self.speed_in_kmh)
        except Exception as e:
            logger.error("Exception chunking path {}: {}".format(path, e))
            raise PathRequestException
        self.dest = dest
        self.distances.append(distance)
        self.durations.append(duration)
        behav = self.MovingBehaviour(period=1)
        self.addBehaviour(behav)

    def step(self):
        if self.chunked_path:
            _next = self.chunked_path.pop(0)
            distance = distance_in_meters(self.get_position(), _next)
            self.animation_speed = distance / kmh_to_ms(self.speed_in_kmh) * ONESECOND_IN_MS
            self.set_position(_next)

    def inform_passenger(self, status, data=None):
        if data is None:
            data = {}
        msg = ACLMessage()
        msg.addReceiver(self.current_passenger)
        msg.setProtocol(TRAVEL_PROTOCOL)
        msg.setPerformative(INFORM_PERFORMATIVE)
        data["status"] = status
        msg.setContent(json.dumps(data))
        self.send(msg)

    def cancel_passenger(self, data=None):
        logger.error("Taxi {} could not get a path to passenger {}.".format(self.agent_id,
                                                                            self.current_passenger.getName()))
        if data is None:
            data = {}
        reply = ACLMessage()
        reply.addReceiver(self.current_passenger)
        reply.setProtocol(REQUEST_PROTOCOL)
        reply.setPerformative(CANCEL_PERFORMATIVE)
        reply.setContent(json.dumps(data))
        logger.debug("Taxi {} sent cancel proposal to passenger {}".format(self.agent_id,
                                                                           self.current_passenger.getName()))
        self.send(reply)

    def to_json(self):
        return {
            "id": self.agent_id,
            "position": self.current_pos,
            "speed": float("{0:.2f}".format(self.animation_speed)) if self.animation_speed else None,
            "dest": self.dest,
            "status": self.status,
            "path": self.path,
            "passenger": self.current_passenger.getName() if self.current_passenger else None,
            "assignments": self.num_assignments,
            "distance": "{0:.2f}".format(sum(self.distances)),
            "url": "http://127.0.0.1:{port}".format(port=self.port)
        }

    class MovingBehaviour(PeriodicBehaviour):
        def _onTick(self):
            self.myAgent.step()
            self.setPeriod(self.myAgent.animation_speed / ONESECOND_IN_MS)
            if self.myAgent.is_in_destination():
                self.myAgent.removeBehaviour(self)


class TaxiStrategyBehaviour(StrategyBehaviour):
    def onStart(self):
        self.logger = logging.getLogger("TaxiAgent")
        self.logger.debug("Strategy {} started in taxi {}".format(type(self).__name__, self.myAgent.agent_id))

    def pick_up_passenger(self, passenger_id, origin, dest):
        """
        Starts a TRAVEL_PROTOCOL to pick up a passenger and get him to his destiny.
        It automatically launches all the graphical process until the passenger is
        delivered.
        :param passenger_id: the id of the passenger
        :type passenger_id: :class:`str`
        :param origin: the coordinates of the current location of the passenger
        :type origin: :class:`list`
        :param dest: the coordinates of the target destiny of the passenger
        :type dest: :class:`list`
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
        self.myAgent.current_passenger = passenger_aid
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
        :param passenger_id: the id of the passenger
        :type passenger_id: :class:`str`
        :param content: the optional content of the message
        :type content: :class:`dict`
        """
        if content is None:
            content = {}
        passenger_aid = build_aid(passenger_id)
        reply = ACLMessage()
        reply.addReceiver(passenger_aid)
        reply.setProtocol(REQUEST_PROTOCOL)
        reply.setPerformative(PROPOSE_PERFORMATIVE)
        reply.setContent(content)
        self.logger.debug("Taxi {} sent proposal to passenger {}".format(self.myAgent.agent_id, passenger_id))
        self.myAgent.send(reply)

    def cancel_proposal(self, passenger_id, content=None):
        """
        Send an :class:`ACLMessage` to cancel a proposal.
        If the content is empty the proposal is sent without content.
        :param passenger_id: the id of the passenger
        :type passenger_id: :class:`str`
        :param content: the optional content of the message
        :type content: :class:`dict`
        """
        if content is None:
            content = {}
        passenger_aid = build_aid(passenger_id)
        reply = ACLMessage()
        reply.addReceiver(passenger_aid)
        reply.setProtocol(REQUEST_PROTOCOL)
        reply.setPerformative(CANCEL_PERFORMATIVE)
        reply.setContent(json.dumps(content))
        self.logger.debug("Taxi {} sent cancel proposal to passenger {}".format(self.myAgent.agent_id, passenger_id))
        self.myAgent.send(reply)

    def _process(self):
        raise NotImplementedError
