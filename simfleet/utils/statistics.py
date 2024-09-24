import datetime
import itertools
from typing import Optional, List, Dict


class Event:
    """
    A class to represent a specific event in the system.
    Each event is linked to KPIs and the agents involved in that event.
    """

    def __init__(self, event_type: str, agent_name: str, data: Optional[Dict] = None):
        self.timestamp = datetime.datetime.now()
        self.event_type = event_type
        self.agent_name = agent_name
        self.data = data if data else {}  # Additional data related to the event (like distances, times, etc.)

    # Alternative - Erase
    def to_dict(self) -> Dict:
        """
        Convert the event to a dictionary in the required format.
        """
        return {
            "name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "event": self.event_type,
            "details": self.data
        }


class StatisticsStore:
    """Stores and allows queries about KPI-related events for a single agent."""

    # def __init__(self, size: int, agent_name: str):
    def __init__(self, agent_name: str):
        # self.size = size
        self.store = []
        self.agent_name = agent_name

    def get_agent_name(self) -> str:
        """
        Returns the name of the agent.
        """
        return self.agent_name

    def reset(self) -> None:
        """Resets the statistics store"""
        self.store = []

    def emit(self, event_type: str, data: Optional[Dict] = None) -> None:
        """
        Adds a new event to the statistics store.

        Args:
          event_type (str): the type of the event (e.g., "Customer Request", "Charging Start")
          data (dict, optional): additional data related to the event (e.g., distances, times) (Default value = None)
        """
        event = Event(event_type, self.agent_name, data)
        self.store.insert(0, event)
        # if len(self.store) > self.size:   #QUITAR EL LIMITE
        #    del self.store[-1]

    def all(self, limit: Optional[int] = None) -> List[Event]:
        """
        Returns all the events, until a limit if defined.

        Args:
          limit (int, optional): the max number of events to return (Default value = None)

        Returns:
          list: a list of events
        """
        return self.store[:limit][::-1]

    # Alternative - Erase
    def all_events(self) -> List[Dict]:
        """
        Returns all events in the store, formatted as dictionaries.
        """
        return [event.to_dict() for event in self.store]
