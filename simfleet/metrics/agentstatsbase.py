import pandas as pd
from tabulate import tabulate
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

    def print_stats(self, df: pd.DataFrame, title: str = "Agent") -> None:
        """
        Prints the provided DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to print.
            title (str): The title to display before the DataFrame.
        """
        if df is not None and not df.empty:
            print(f"{title} metrics stats")
            print(tabulate(df, headers="keys", showindex=False, tablefmt="fancy_grid"))
        else:
            print(f"No data available for {title}.")
