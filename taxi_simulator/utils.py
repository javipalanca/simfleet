import json
import os
import sys
import time
import logging
import socket
import uuid
from importlib import import_module
from abc import ABCMeta

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

from spade.ACLMessage import ACLMessage
from spade.Behaviour import Behaviour, OneShotBehaviour, ACLTemplate, MessageTemplate

from helpers import distance_in_meters, kmh_to_ms, build_aid, content_to_json

logger = logging.getLogger()

TAXI_WAITING = 10
TAXI_MOVING_TO_PASSENGER = 11
TAXI_IN_PASSENGER_PLACE = 12
TAXI_MOVING_TO_DESTINATION = 13
TAXI_WAITING_FOR_APPROVAL = 14

PASSENGER_WAITING = 20
PASSENGER_IN_TAXI = 21
PASSENGER_IN_DEST = 22
PASSENGER_LOCATION = 23
PASSENGER_ASSIGNED = 24


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
    return statuses[status_code]


def timeout_receive(agent, timeout):
    """
    makes an agent to wait for a message until a timeout

    Args:
        agent: the agent who is receiving the message
        timeout (int): the number of seconds to wait for the message

    Returns:
        :obj:`spade.ACLMessage.ACLMessage`: a received message or :data:`None`
    """
    init_time = time.time()
    msg = agent._receive(block=False)
    if msg is not None:
        return msg
    if timeout:
        while (time.time() - init_time) < timeout:
            msg = agent._receive(block=False)
            if msg is not None:
                return msg
            time.sleep(0.1)
    return None


class StrategyBehaviour(Behaviour):
    """
    The behaviour that all parent strategies must inherit from. It complies with the Strategy Pattern.
    """
    __metaclass__ = ABCMeta

    def store_value(self, key, value):
        """
        Stores a value (named by a key) in the agent's knowledge base that runs the behaviour.
        This allows the strategy to have persistent values between loops.

        Args:
            key (str): the name of the value
            value (object): The object to be stored
        """
        self.myAgent.store_value(key, value)

    def get_value(self, key):
        """
        Returns a stored value from the agent's knowledge base.

        Args:
            key (str): the name of the value

        Returns:
             object: the object stored with key

        Raises:
             KeyError: if the key is not in the knowledge base
        """
        return self.myAgent.get_value(key)

    def has_value(self, key):
        """
        Checks if a key is registered in the agent's knowledge base

        Args:
            key (str): the name of the value to be checked

        Returns:
             bool: if the key is in the agent's knowledge base
        """
        return self.myAgent.has_value(key)

    def timeout_receive(self, timeout=5):

        return self.receive(timeout)

    def receive(self, timeout=5):
        """
        Waits for a message until timeout is done.
        If a message is received the method returns immediately.
        If the time has passed and no message has been received, it returns None.

        Args:
            timeout (int optional): number of seconds to wait for a message

        Returns:
            :class:`spade.ACLMessage.ACLMessage` or :data:`None`: a message or None
        """
        return timeout_receive(self, timeout)

    def send(self, message):
        """
        Sends an :class:`spade.ACLMessage.ACLMessage`

        Args:
            message (:class:`spade.ACLMessage.ACLMessage`): the message to be sent
        """
        self.myAgent.send(message)


class RequestRouteBehaviour(OneShotBehaviour):
    """
    A one-shot behaviour that is executed to request for a new route to the route agent.
    """
    def __init__(self, msg, origin, destination):
        self.origin = origin
        self.destination = destination
        self._msg = msg
        self.result = {"path": None, "distance": None, "duration": None}
        OneShotBehaviour.__init__(self)

    def _process(self):
        try:
            self._msg.addReceiver(build_aid("route"))
            self._msg.setPerformative("route")

            content = {"origin": self.origin, "destination": self.destination}
            self._msg.setContent(json.dumps(content))

            self.myAgent.send(self._msg)
            logger.debug("RequestRouteBehaviour sent message.")
            msg = timeout_receive(self, 20)
            logger.debug("RequestRouteBehaviour received message: {}".format(msg))
            if msg is None:
                logger.warn("There was an error requesting the route (timeout)")
                self.result = {"type": "error"}
                return

            self.result = content_to_json(msg)

        except Exception, e:
            logger.error("Exception requesting route: " + str(e))


def request_path(agent, origin, destination):
    """
    Sends a message to the RouteAgent to request a path

    Args:
        agent: the agent who is requesting the path
        origin (list): a list with the origin coordinates [longitude, latitude]
        destination (list): a list with the target coordinates [longitude, latitude]

    Returns:
        list, float, float: a list of points (longitude and latitude) representing the path, the distance of the path in meters, a estimation of the duration of the path

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

    msg = ACLMessage()
    template = ACLTemplate()
    template.setConversationId(msg.getConversationId())
    r = str(uuid.uuid4()).replace("-", "")
    msg.setReplyWith(r)
    template.setInReplyTo(r)
    t = MessageTemplate(template)
    b = RequestRouteBehaviour(msg, origin, destination)
    agent.addBehaviour(b, t)
    b.join()

    if b.result is {} or "type" in b.result and b.result["type"] == "error":
        return None, None, None
    else:
        return b.result["path"], b.result["distance"], b.result["duration"]


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


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    """
    Decorator to allow the cross-domain situation in web requests.
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)

    return decorator
