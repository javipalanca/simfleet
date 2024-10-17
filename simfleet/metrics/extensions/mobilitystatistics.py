import pandas as pd
from simfleet.metrics.agentstatsbase import AgentStatsBase
from simfleet.utils.statistics import Log


class MobilityStatistics(AgentStatsBase):

    def run(self, events_log: Log) -> None:
        """
        Run the statistics generation process based on the agent type.

        Args:
            events_log (Log): A log containing all events from the simulation.
        """

        self.taxi_metrics(events_log, "simfleet_metrics_taxi.json")

        self.electric_taxi_metrics(events_log, "simfleet_metrics_electrictaxi.json")

        self.customer_taxi_metrics(events_log, "simfleet_metrics_taxicustomer.json")


    def taxi_metrics(self, events_log: Log, file_path: str) -> None:
        """
        Combines the calculation, JSON generation, and export process for ElectricTaxiAgent.

        Args:
            events_log (Log): A log containing all events from the simulation.
            file_path (str): The path where the final JSON file will be exported.
        """
        # Filtering relevant events for TaxiAgent
        filtered_events = events_log.filter(lambda event: event.class_type == "TaxiAgent" and
                                                          event.event_type in {
                                                              'transport_offer_acceptance',
                                                              'travel_to_pickup',
                                                              'travel_to_destination'
                                                          })

        # Transform events into a DataFrame
        event_fields = ["name", "timestamp", "event_type", "class_type"]
        details_fields = ["distance"]
        dataframe = filtered_events.to_dataframe(event_fields=event_fields, details_fields=details_fields)

        # Calculating KPIs (assignments, total distances, waiting and charging times)
        assignments = dataframe[dataframe["event_type"] == "transport_offer_acceptance"].groupby("name").size()
        total_distance = \
        dataframe[dataframe["event_type"].isin(["travel_to_pickup", "travel_to_destination"])] \
            .groupby("name")["distance"].sum()
        customer_total_distance = dataframe[dataframe["event_type"] == "travel_to_destination"] \
            .groupby("name")["distance"].sum()

        # Combining all metrics into a final DataFrame
        result_df = pd.DataFrame({
            "name": dataframe.groupby("name")["name"].first(),
            "class_type": dataframe.groupby("name")["class_type"].first(),
            "assignments": assignments,
            "total_distance": total_distance,
            "customer_total_distance": customer_total_distance
        }).fillna(0)

        # Calculating general averages for the "GeneralMetrics" section
        avg_total_distance = result_df["total_distance"].mean()

        # Convert the DataFrame into a dictionary structure indexed by an agent number
        agent_metrics = result_df.to_dict(orient="records")

        # Convert the agent metrics into a dictionary with numeric keys (0, 1, 2, ...)
        numbered_agents = {str(i): agent_metrics[i] for i in range(len(agent_metrics))}

        # Converting the result DataFrame into a JSON-like structure
        #agent_metrics = result_df.to_dict(orient="index")
        json_structure = {
            "GeneralMetrics": {
                "Class type": "ElectricTaxiAgent",
                "Avg Total Distance": f"{avg_total_distance:.2f}"
            },
            "ElectricTaxiAgent": numbered_agents#{
                #str(i): agent_metrics[i] for i in agent_metrics
            #}
        }

        # Exporting the result to a JSON file
        self.export_to_json(json_structure, file_path)

    def electric_taxi_metrics(self, events_log: Log, file_path: str) -> None:
        """
        Combines the calculation, JSON generation, and export process for ElectricTaxiAgent.

        Args:
            events_log (Log): A log containing all events from the simulation.
            file_path (str): The path where the final JSON file will be exported.
        """
        # Filtering relevant events for ElectricTaxiAgent
        filtered_events = events_log.filter(lambda event: event.class_type == "ElectricTaxiAgent" and
                                                          event.event_type in {
                                                              'transport_offer_acceptance',
                                                              'travel_to_pickup',
                                                              'travel_to_destination',
                                                              'travel_to_station',
                                                              'arrival_at_station',
                                                              'service_start',
                                                              'service_completion'
                                                          })

        # Transform events into a DataFrame
        event_fields = ["name", "timestamp", "event_type", "class_type"]
        details_fields = ["distance"]
        dataframe = filtered_events.to_dataframe(event_fields=event_fields, details_fields=details_fields)

        # Calculating KPIs (assignments, total distances, waiting and charging times)
        assignments = dataframe[dataframe["event_type"] == "transport_offer_acceptance"].groupby("name").size()
        total_distance = \
        dataframe[dataframe["event_type"].isin(["travel_to_pickup", "travel_to_destination", "travel_to_station"])] \
            .groupby("name")["distance"].sum()
        customer_total_distance = dataframe[dataframe["event_type"] == "travel_to_destination"] \
            .groupby("name")["distance"].sum()
        station_total_distance = dataframe[dataframe["event_type"] == "travel_to_station"] \
            .groupby("name")["distance"].sum()

        # Using pivot table to calculate waiting and charging times
        pivot_df = dataframe.pivot_table(index="name", columns="event_type", values="timestamp", aggfunc="first")
        waiting_in_station_time = (pivot_df["service_start"] - pivot_df["arrival_at_station"])
        charging_time = (pivot_df["service_completion"] - pivot_df["service_start"])

        # Combining all metrics into a final DataFrame
        result_df = pd.DataFrame({
            "name": dataframe.groupby("name")["name"].first(),
            "class_type": dataframe.groupby("name")["class_type"].first(),
            "assignments": assignments,
            "total_distance": total_distance,
            "customer_total_distance": customer_total_distance,
            "station_total_distance": station_total_distance,
            "waiting_in_station_time": waiting_in_station_time,
            "charging_time": charging_time
        }).fillna(0)

        # Calculating general averages for the "GeneralMetrics" section
        avg_charging_time = result_df["charging_time"].mean()
        avg_total_distance = result_df["total_distance"].mean()

        # Convert the DataFrame into a dictionary structure indexed by an agent number
        agent_metrics = result_df.to_dict(orient="records")

        # Convert the agent metrics into a dictionary with numeric keys (0, 1, 2, ...)
        numbered_agents = {str(i): agent_metrics[i] for i in range(len(agent_metrics))}

        # Converting the result DataFrame into a JSON-like structure
        #agent_metrics = result_df.to_dict(orient="index")
        json_structure = {
            "GeneralMetrics": {
                "Class type": "ElectricTaxiAgent",
                "Avg Transport Charging Time": f"{avg_charging_time:.2f}",
                "Avg Total Distance": f"{avg_total_distance:.2f}"
            },
            "ElectricTaxiAgent": numbered_agents#{
                #str(i): agent_metrics[i] for i in agent_metrics
            #}
        }

        # Exporting the result to a JSON file
        self.export_to_json(json_structure, file_path)


    def customer_taxi_metrics(self, events_log: Log, file_path: str) -> None:
        """
        Combines the calculation, JSON generation, and export process for TaxiCustomerAgent.

        Args:
            events_log (Log): A log containing all events from the simulation.
            file_path (str): The path where the final JSON file will be exported.
        """
        # Filtering relevant events for TaxiCustomerAgent
        filtered_events = events_log.filter(lambda event: event.class_type == "TaxiCustomerAgent" and
                                                          event.event_type in {'customer_request', 'customer_pickup',
                                                                               'trip_completion'})

        # Transform events into a DataFrame
        event_fields = ["name", "timestamp", "event_type", "class_type"]
        details_fields = []
        dataframe = filtered_events.to_dataframe(event_fields=event_fields, details_fields=details_fields)

        # Using pivot table to calculate waiting time and total trip time
        pivot_df = dataframe.pivot_table(index="name", columns="event_type", values="timestamp", aggfunc="first")
        waiting_time = (pivot_df["customer_pickup"] - pivot_df["customer_request"])
        total_time = (pivot_df["trip_completion"] - pivot_df["customer_request"])

        # Combining all metrics into a final DataFrame
        result_df = pd.DataFrame({
            "name": dataframe.groupby("name")["name"].first(),
            "class_type": dataframe.groupby("name")["class_type"].first(),
            "waiting_time": waiting_time,
            "total_time": total_time
        }).fillna(0)

        # Calculating general averages for the "GeneralMetrics" section
        avg_waiting_time = result_df["waiting_time"].mean()
        avg_total_time = result_df["total_time"].mean()

        # Convert the DataFrame into a dictionary structure indexed by an agent number
        agent_metrics = result_df.to_dict(orient="records")

        # Convert the agent metrics into a dictionary with numeric keys (0, 1, 2, ...)
        numbered_agents = {str(i): agent_metrics[i] for i in range(len(agent_metrics))}

        # Converting the result DataFrame into a JSON-like structure
        #agent_metrics = result_df.to_dict(orient="index")
        json_structure = {
            "GeneralMetrics": {
                "Class type": "TaxiCustomerAgent",
                "Avg Waiting Time": f"{avg_waiting_time:.2f}",
                "Avg Total Time": f"{avg_total_time:.2f}"
            },
            "TaxiCustomerAgent": numbered_agents #{
                #str(i): agent_metrics[i] for i in agent_metrics
            #}
        }

        # Exporting the result to a JSON file
        self.export_to_json(json_structure, file_path)

    def export_to_json(self, json_data: dict, file_path: str) -> None:
        """
        Export the final JSON structure to a JSON file.

        Args:
            json_data (dict): The data to be exported.
            file_path (str): Path where the JSON file will be saved.
        """
        with open(file_path, 'w') as f:
            import json
            json.dump(json_data, f, indent=4)
