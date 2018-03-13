import json
import logging

import requests
from collections import defaultdict
from requests.adapters import HTTPAdapter
from spade.Agent import Agent
from spade.Behaviour import Behaviour, ACLTemplate, MessageTemplate
from urllib3 import Retry

from helpers import content_to_json

logger = logging.getLogger("RouteAgent")


class RouteAgent(Agent):
    """
    The RouteAgent receives request for paths, queries an OSRM server and returns the information.
    It also caches the queries to avoid overloading the OSRM server.
    """

    def __init__(self, agentjid, password, debug):
        Agent.__init__(self, agentjid, password, debug=debug)

        self.route_cache = defaultdict(dict)

    def _setup(self):
        template = ACLTemplate()
        template.setPerformative("route")
        t = MessageTemplate(template)
        self.addBehaviour(self.RequestRouteBehaviour(), t)
        logger.info("Route agent running")

    def get_route(self, origin, destination):
        """
        Checks the cache for a path, if not found then it queries the OSRM server.

        Args:
            origin (list): origin coordinate (longitude, latitude)
            destination (list): target coordinate (longitude, latitude)

        Returns:
            dict: a dict with three keys: path, distance and duration
        """
        key = ",".join([str(origin), str(destination)])
        try:
            item = self.route_cache[key]
            logger.debug("Got route from cache")
        except KeyError:
            logger.debug("Requesting new route from server ({},{}).".format(origin, destination))
            path, distance, duration = self.request_route_to_server(origin, destination)
            item = {"path": path, "distance": distance, "duration": duration}
            if path is not None:
                self.route_cache[key] = item

        return item

    def persist_cache(self):
        """
        Persists the cache to a JSON file.
        """
        with open("route_cache.json", 'w') as f:
            try:
                json.dump(self.route_cache, f)
                logger.debug("Cache persisted.")
            except:
                logger.warn("Could not persist cache.")

    def load_cache(self):
        """
        Loads the cache from file.
        """
        try:
            with open("route_cache.json", 'r') as f:
                self.route_cache = json.load(f)
            logger.debug("Cache loaded.")
        except:
            logger.warn("Could not load cache file.")
            self.route_cache = {}

    @staticmethod
    def request_route_to_server(origin, destination):
        """
        Queries the OSRM for a path.

        Args:
            origin (list): origin coordinate (longitude, latitude)
            destination (list): target coordinate (longitude, latitude)

        Returns:
            list, float, float = the path, the distance of the path and the estimated duration
        """
        try:
            url = "http://osrm.gti-ia.upv.es/route/v1/car/{src1},{src2};{dest1},{dest2}?geometries=geojson&overview=full"
            src1, src2, dest1, dest2 = origin[1], origin[0], destination[1], destination[0]
            url = url.format(src1=src1, src2=src2, dest1=dest1, dest2=dest2)

            session = requests.Session()
            retry = Retry(connect=3, backoff_factor=1.0)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount(url, adapter)
            result = session.get(url)
            result = json.loads(result.content)

            path = result["routes"][0]["geometry"]["coordinates"]
            path = [[point[1], point[0]] for point in path]
            duration = result["routes"][0]["duration"]
            distance = result["routes"][0]["distance"]
            if path[-1] != destination:
                path.append(destination)
            return path, distance, duration
        except Exception:
            return None, None, None

    class RequestRouteBehaviour(Behaviour):
        """
        This cyclic behaviour listens for route requests from other agents.
        When a message is received it answers with the path.
        """

        def onStart(self):
            self.myAgent.load_cache()

        def onEnd(self):
            self.myAgent.persist_cache()

        def _process(self):
            logger.debug("Wait for new route request message.")
            msg = self._receive(block=True)
            logger.debug("Got route request message. {}".format(msg.getContent()))

            try:
                content = content_to_json(msg)
                reply_content = self.myAgent.get_route(content["origin"], content["destination"])
                reply_content["type"] = "success"
            except Exception as e:
                logger.error("Error requesting route: {}".format(e))
                reply_content = {"type": "error", "body": str(e)}

            if reply_content["path"] is None:
                logger.error("Could not retrieve route.")
                reply_content = {"type": "error", "body": "Could not retrieve route."}

            reply = msg.createReply()
            reply.setContent(json.dumps(reply_content))

            self.myAgent.send(reply)
