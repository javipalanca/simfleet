import time
import asyncio

from loguru import logger
from spade.agent import Agent
from collections import defaultdict
from spade.message import Message

from simfleet.utils.statistics import StatisticsStore

class SimfleetAgent(Agent):
    """
        SimfleetAgent is the base class for all agents in the SimFleet framework. It provides essential functionalities for managing
        registration, messaging, and event observation for agents that interact with the transportation fleet and customer system.

        Attributes:
            __observers (dict): A dictionary of observer callbacks to monitor changes in agent properties.
            agent_id (str): The identifier for the agent.
            strategy (function): The current strategy assigned to the agent.
            running_strategy (bool): Indicates if the strategy is currently running.
            port (int): The port used by the agent.
            stopped (bool): Indicates if the agent has stopped.
            ready (bool): Flag to check if the agent is ready to operate.
            is_launched (bool): Flag indicating if the agent has been launched.
            directory_id (str): The JID of the directory service for agent registration.
            status (str): The current status of the agent.
            fleet_type (str): The type of fleet to which the agent belongs.
            registration (bool): Indicates whether the agent is registered or not.
            init_time (float): The start time of the agent's lifecycle.
            end_time (float): The end time of the agent's lifecycle.
            events_store (StatisticsStore): A storage mechanism for agent events and statistics.
    """
    def __init__(self, agentjid, password):
        super().__init__(agentjid, password)
        self.__observers = defaultdict(list)
        self.agent_id = None
        self.agent_name = None
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

        self.init_time = None   #Change
        self.end_time = None    #Change

        self.events_store = StatisticsStore(agent_name=str(agentjid), class_type=type(self))


    async def stop(self):
        """
            Stops the agent and marks it as stopped. Overrides the default stop behavior in spade.
        """
        self.stopped = True
        await super().stop()


    def is_stopped(self):
        """
            Checks if the agent is stopped.

            Returns:
                bool: True if the agent is stopped, False otherwise.
        """
        return self.stopped


    def is_ready(self):
        """
            Checks if the agent is ready for operation.

            Returns:
                bool: True if the agent is ready, False otherwise.
        """
        return not self.is_launched or (self.is_launched and self.ready)


    async def sleep(self, seconds):
        """
            Pauses the agent’s operation for a specified duration.

            Args:
                seconds (int): The duration in seconds for which the agent should pause.
        """
        await asyncio.sleep(seconds)
        #time.sleep(seconds)


    def set(self, key, value):
        """
            Sets a value to a specific key in the agent’s properties. If an observer is registered for this key,
            the callback is triggered upon value change.

            Args:
                key (str): The property name.
                value (any): The value to be assigned.
        """
        old = self.get(key)
        super().set(key, value)
        if key in self.__observers:
            for callback in self.__observers[key]:
                callback(old, value)


    def set_registration(self, status, content=None):
        """
        Sets the registration status of the agent.

        Args:
            status (bool): True if the agent is registered, False otherwise.
            content (dict, optional): Additional information about the agent, such as its icon and fleet type.
        """
        if content is not None:
            self.icon = content["icon"] if self.icon is None else self.icon
            self.fleet_type = content["fleet_type"]
        self.registration = status


    def watch_value(self, key, callback):
        """
        Registers a callback function that is triggered when a specified key's value changes.

        Args:
            key (str): The property name to observe.
            callback (function): The callback function to trigger when the property changes. Receives the old and new value.
        """
        self.__observers[key].append(callback)


    def set_fleet_type(self, fleet_type):
        """
        Sets the type of fleet to which the agent belongs.

        Args:
            fleet_type (str): The type of fleet (e.g., "bus", "taxi").
        """
        self.fleet_type = fleet_type

    #New version send for spade 4
    async def send(self, msg: Message) -> None:
        """
            Sends a message to another agent, ensuring that the sender's JID is correctly included in the message.

            Args:
                msg (spade.message.Message): The message to be sent.
        """
        if not msg.sender:
            msg.sender = str(self.jid)
            logger.debug(f"Adding agent's jid as sender to message: {msg}")
        await self.container.send(msg, self)
        msg.sent = True
        self.traces.append(msg, category=str(self))

    def set_id(self, agent_id):
        """
        Sets the agent's identifier.

        Args:
            agent_id (str): The new identifier for the agent.
        """
        self.agent_id = agent_id


    def get_id(self):
        """
        Retrieves the agent's identifier.

        Returns:
            str: The identifier of the agent.
        """
        return self.agent_id

    def set_name(self, name):
        """
            Sets the name of the bus stop.
        """
        self.agent_name = name


    def set_directory(self, directory_id):
        """
        Sets the JID of the directory agent responsible for managing the directory of services.

        Args:
            directory_id (str): The JID of the directory agent.
        """
        self.directory_id = directory_id

    def to_json(self):
        """
        Serialises the basic information of a Simfleet agent to a JSON format.
        This function is the basis for JSON representations of specific subclasses.
        """
        return {
            "id": self.agent_id,
            "status": self.status,
        }

    def total_time(self):
        """
        Calculates the total simulation time from the agent's activation until it reaches its destination.

        Returns:
            float: The total time in seconds, or None if the times are not available.
        """
        if self.init_time and self.end_time:
            return self.end_time - self.init_time
        else:
            return None
