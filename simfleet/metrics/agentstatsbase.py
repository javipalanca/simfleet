from abc import ABC, abstractmethod  # For defining an abstract class
from simfleet.utils.statistics import Log


# Base class (parent)
class AgentStatsBase(ABC):

    @abstractmethod
    def run(self, events_log: Log) -> None:
        """
        Abstract method that must be implemented in subclasses.
        This method will handle the specific logic for processing
        events based on the type of agent.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement the run method.")
