import json
import logging
import time

from spade.ACLMessage import ACLMessage
from spade.Agent import Agent
from spade.Behaviour import OneShotBehaviour, ACLTemplate, MessageTemplate, Behaviour

from utils import unused_port, random_position, PASSENGER_WAITING, coordinator_aid, REQUEST_PROTOCOL, \
    REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, PASSENGER_IN_DEST, TAXI_MOVING_TO_PASSENGER, PASSENGER_IN_TAXI, \
    TAXI_IN_PASSENGER_PLACE, TRAVEL_PROTOCOL, PASSENGER_LOCATION

logger = logging.getLogger("PassengerAgent")


class PassengerAgent(Agent):
    def __init__(self, agentjid, password, debug):
        Agent.__init__(self, agentjid, password, debug=debug)
        self.agent_id = None
        self.status = PASSENGER_WAITING
        self.current_pos = None
        self.dest = None
        self.port = None
        self.init_time = None

    def _setup(self):
        self.port = unused_port("127.0.0.1")
        self.wui.setPort(self.port)
        self.wui.start()
        self.wui.registerController("update_position", self.update_position_controller)

        tpl = ACLTemplate()
        tpl.setProtocol(REQUEST_PROTOCOL)
        template = MessageTemplate(tpl)
        self.addBehaviour(AcceptFirstRequestTaxiBehaviour(), template)

        tpl = ACLTemplate()
        tpl.setProtocol(TRAVEL_PROTOCOL)
        template = MessageTemplate(tpl)
        self.addBehaviour(TravelBehaviour(), template)

        self.init_time = None
        self.end_time = None
        self.pick_up_time = None

    def update_position_controller(self, lat, lon):
        coords = [float(lat), float(lon)]
        self.set_position(coords)

        return None, {}

    def set_id(self, agent_id):
        self.agent_id = agent_id

    def set_position(self, coords=None):
        if coords:
            self.current_pos = coords
        else:
            self.current_pos = random_position()
        logger.info("Passenger {} position is {}".format(self.agent_id, self.current_pos))

    def get_position(self):
        return self.current_pos

    def total_time(self):
        if self.init_time and self.end_time:
            return self.end_time - self.init_time
        else:
            return 0

    def to_json(self):
        return {
            "id": self.agent_id,
            "position": self.current_pos,
            "dest": self.dest,
            "status": self.status,
            "url": "http://127.0.0.1:{port}".format(port=self.port)
        }


class TravelBehaviour(Behaviour):
    def _process(self):
        msg = self._receive(block=True)
        content = json.loads(msg.getContent())
        if "status" in content:
            status = content["status"]
            if status == TAXI_MOVING_TO_PASSENGER:
                self.myAgent.status = PASSENGER_WAITING
                self.myAgent.waiting_time = time.time() - self.myAgent.init_time
            elif status == TAXI_IN_PASSENGER_PLACE:
                self.myAgent.status = PASSENGER_IN_TAXI
                logger.info("Passenger {} in taxi.".format(self.myAgent.agent_id))
                self.myAgent.pick_up_time = time.time() - self.myAgent.waiting_time
            elif status == PASSENGER_IN_DEST:
                self.myAgent.status = PASSENGER_IN_DEST
                self.myAgent.end_time = time.time()
                logger.info("Passenger {} arrived to destiny after {} seconds.".format(self.myAgent.agent_id,
                                                                                       self.myAgent.total_time()))
            elif status == PASSENGER_LOCATION:
                coords = content["location"]
                self.myAgent.set_position(coords)


class PassengerStrategyBehaviour(OneShotBehaviour):
    def onStart(self):
        self.myAgent.init_time = time.time()

    def timeout_receive(self, timeout=5):
        init_time = time.time()
        while (time.time() - init_time) < timeout:
            msg = self._receive(block=False)
            if msg is not None:
                return msg
            time.sleep(0.1)
        return None

    def send_request(self):
        if not self.myAgent.dest:
            self.myAgent.dest = random_position()
        msg = ACLMessage()
        msg.addReceiver(coordinator_aid)
        msg.setProtocol(REQUEST_PROTOCOL)
        msg.setPerformative(REQUEST_PERFORMATIVE)
        content = {
            "passenger_id": self.myAgent.agent_id,
            "origin": self.myAgent.current_pos,
            "dest": self.myAgent.dest
        }
        msg.setContent(json.dumps(content))
        self.myAgent.send(msg)
        logger.info("Passenger {} asked for a taxi to {}.".format(self.myAgent.agent_id, self.myAgent.dest))

    def accept_taxi(self, taxi_aid):
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
        logger.info("Passenger {} accepted proposal from taxi {}".format(self.myAgent.agent_id, taxi_aid.getName()))

    def _process(self):
        raise NotImplementedError


class AcceptFirstRequestTaxiBehaviour(PassengerStrategyBehaviour):
    def _process(self):
        msg = None
        while msg is None:
            self.send_request()
            msg = self.timeout_receive(timeout=5)

        taxi_aid = msg.getSender()
        logger.info("Passenger {} received proposal from {}".format(self.myAgent.agent_id, taxi_aid.getName()))
        self.accept_taxi(taxi_aid)
