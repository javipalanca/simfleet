import asyncio
import json
import os
import sys
import time
import logging
import socket
import uuid
from importlib import import_module
from abc import ABCMeta

from spade.message import Message
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.template import Template

from .helpers import distance_in_meters, kmh_to_ms

logger = logging.getLogger()

TAXI_WAITING = "TAXI_WAITING"
TAXI_MOVING_TO_PASSENGER = "TAXI_MOVING_TO_PASSENGER"
TAXI_IN_PASSENGER_PLACE = "TAXI_IN_PASSENGER_PLACE"
TAXI_MOVING_TO_DESTINATION = "TAXI_MOVING_TO_DESTINATION"
TAXI_WAITING_FOR_APPROVAL = "TAXI_WAITING_FOR_APPROVAL"

PASSENGER_WAITING = "PASSENGER_WAITING"
PASSENGER_IN_TAXI = "PASSENGER_IN_TAXI"
PASSENGER_IN_DEST = "PASSENGER_IN_DEST"
PASSENGER_LOCATION = "PASSENGER_LOCATION"
PASSENGER_ASSIGNED = "PASSENGER_ASSIGNED"


def status_to_str(status_code):
    """
    Translates an int status code to a string that represents the status

    Args:
        status_code (int): the code of the status

    Returns:
        str: the string that represents the status
    """
    statuses = {
        10: "TAXI_WAITING",
        11: "TAXI_MOVING_TO_PASSENGER",
        12: "TAXI_IN_PASSENGER_PLACE",
        13: "TAXI_MOVING_TO_DESTINATION",
        14: "TAXI_WAITING_FOR_APPROVAL",
        20: "PASSENGER_WAITING",
        21: "PASSENGER_IN_TAXI",
        22: "PASSENGER_IN_DESTINATION",
        23: "PASSENGER_LOCATION",
        24: "PASSENGER_ASSIGNED"
    }
    if status_code in statuses:
        return statuses[status_code]
    return status_code


class StrategyBehaviour(CyclicBehaviour, metaclass=ABCMeta):
    """
    The behaviour that all parent strategies must inherit from. It complies with the Strategy Pattern.
    """
    pass


class RequestRouteBehaviour(OneShotBehaviour):
    """
    A one-shot behaviour that is executed to request for a new route to the route agent.
    """

    def __init__(self, msg: Message, origin: list, destination: list, route_agent: str):
        """
        Behaviour to request a route to a route agent
        Args:
            msg (Message): the message to be sent
            origin (list): origin of the route
            destination (list): destination of the route
            route_agent (str): name of the route agent
        """
        self.origin = origin
        self.destination = destination
        self._msg = msg
        self.route_agent = route_agent
        self.result = {"path": None, "distance": None, "duration": None}
        super().__init__()

    async def run(self):
        try:
            self._msg.to = self.route_agent
            self._msg.set_metadata("performative", "route")
            content = {"origin": self.origin, "destination": self.destination}
            self._msg.body = json.dumps(content)
            await self.send(self._msg)
            logger.debug("RequestRouteBehaviour sent message: {}".format(self._msg))
            msg = await self.receive(20)
            logger.debug("RequestRouteBehaviour received message: {}".format(msg))
            if msg is None:
                logger.warning("There was an error requesting the route (timeout)")
                self.exit_code = {"type": "error"}
                return

            self.kill(json.loads(msg.body))

        except Exception as e:
            logger.error("Exception requesting route: " + str(e))


async def request_path(agent, origin, destination, route_id):
    """
    Sends a message to the RouteAgent to request a path

    Args:
        agent: the agent who is requesting the path
        origin (list): a list with the origin coordinates [longitude, latitude]
        destination (list): a list with the target coordinates [longitude, latitude]

    Returns:
        list, float, float: a list of points (longitude and latitude) representing the path,
                            the distance of the path in meters, a estimation of the duration of the path

    Examples:
        >>> path, distance, duration = request_path(an_agent, origin=[0,0], destination=[1,1])
        >>> print(path)
        [[0,0], [0,1], [1,1]]
        >>> print(distance)
        2.0
        >>> print(duration)
        3.24
    """
    if origin[0] == destination[0] and origin[1] == destination[1]:
        return [[origin[1], origin[0]]], 0, 0

    msg = Message()
    msg.thread = str(uuid.uuid4()).replace("-", "")
    template = Template()
    template.thread = msg.thread
    behav = RequestRouteBehaviour(msg, origin, destination, route_id)
    agent.add_behaviour(behav, template)

    while not behav.is_killed():
        await asyncio.sleep(0.01)

    if behav.exit_code is {} or "type" in behav.exit_code and behav.exit_code["type"] == "error":
        return None, None, None
    else:
        return behav.exit_code["path"], behav.exit_code["distance"], behav.exit_code["duration"]


def unused_port(hostname):
    """Return a port that is unused on the current host."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((hostname, 0))
    port = s.getsockname()[1]
    s.close()
    return port


def chunk_path(path, speed_in_kmh):
    """
    Splits the path into smaller chunks taking into account the speed.

    Args:
        path (list): the original path. A list of points (lon, lat)
        speed_in_kmh (float): the speed in km per hour at which the path is being traveled.

    Returns:
        list: a new path equivalent (to the first one), that has at least the same number of points.
    """
    meters_per_second = kmh_to_ms(speed_in_kmh)
    length = len(path)
    chunked_lat_lngs = []

    for i in range(1, length):
        _cur = path[i - 1]
        _next = path[i]
        if _cur == _next:
            continue
        distance = distance_in_meters(_cur, _next)
        factor = meters_per_second / distance if distance else 0
        diff_lat = factor * (_next[0] - _cur[0])
        diff_lng = factor * (_next[1] - _cur[1])

        if distance > meters_per_second:
            while distance > meters_per_second:
                _cur = [_cur[0] + diff_lat, _cur[1] + diff_lng]
                distance = distance_in_meters(_cur, _next)
                chunked_lat_lngs.append(_cur)
        else:
            chunked_lat_lngs.append(_cur)

    chunked_lat_lngs.append(path[length - 1])

    return chunked_lat_lngs


def load_class(class_path):
    """
    Tricky method that imports a class form a string.

    Args:
        class_path (str): the path where the class to be imported is.

    Returns:
        class: the class imported and ready to be instantiated.
    """
    sys.path.append(os.getcwd())
    module_path, class_name = class_path.rsplit(".", 1)
    mod = import_module(module_path)
    return getattr(mod, class_name)


def avg(array):
    """
    Makes the average of an array without Nones.
    Args:
        array (list): a list of floats and Nones

    Returns:
        float: the average of the list without the Nones.
    """
    array_wo_nones = list(filter(None, array))
    return (sum(array_wo_nones, 0.0) / len(array_wo_nones)) if len(array_wo_nones) > 0 else 0.0
