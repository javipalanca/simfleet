import logging

from spade.Agent import Agent

from utils import TAXI_WAITING, random_position

logger = logging.getLogger("TaxiAgent")


class TaxiAgent(Agent):
    def _setup(self):
        self.status = TAXI_WAITING
        self.dest = None

    def set_id(self, taxi_id):
        self.taxi_id = taxi_id

    def set_position(self, coords=None):
        if coords:
            self.current_pos = coords
        else:
            self.current_pos = random_position()

    def to_json(self):
        return {
            "id": self.taxi_id,
            "position": self.current_pos,
            "dest": self.dest,
            "status": self.status
        }
