import random
import json
from spade.Agent import Agent

from taxi_simulator.structs import TAXI_WAITING


def random_position():
    with open("taxi_simulator/templates/data/taxi_stations.json") as f:
        stations = json.load(f)["features"]
        pos = random.choice(stations)
        return pos["geometry"]["coordinates"]


class TaxiAgent(Agent):
    def _setup(self):
        self.current_pos = None
        self.status = TAXI_WAITING
        self.dest = None

    def set_position(self, coords=None):
        if coords:
            self.current_pos = coords
        else:
            self.current_pos = random_position()
