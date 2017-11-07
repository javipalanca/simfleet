import json
import logging

import requests
from spade.Agent import Agent

from utils import TAXI_WAITING, random_position, unused_port

logger = logging.getLogger("TaxiAgent")


class TaxiAgent(Agent):

    def __init__(self, agentjid, password, debug):
        Agent.__init__(self, agentjid, password, debug=debug)
        self.taxi_id = None
        self.status = TAXI_WAITING
        self.current_pos = None
        self.dest = None
        self.path = None
        self.distance = 0
        self.duration = 0
        self.port = None

    def _setup(self):
        self.port = unused_port("127.0.0.1")
        self.wui.setPort(self.port)
        self.wui.start()

        self.wui.registerController("update_position", self.update_position_controller)

    def update_position_controller(self, lat, lon):
        self.current_pos = [float(lat), float(lon)]
        logger.info("Agent {} updated position to {}".format(self.taxi_id, self.current_pos))
        return None, {}

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
            "status": self.status,
            "path": self.path,
            "url": "http://127.0.0.1:{port}".format(port=self.port)
        }

    def move_to(self, dest):
        path, distance, duration = self.request_path(dest)
        self.path = path
        self.dest = dest
        self.distance += distance
        self.duration += duration

    def request_path(self, dest):
        logger.info("Requesting path from {} to {}".format(self.current_pos, dest))
        url = "http://gtirouter.dsic.upv.es:43008/route/v1/car/{src1},{src2};{dest1},{dest2}?geometries=geojson&overview=full"
        src1, src2, dest1, dest2 = self.current_pos[1], self.current_pos[0], dest[1], dest[0]
        url = url.format(src1=src1, src2=src2, dest1=dest1, dest2=dest2)
        result = requests.get(url)
        result = json.loads(result.content)
        path = result["routes"][0]["geometry"]["coordinates"]
        path = [[point[1], point[0]] for point in path]
        duration = result["routes"][0]["duration"]
        distance = result["routes"][0]["distance"]

        return path, distance, duration
