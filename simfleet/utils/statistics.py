from datetime import datetime
from typing import Optional, List, Dict, Callable


class Event:
    """
    A class to represent a specific event in the system.
    Each event is linked to KPIs and the agents involved in that event.
    """

    def __init__(self, name: str, event_type: str, class_type: str, timestamp: Optional[str] = None, details: Optional[Dict] = None):
        self.name = name  # Corresponds to "name" in your logs
        self.event_type = event_type  # Corresponds to "event" in your logs
        self.class_type = class_type.__name__  # New parameter to store the type of class
        self.timestamp = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        self.details = details if details else {}  # Corresponds to "details" in your logs

    # Alternative - Erase
    def to_dict(self) -> Dict:
        """Convert the event to a dictionary."""
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "event": self.event_type,
            "class_type": self.class_type,
            "details": self.details
        }


class StatisticsStore:
    """Stores and allows queries about KPI-related events for a single agent."""

    def __init__(self, agent_name: str, class_type: str):
        self.store = []
        self.agent_name = agent_name
        self.class_type = class_type  # Store the type of the agent for use in events

    def get_agent_name(self) -> str:
        """
        Returns the name of the agent.
        """
        return self.agent_name

    def emit(self, event_type: str, details: Optional[Dict] = None, timestamp: Optional[str] = None) -> None:
        """
        Adds a new event to the statistics store.
        """
        event = Event(name=self.agent_name, event_type=event_type, class_type=self.class_type, timestamp=timestamp, details=details)
        self.store.append(event)

    def all(self, limit: Optional[int] = None) -> List[Event]:
        """
        Returns all the events, until a limit if defined.
        """
        return self.store[:limit]

    # Alternative - Erase
    def all_events(self) -> List[Dict]:
        """
        Returns all events in the store, formatted as dictionaries.
        """
        return [event.to_dict() for event in self.store]

    def generate_partial_log(self) -> 'Log':
        """
        Generates a partial log of all events associated with this agent.
        """
        return Log(self.all())


class Log:
    """A class representing the log of all events, with filtering functionality."""

    def __init__(self, events: Optional[List[Event]] = None):
        self.events = events if events else []

    def filter(self, criterion: Callable[[Event], bool]) -> 'Log':
        """
        Filters the events based on a given criterion (a callable that returns True or False).
        """
        filtered_events = [event for event in self.events if criterion(event)]
        return Log(filtered_events)

    def filter_by_name(self, name: str) -> 'Log':
        """Filters events by the agent's name."""
        return self.filter(lambda event: event.name == name)

    def filter_by_class_type(self, class_type: str) -> 'Log':
        """Filters events by the class type."""
        return self.filter(lambda event: event.class_type == class_type)

    def filter_by_event_type(self, event_type: str) -> 'Log':
        """Filters events by the type of event."""
        return self.filter(lambda event: event.event_type == event_type)

    def filter_by_time_window(self, start_time: datetime, end_time: datetime) -> 'Log':
        """Filters events by a time window."""
        return self.filter(lambda event: start_time <= event.timestamp <= end_time)

    def drop(self, fields: List[str]) -> 'Log':
        """
        Removes specified fields from the 'details' of each event.
        """
        for event in self.events:
            for field in fields:
                if field in event.details:
                    del event.details[field]
        return self

    def all_events(self) -> List[Dict]:
        """Returns all events as a list of dictionaries."""
        return [event.to_dict() for event in self.events]

    def add_events(self, other_log: 'Log') -> None:
        """Adds events from another log to this log."""
        self.events.extend(other_log.events)

    def sort_by_timestamp(self, reverse: bool = False) -> None:
        """
        Sorts the events by their timestamp.

        Args:
            reverse (bool): If True, sorts in descending order. Defaults to False (ascending order).
        """
        self.events.sort(key=lambda event: event.timestamp, reverse=reverse)
