#import json    #Not used
import time
from asyncio import Future
#import asyncio     #Not used
#from asyncio import CancelledError     #Not used
from collections import defaultdict
from typing import Union, Coroutine

from loguru import logger

from spade.agent import Agent

#from simfleet.utils.helpers import random_position     #Not used

from simfleet.utils.statistics import StatisticsStore

class SimfleetAgent(Agent):
    def __init__(self, agentjid, password):
        super().__init__(agentjid, password)
        self.__observers = defaultdict(list)
        self.agent_id = None
        self.strategy = None
        self.running_strategy = False
        self.port = None
        self.stopped = False #True
        self.ready = False
        self.is_launched = False
        self.directory_id = None
        self.status = None
        self.fleet_type = None
        self.registration = None

        self.init_time = None
        self.end_time = None

        # New statistics
        self.events_store = StatisticsStore(agent_name=str(agentjid))

    async def stop(self):
        self.stopped = True
        await super().stop()

    #New function - Know if the agent is stopped
    def is_stopped(self):
        return self.stopped

    #Used TransportAgent - CustomerAgent - StationAgent (different) -- ANALIZAR REUNION
    def is_ready(self):
        return not self.is_launched or (self.is_launched and self.ready)

    #Used TransportAgent
    def sleep(self, seconds):
        # await asyncio.sleep(seconds)
        time.sleep(seconds)

    #Used TransportAgent
    def set(self, key, value):
        old = self.get(key)
        super().set(key, value)
        if key in self.__observers:
            for callback in self.__observers[key]:
                callback(old, value)

    #Used TransportAgent - StationAgent (different) - FleetMaganerAgent (different)
    def set_registration(self, status, content=None):
        """
        Sets the status of registration
        Args:
            status (boolean): True if the transport agent has registered or False if not
            content (dict):
        """
        if content is not None:
            self.icon = content["icon"] if self.icon is None else self.icon
            self.fleet_type = content["fleet_type"]
        self.registration = status

    #Used TransportAgent (transport.py)
    def watch_value(self, key, callback):
        """
        Registers an observer callback to be run when a value is changed

        Args:
            key (str): the name of the value
            callback (function): a function to be called when the value changes. It receives two arguments: the old and the new value.
        """
        self.__observers[key].append(callback)

    #Used TransportAgent - CustomerAgent - FleetManagerAgent
    def set_fleet_type(self, fleet_type):
        """
        Sets the type of fleet to be used.

        Args:
            fleet_type (str): the type of the fleet to be used
        """
        self.fleet_type = fleet_type

    #Used TransportAgent - StationAgent
    async def send(self, msg):
        if not msg.sender:
            msg.sender = str(self.jid)
            logger.debug(f"Adding agent's jid as sender to message: {msg}")
        aioxmpp_msg = msg.prepare()
        await self.client.send(aioxmpp_msg)
        msg.sent = True
        self.traces.append(msg, category=str(self))

    #Used TransportAgent - CustomerAgent - StationAgent - FleetManagerAgent
    def set_id(self, agent_id):
        """
        Sets the agent identifier
        Args:
            agent_id (str): The new Agent Id
        """
        self.agent_id = agent_id

    # Used TransportAgent - CustomerAgent - StationAgent - FleetManagerAgent        #NEW
    def get_id(self):
        """
        Gets the agent identifier

        """
        return self.agent_id

    #Used TransportAgent - CustomerAgent - StationAgent - FleetManagerAgent
    def set_directory(self, directory_id):
        """
        Sets the directory JID address
        Args:
            directory_id (str): the DirectoryAgent jid

        """
        self.directory_id = directory_id

    #Used CustomerAgent
    def total_time(self):
        """
        Returns the time since the customer was activated until it reached its destination.

        Returns:
            float: the total time of the customer's simulation.
        """
        if self.init_time and self.end_time:
            return self.end_time - self.init_time
        else:
            return None

    #def to_json(self):
    #    """
    #    Returns a JSON with the relevant data of this type of agent
    #    """
    #    data = {}
    #    data.update({
    #        "id": self.agent_id,
    #        "status": self.status,
    #        "init_time": self.init_time,
    #        "end_time": self.end_time
    #    })
    #    return data
