import logging
import time

from spade.Agent import Agent

from utils import unused_port, random_position, PASSENGER_WAITING

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

        self.init_time = time.time()

    def update_position_controller(self, lat, lon):
        self.current_pos = [float(lat), float(lon)]
        logger.info("Agent {} updated position to {}".format(self.agent_id, self.current_pos))
        return None, {}

    def set_id(self, agent_id):
        self.agent_id = agent_id

    def set_position(self, coords=None):
        if coords:
            self.current_pos = coords
        else:
            self.current_pos = random_position()

    def to_json(self):
        return {
            "id": self.agent_id,
            "position": self.current_pos,
            "dest": self.dest,
            "status": self.status,
            "url": "http://127.0.0.1:{port}".format(port=self.port)
        }
