====================
Metrics Usage Manual
====================

Simfleet includes a default metrics module that filters specific simulation events and calculates key performance indicators (KPIs) for different agent types.
The results are exported in JSON format and summarized for easier analysis. Key components include base statistics for taxi and electric taxi scenarios,
as well as KPIs such as total distance, number of assignments, and waiting times.

Default events
==============

Simfleet includes an Event System that records critical activities performed by agents during the simulation. These events provide valuable information about agent
behavior and performance.

Simfleet comes with default event types for taxi and electric taxi scenarios.

The key default events are:

+-------------------------------+
|  Default events: TaxiCustomer |
+-------------------------------+
|  Event                        |
+===============================+
| customer_request              |
+-------------------------------+
| transport_offer_acceptance    |
+-------------------------------+
| wait_for_pickup               |
+-------------------------------+
| customer_pickup               |
+-------------------------------+
| travel_to_destination         |
+-------------------------------+
| trip_completion               |
+-------------------------------+

+----------------------------------------------------------+
|  Default events: Taxi and ElectricTaxi                   |
+----------------------------+----------+------------------+
|  Event                     |   Taxi   |   ElectricTaxi   |
+============================+==========+==================+
| customer_request_reception |   yes    |       yes        |
+----------------------------+----------+------------------+
| transport_offer            |   yes    |       yes        |
+----------------------------+----------+------------------+
| transport_offer_acceptance |   yes    |       yes        |
+----------------------------+----------+------------------+
| travel_to_pickup           |   yes    |       yes        |
+----------------------------+----------+------------------+
| customer_pickup            |   yes    |       yes        |
+----------------------------+----------+------------------+
| travel_to_destination      |   yes    |       yes        |
+----------------------------+----------+------------------+
| trip_completion            |   yes    |       yes        |
+----------------------------+----------+------------------+
| transport_need_for_service |   no     |       yes        |
+----------------------------+----------+------------------+
| travel_to_station          |   no     |       yes        |
+----------------------------+----------+------------------+
| arrival_at_station         |   no     |       yes        |
+----------------------------+----------+------------------+
| wait_for_service           |   no     |       yes        |
+----------------------------+----------+------------------+
| service_start              |   no     |       yes        |
+----------------------------+----------+------------------+
| service_completion         |   no     |       yes        |
+----------------------------+----------+------------------+

Both the GUI and the CLI allow users to extract these events once a simulation starts. An example of the output with events:

.. code-block:: json

    [
    {
        "name": "taxicustomer1@localhost",
        "timestamp": 6.138403,
        "event_type": "customer_request",
        "class_type": "TaxiCustomerAgent",
        "details": {}
    },
    {
        "name": "taxi1@localhost",
        "timestamp": 6.1398,
        "event_type": "transport_offer_acceptance",
        "class_type": "TaxiAgent",
        "details": {}
    },
    {
        "name": "taxicustomer1@localhost",
        "timestamp": 6.141237,
        "event_type": "wait_for_pickup",
        "class_type": "TaxiCustomerAgent",
        "details": {}
    },
    {
        "name": "taxi1@localhost",
        "timestamp": 6.159652,
        "event_type": "travel_to_pickup",
        "class_type": "TaxiAgent",
        "details": {
            "distance": 2815,
            "duration": 261.1
        }
    },
    {
        "name": "taxicustomer1@localhost",
        "timestamp": 12.195493,
        "event_type": "customer_pickup",
        "class_type": "TaxiCustomerAgent",
        "details": {}
    },
    {
        "name": "taxi1@localhost",
        "timestamp": 23.262776,
        "event_type": "trip_completion",
        "class_type": "TaxiAgent",
        "details": {}
    }
    ]

Default metrics
===============

Taxi metrics
------------

The Taxi and ElectricTaxi metrics calculate and export statistics for regular taxis and electric taxis, respectively. Both metrics track similar KPIs,
such as the number of assignments, total distance and customer total distance.

These metrics include:

* **Assignments:** The number of assignments each taxi completes.

* **Total Distance:** The sum of distances traveled by each taxi.

* **Customer Total Distance:** The distance traveled with customers onboard.

Example CLI Output:

.. code-block:: json:

    2024-12-20 15:12:53.351 | WARNING  | simfleet.simulator:run:1391 - Agent[simulator_taxis]: The agent has a mailbox size of (0)
    2024-12-20 15:12:53.381 | INFO     | simfleet.simulator:stop:585 - Stopping simulation...
    2024-12-20 15:12:53.382 | INFO     | simfleet.simulator:stop:587 - Terminating... (74.3 seconds elapsed)
    Simulation Results:
    taxi_df stats
    ╒═════════════════╤══════════════╤═══════════════╤══════════════════╤═══════════════════════════╕
    │ name            │ class_type   │   assignments │   total_distance │   customer_total_distance │
    ╞═════════════════╪══════════════╪═══════════════╪══════════════════╪═══════════════════════════╡
    │ taxi1@localhost │ TaxiAgent    │             1 │           8864.2 │                    6049.2 │
    ╘═════════════════╧══════════════╧═══════════════╧══════════════════╧═══════════════════════════╛


Example JSON Output:

.. code-block:: json

    {
    "GeneralMetrics": {
        "Class type": "ElectricTaxiAgent",
        "Avg Total Distance": "8864.20"
    },
    "ElectricTaxiAgent": {
        "0": {
            "name": "taxi1@localhost",
            "class_type": "TaxiAgent",
            "assignments": 1,
            "total_distance": 8864.2,
            "customer_total_distance": 6049.2
        }
    }
    }


ElectricTaxi metrics
--------------------

The ElectricTaxi metrics module calculates and exports additional metrics specific to electric taxis. These include station-related distances, waiting times at charging stations,
and charging durations. These distinctions help to understand the operational differences and requirements of electric taxis.

These metrics include:

* **Station Total Distance:** The distance traveled to charging stations.

* **Waiting in Station Time:** Time spent waiting for charging service.

* **Charging Time:** Time spent charging.

Example CLI Output:

.. code-block:: console

    2024-12-20 12:16:05.569 | INFO     | simfleet.simulator:stop:585 - Stopping simulation...
    2024-12-20 12:16:05.569 | INFO     | simfleet.simulator:stop:587 - Terminating... (70.2 seconds elapsed)
    2024-12-20 12:16:05.584 | WARNING  | simfleet.metrics.lib.mobilitystatistics:run:22 - EXCEPTION - taxi_metrics hasn't events: 'event_type'
    Simulation Results:
    electrictaxi_df stats
    ╒═════════════════╤═══════════════════╤═══════════════╤══════════════════╤═══════════════════════════╤══════════════════════════╤═══════════════════════════╤═════════════════╕
    │ name            │ class_type        │   assignments │   total_distance │   customer_total_distance │   station_total_distance │   waiting_in_station_time │   charging_time │
    ╞═════════════════╪═══════════════════╪═══════════════╪══════════════════╪═══════════════════════════╪══════════════════════════╪═══════════════════════════╪═════════════════╡
    │ taxi1@localhost │ ElectricTaxiAgent │             1 │          19882.2 │                   10377.6 │                   3585.1 │                  0.004253 │         2.69983 │
    ├─────────────────┼───────────────────┼───────────────┼──────────────────┼───────────────────────────┼──────────────────────────┼───────────────────────────┼─────────────────┤
    │ taxi2@localhost │ ElectricTaxiAgent │             3 │          18676.1 │                    8001.2 │                   2715   │                  0.004592 │         1.69966 │
    ╘═════════════════╧═══════════════════╧═══════════════╧══════════════════╧═══════════════════════════╧══════════════════════════╧═══════════════════════════╧═════════════════╛


Example JSON Output:

.. code-block:: json

    {
    "GeneralMetrics": {
        "Class type": "ElectricTaxiAgent",
        "Avg Transport Charging Time": "2.20",
        "Avg Total Distance": "19279.15"
    },
    "ElectricTaxiAgent": {
        "0": {
            "name": "taxi1@localhost",
            "class_type": "ElectricTaxiAgent",
            "assignments": 1,
            "total_distance": 19882.2,
            "customer_total_distance": 10377.6,
            "station_total_distance": 3585.1,
            "waiting_in_station_time": 0.004253000000000284,
            "charging_time": 2.6998309999999996
        },
        "1": {
            "name": "taxi2@localhost",
            "class_type": "ElectricTaxiAgent",
            "assignments": 3,
            "total_distance": 18676.1,
            "customer_total_distance": 8001.200000000001,
            "station_total_distance": 2715.0,
            "waiting_in_station_time": 0.004592000000002372,
            "charging_time": 1.699659999999998
        }
    }
    }


TaxiCustomer metrics
--------------------

The TaxiCustomer metrics calculate and export statistics for taxi customers.

These metrics include:

* **Waiting Time:** The time between requesting a taxi and being picked up.

* **Total Trip Time:** The time from requesting a taxi to arriving at the destination.

Example CLI Output:

.. code-block:: console

    taxicustomer_df stats
    ╒═════════════════════╤═══════════════════╤════════════════╤══════════════╕
    │ name                │ class_type        │   waiting_time │   total_time │
    ╞═════════════════════╪═══════════════════╪════════════════╪══════════════╡
    │ customer1@localhost │ TaxiCustomerAgent │       22.01    │     41.0558  │
    ├─────────────────────┼───────────────────┼────────────────┼──────────────┤
    │ customer2@localhost │ TaxiCustomerAgent │        4.12708 │      7.17027 │
    ├─────────────────────┼───────────────────┼────────────────┼──────────────┤
    │ customer3@localhost │ TaxiCustomerAgent │       20.0522  │     26.0952  │
    ├─────────────────────┼───────────────────┼────────────────┼──────────────┤
    │ customer4@localhost │ TaxiCustomerAgent │       38.0459  │     44.0929  │
    ╘═════════════════════╧═══════════════════╧════════════════╧══════════════╛

Example JSON Output:

.. code-block:: json

    {
    "GeneralMetrics": {
        "Class type": "TaxiCustomerAgent",
        "Avg Waiting Time": "21.06",
        "Avg Total Time": "29.60"
    },
    "TaxiCustomerAgent": {
        "0": {
            "name": "customer1@localhost",
            "class_type": "TaxiCustomerAgent",
            "waiting_time": 22.010048,
            "total_time": 41.055828
        },
        "1": {
            "name": "customer2@localhost",
            "class_type": "TaxiCustomerAgent",
            "waiting_time": 4.1270750000000005,
            "total_time": 7.170272
        },
        "2": {
            "name": "customer3@localhost",
            "class_type": "TaxiCustomerAgent",
            "waiting_time": 20.052232,
            "total_time": 26.095173
        },
        "3": {
            "name": "customer4@localhost",
            "class_type": "TaxiCustomerAgent",
            "waiting_time": 38.045898,
            "total_time": 44.092919
        }
    }
    }
