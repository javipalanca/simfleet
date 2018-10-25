import logging

import pandas as pd
from tabulate import tabulate
import json

from .passenger import PassengerAgent
from .taxi import TaxiAgent
from .scenario import Scenario
from .coordinator import CoordinatorAgent
from .route import RouteAgent

logger = logging.getLogger()


class SimulationConfig(object):
    """
    Dataclass to store the :class:`Simulator` config
    """

    def __init__(self):
        self.host = None
        self.simulation_name = None
        self.max_time = None
        self.taxi_strategy = None
        self.passenger_strategy = None
        self.coordinator_strategy = None
        self.scenario = None
        self.num_taxis = None
        self.num_passengers = None
        self.http_port = None
        self.ip_address = None
        self.coordinator_name = None
        self.coordinator_password = None
        self.route_name = None
        self.route_password = None
        self.verbose = None


class Simulator(object):
    """
    The Simulator. It manages all the simulation processes.
    Tasks done by the simulator at initialization:
        #. Create the XMPP server
        #. Run the SPADE backend
        #. Run the coordinator and route agents.
        #. Create agents passed as parameters (if any).
        #. Create agents defined in scenario (if any).

    After these tasks are done in the Simulator constructor, the simulation is started when the ``run`` method is called.
    """

    def __init__(self, config):
        self.config = config
        self.pretty_name = "({})".format(self.config.simulation_name) if self.config.simulation_name else ""
        self.verbose = self.config.verbose

        self.host = config.host

        self.simulation_time = 0

        self.coordinator_agent = None

        self.df_avg = None
        self.passenger_df = None
        self.taxi_df = None

        logger.info("Starting Taxi Simulator {}".format(self.pretty_name))

        self.coordinator_agent = CoordinatorAgent("{}@{}".format(config.coordinator_name, self.host),
                                                  password=config.coordinator_password,
                                                  http_port=config.http_port,
                                                  ip_address=config.ip_address)

        self.coordinator_agent.set_strategies(config.coordinator_strategy,
                                              config.taxi_strategy,
                                              config.passenger_strategy)
        self.coordinator_agent.start()

        route_id = "{}@{}".format(config.route_name, self.host)
        self.route_agent = RouteAgent(route_id, config.route_password)
        self.route_agent.start()
        self.coordinator_agent.route_id = route_id

        logger.info("Creating {} taxis and {} passengers.".format(config.num_taxis, config.num_passengers))
        self.coordinator_agent.create_agents_batch(TaxiAgent, config.num_taxis)
        self.coordinator_agent.create_agents_batch(PassengerAgent, config.num_passengers)

        if config.scenario:
            scenario = Scenario(config.scenario)
            scenario.load(self.coordinator_agent)

    def is_simulation_finished(self):
        """
        Checks if the simulation is finished.
        A simulation is finished if the max simulation time has been reached or when the coordinator says it.

        Returns:
            bool: whether the simulation is finished or not.
        """
        if self.config.max_time is None:
            return False
        return self.time_is_out() or self.coordinator_agent.is_simulation_finished()

    def time_is_out(self):
        """
        Checks if the max simulation time has been reached.

        Returns:
            bool: whether the max simulation time has been reached or not.
        """
        return self.coordinator_agent.get_simulation_time() > self.config.max_time

    def run(self):
        """
        Starts the simulation (tells the coordinator agent to start the simulation).
        """
        self.coordinator_agent.run_simulation()

    def stop(self):
        """
        Finishes the simulation and prints simulation stats.
        Tasks done when a simulation is stopped:
            #. Stop participant agents.
            #. Print stats.
            #. Stop Route agent.
            #. Stop Coordinator agent.
        """
        self.simulation_time = self.coordinator_agent.get_simulation_time()

        logger.info("\nTerminating... ({0:.1f} seconds elapsed)".format(self.simulation_time))

        self.coordinator_agent.stop_agents()

        self.print_stats()

        self.route_agent.stop()
        self.coordinator_agent.stop()

    def collect_stats(self):
        """
        Collects stats from all participant agents and from the simulation and stores it in three dataframes.
        """

        df_avg, self.taxi_df, self.passenger_df = self.coordinator_agent.get_stats_dataframes()

        columns = []
        if self.config.simulation_name:
            df_avg["Simulation Name"] = self.config.simulation_name
            columns = ["Simulation Name"]
        columns += ["Avg Waiting Time", "Avg Total Time", "Simulation Time"]
        if self.config.max_time:
            df_avg["Max Time"] = self.config.max_time
            columns += ["Max Time"]
        columns += ["Simulation Finished"]
        self.df_avg = df_avg[columns]

    def get_stats(self):
        """
        Returns the dataframes collected by :func:`collect_stats`

        Returns:
            ``pandas.DataFrame``, ``pandas.DataFrame``, ``pandas.DataFrame``: average df, passengers df and taxi df
        """
        return self.df_avg, self.passenger_df, self.taxi_df

    def print_stats(self):
        """
        Prints the dataframes collected by ``collect_stats``.
        """
        if self.df_avg is None:
            self.collect_stats()

        print("Simulation Results")
        print(tabulate(self.df_avg, headers="keys", showindex=False, tablefmt="fancy_grid"))
        print("Passenger stats")
        print(tabulate(self.passenger_df, headers="keys", showindex=False, tablefmt="fancy_grid"))
        print("Taxi stats")
        print(tabulate(self.taxi_df, headers="keys", showindex=False, tablefmt="fancy_grid"))

    def write_file(self, filename, fileformat="json"):
        """
        Writes the dataframes collected by ``collect_stats`` in JSON or Excel format.

        Args:
            filename (str): name of the output file to be written.
            fileformat (str): format of the output file. Choices: json or excel
        """
        if self.df_avg is None:
            self.collect_stats()
        if fileformat == "json":
            self.write_json(filename)
        elif fileformat == "excel":
            self.write_excel(filename)

    def write_json(self, filename):
        """
        Writes the collected data by ``collect_stats`` in a json file.

        Args:
            filename (str): name of the json file.
        """
        data = {
            "simulation": json.loads(self.df_avg.to_json(orient="index"))["0"],
            "passengers": json.loads(self.passenger_df.to_json(orient="index")),
            "taxis": json.loads(self.taxi_df.to_json(orient="index"))
        }

        with open(filename, 'w') as f:
            f.seek(0)
            json.dump(data, f, indent=4)

    def write_excel(self, filename):
        """
        Writes the collected data by ``collect_stats`` in an excel file.

        Args:
            filename (str): name of the excel file.
        """
        writer = pd.ExcelWriter(filename)
        self.df_avg.to_excel(writer, 'Simulation')
        self.passenger_df.to_excel(writer, 'Passengers')
        self.taxi_df.to_excel(writer, 'Taxis')
        writer.save()
