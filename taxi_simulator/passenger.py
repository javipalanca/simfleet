import json
import logging
import time

from spade.ACLMessage import ACLMessage
from spade.Agent import Agent
from spade.Behaviour import ACLTemplate, MessageTemplate, Behaviour

from utils import unused_port, random_position, PASSENGER_WAITING, coordinator_aid, REQUEST_PROTOCOL, \
    REQUEST_PERFORMATIVE, ACCEPT_PERFORMATIVE, PASSENGER_IN_DEST, TAXI_MOVING_TO_PASSENGER, PASSENGER_IN_TAXI, \
    TAXI_IN_PASSENGER_PLACE, TRAVEL_PROTOCOL, PASSENGER_LOCATION, REFUSE_PERFORMATIVE, PASSENGER_ASSIGNED

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
        self.waiting_time = None
        self.pick_up_time = None
        self.end_time = None

    def _setup(self):
        self.port = unused_port("127.0.0.1")
        self.wui.setPort(self.port)
        self.wui.start()
        self.wui.registerController("update_position", self.update_position_controller)

        tpl = ACLTemplate()
        tpl.setProtocol(TRAVEL_PROTOCOL)
        template = MessageTemplate(tpl)
        self.addBehaviour(TravelBehaviour(), template)

    def add_strategy(self, strategyClass):
        tpl = ACLTemplate()
        tpl.setProtocol(REQUEST_PROTOCOL)
        template = MessageTemplate(tpl)
        self.addBehaviour(strategyClass(), template)

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
        logger.debug("Passenger {} position is {}".format(self.agent_id, self.current_pos))

    def get_position(self):
        return self.current_pos

    def total_time(self):
        if self.init_time and self.end_time:
            return self.end_time - self.init_time
        else:
            return 0

    def get_waiting_time(self):
        if self.init_time:
            if self.pick_up_time:
                t = self.pick_up_time - self.init_time
            else:
                t = time.time() - self.init_time
            return t
        return None

    def get_pick_up_time(self):
        if self.pick_up_time:
            return self.pick_up_time - self.waiting_time
        return None

    def to_json(self):
        t = self.get_waiting_time()
        return {
            "id": self.agent_id,
            "position": self.current_pos,
            "dest": self.dest,
            "status": self.status,
            "taxi": self.taxi_assigned,
            "url": "http://127.0.0.1:{port}".format(port=self.port),
            "waiting": float("{0:.2f}".format(t)) if t else None
        }


class TravelBehaviour(Behaviour):
    def _process(self):
        msg = self._receive(block=True)
        content = json.loads(msg.getContent())
        if "status" in content:
            status = content["status"]
            if status == TAXI_MOVING_TO_PASSENGER:
                self.myAgent.status = PASSENGER_ASSIGNED
                self.myAgent.waiting_time = time.time()
            elif status == TAXI_IN_PASSENGER_PLACE:
                self.myAgent.status = PASSENGER_IN_TAXI
                logger.info("Passenger {} in taxi.".format(self.myAgent.agent_id))
                self.myAgent.pick_up_time = time.time()
            elif status == PASSENGER_IN_DEST:
                self.myAgent.status = PASSENGER_IN_DEST
                self.myAgent.end_time = time.time()
                logger.info("Passenger {} arrived to destiny after {} seconds.".format(self.myAgent.agent_id,
                                                                                       self.myAgent.total_time()))
            elif status == PASSENGER_LOCATION:
                coords = content["location"]
                self.myAgent.set_position(coords)


class PassengerStrategyBehaviour(Behaviour):
    def onStart(self):
        self.logger = logging.getLogger("PassengerAgent")
        self.logger.debug("Strategy {} started in passenger {}".format(type(self).__name__, self.myAgent.agent_id))
        self.myAgent.init_time = time.time()

    def timeout_receive(self, timeout=5):
        init_time = time.time()
        while (time.time() - init_time) < timeout:
            msg = self._receive(block=False)
            if msg is not None:
                return msg
            time.sleep(0.1)
        return None

    def send_request(self, content=None):
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
        self.logger.debug("Passenger {} accepted proposal from taxi {}".format(self.myAgent.agent_id,
                                                                               taxi_aid.getName()))
        self.myAgent.status = PASSENGER_ASSIGNED

    def refuse_taxi(self, taxi_aid):
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
        self.logger.debug("Passenger {} refused proposal from taxi {}".format(self.myAgent.agent_id,
                                                                              taxi_aid.getName()))

    def _process(self):
        raise NotImplementedError
