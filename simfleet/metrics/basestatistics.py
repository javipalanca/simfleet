from abc import ABC, abstractmethod
from simfleet.utils.statistics import Log


# Base class (parent)
class BaseStatisticsClass(ABC):

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

    def print_stats(self) -> None:
        """
        print_stats method of the base class, which only displays a message if it is not implemented in the child class.
        implemented in the child class.
        """
        raise NotImplementedError("No statistics are printed because it has not been implemented.")
