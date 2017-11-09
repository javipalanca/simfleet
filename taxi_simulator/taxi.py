import json
import logging

from spade.ACLMessage import ACLMessage
from spade.Agent import Agent
from spade.Behaviour import Behaviour, ACLTemplate, MessageTemplate

from utils import TAXI_WAITING, random_position, unused_port, request_path, PROPOSE_PERFORMATIVE, INFORM_PERFORMATIVE, \
    TAXI_MOVING_TO_PASSENGER, TAXI_IN_PASSENGER_PLACE, TAXI_MOVING_TO_DESTINY, \
    PASSENGER_IN_DEST, REQUEST_PROTOCOL, TRAVEL_PROTOCOL, PASSENGER_LOCATION, build_aid

logger = logging.getLogger("TaxiAgent")


class TaxiAgent(Agent):
    def __init__(self, agentjid, password, debug):
        Agent.__init__(self, agentjid, password, debug=debug)
        self.agent_id = None
        self.status = TAXI_WAITING
        self.current_pos = None
        self.dest = None
        self.path = None
        self.distance = 0
        self.duration = 0
        self.port = None
        self.current_passenger = None
        self.current_passenger_orig = None
        self.current_passenger_dest = None

    def _setup(self):
        self.port = unused_port("127.0.0.1")
        self.wui.setPort(self.port)
        self.wui.start()

        self.wui.registerController("update_position", self.update_position_controller)
        self.wui.registerController("arrived", self.arrived_to_dest_controller)

    def add_strategy(self, strategyClass):
        tpl = ACLTemplate()
        tpl.setProtocol(REQUEST_PROTOCOL)
        template = MessageTemplate(tpl)
        self.addBehaviour(strategyClass(), template)

    def update_position_controller(self, lat, lon):
        coords = [float(lat), float(lon)]
        self.set_position(coords)
        return None, {}

    def arrived_to_dest_controller(self):
        if self.status == TAXI_MOVING_TO_PASSENGER:
            self.inform_passenger(TAXI_IN_PASSENGER_PLACE)
            self.status = TAXI_MOVING_TO_DESTINY
            self.move_to(self.current_passenger_dest)
            logger.info("Taxi {} has picked up the passenger {}.".format(self.agent_id, self.current_passenger.getName()))
        elif self.status == TAXI_MOVING_TO_DESTINY:
            self.inform_passenger(PASSENGER_IN_DEST)
            self.status = TAXI_WAITING
            logger.info("Taxi {} has taken the passenger {} to his destination.".format(self.agent_id,
                                                                                        self.current_passenger.getName()))
            self.current_passenger = None

        return None, {}

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

    def get_position(self):
        return self.current_pos

    def move_to(self, dest):
        logger.debug("Requesting path from {} to {}".format(self.current_pos, dest))
        path, distance, duration = request_path(self.current_pos, dest)
        self.path = path
        self.dest = dest
        self.distance += distance
        self.duration += duration

    def inform_passenger(self, status, data=None):
        if data is None:
            data = {}
        msg = ACLMessage()
        msg.addReceiver(self.current_passenger)
        msg.setProtocol(TRAVEL_PROTOCOL)
        msg.setPerformative(INFORM_PERFORMATIVE)
        content = {
            "status": status
        }
        for k, v in data.items():
            content[k] = v
        msg.setContent(json.dumps(content))
        self.send(msg)

    def to_json(self):
        return {
            "id": self.agent_id,
            "position": self.current_pos,
            "dest": self.dest,
            "status": self.status,
            "path": self.path,
            "url": "http://127.0.0.1:{port}".format(port=self.port)
        }


class TaxiStrategyBehaviour(Behaviour):
    def onStart(self):
        self.logger = logging.getLogger("TaxiAgent")
        self.logger.debug("Strategy {} started in taxi {}".format(type(self).__name__, self.myAgent.agent_id))

    def pick_up_passenger(self, passenger_id, origin, dest):
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
        self.myAgent.status = TAXI_MOVING_TO_PASSENGER
        self.myAgent.current_passenger = passenger_aid
        self.myAgent.current_passenger_orig = origin
        self.myAgent.current_passenger_dest = dest
        self.myAgent.move_to(self.myAgent.current_passenger_orig)
        self.myAgent.send(reply)

    def send_proposal(self, passenger_id, content=None):
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

    def _process(self):
        raise NotImplementedError
