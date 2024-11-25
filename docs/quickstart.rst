============
Quickstart
============

.. contents:: Table of Contents


Start Guide
=================

This quick start guide demonstrates how to launch a basic simulation in SimFleet using taxis
as the sole mode of transport. Ensure you have the appropriate configuration file (in this case,
``4c_2t_1f_input.json``), which already defines a fleet of taxis and clients.

Steps to Start a Simulation:

Loading Scenarios: The Config File
==================================

SimFleet supports the use of a configuration file to define all the fields needed for consistent
scenario loading. A scenario file must be written in JSON format.

An example of a config file with four customers, two transports and one fleet manager:

.. code-block:: json

    {
    "fleets": [
        {
            "password": "secret",
            "name": "fleet1",
            "fleet_type": "taxi"
        }
    ],
    "transports": [
        {
            "speed": 2000,
            "class": "simfleet.common.lib.transports.models.taxi.TaxiAgent",
            "optional": {
                "fleet": "fleet1@localhost"
            },
            "position": [
                39.470390,
                -0.356541
            ],
            "password": "secret",
            "name": "taxi1",
            "icon": "taxi",
            "fleet_type": "taxi",
            "delay": 5
        },
        {
            "speed": 2000,
            "class": "simfleet.common.lib.transports.models.taxi.TaxiAgent",
            "optional": {
                "fleet": "fleet1@localhost"
            },
            "password": "secret",
            "name": "taxi2",
            "icon": "taxi",
            "fleet_type": "taxi",
            "delay": 5
        }
    ],
    "customers": [
        {
            "class": "simfleet.common.lib.customers.models.taxicustomer.TaxiCustomerAgent",
            "position": [
                39.45874369,
                -0.34011479
            ],
            "destination": [
                39.494655,
                -0.361639
            ],
            "password": "secret",
            "name": "taxicustomer1",
            "fleet_type": "taxi",
            "delay": 5
        },
        {
            "class": "simfleet.common.lib.customers.models.taxicustomer.TaxiCustomerAgent",
            "password": "secret",
            "name": "taxicustomer2",
            "fleet_type": "taxi",
            "delay": 5
        },
        {
            "class": "simfleet.common.lib.customers.models.taxicustomer.TaxiCustomerAgent",
            "password": "secret",
            "name": "taxicustomer3",
            "fleet_type": "taxi",
            "delay": 5
        },
        {
            "class": "simfleet.common.lib.customers.models.taxicustomer.TaxiCustomerAgent",
            "password": "secret",
            "name": "taxicustomer4",
            "fleet_type": "taxi",
            "delay": 5
        }
    ],
    "stations": [],
    "stops": [],
    "lines": [],
    "vehicles": [],
    "simulation_name": "taxi_simulation",
    "max_time": 1000,
    "verbose": 4,
    "transport_strategy": "simfleet.common.lib.transports.strategies.electrictaxi.FSMTaxiBehaviour",
    "customer_strategy": "simfleet.common.lib.customers.strategies.taxicustomer.AcceptFirstRequestBehaviour",
    "fleetmanager_strategy": "simfleet.common.lib.fleet.strategies.fleetmanager.DelegateRequestBehaviour",
    "directory_strategy": "simfleet.common.agents.directory.DirectoryStrategyBehaviour",
    "station_strategy": "simfleet.common.lib.stations.models.chargingstation.ChargingService",
    "vehicle_strategy": "simfleet.common.lib.vehicles.strategies.vehicle.FSMOneShotVehicleBehaviour",
    "mobility_metrics": "simfleet.metrics.lib.mobilitystatistics.MobilityStatisticsClass",
    "route_name": "route",
    "route_password": "route_passwd",
    "fleetmanager_name": "fleetmanager",
    "fleetmanager_password": "fleetmanager_passwd",
    "directory_name": "directory",
    "directory_password": "directory_passwd",
    "host": "localhost",
    "xmpp_port": 5222,
    "http_port": 9000,
    "http_ip": "localhost"
    }

Run the Simulation
==================

Once you have the configuration file ``4c_2t_1f_input.json``, open a command line and run the simulator using
the following command for a quick execution ``-r``:

.. code-block:: console

    $ simfleet --config 4c_2t_1f_input.json -r

Alternatively, you can run the simulator without the quick execution option ``-r`` and then interact
with it through the graphical interface:

.. code-block:: console

    $ simfleet --config 4c_2t_1f_input.json

.. hint::
    The Simulator agent is who raises the GUI and shows the address in the console output:

    .. code-block:: console

        2024-11-25 16:29:07.229 | INFO     | simfleet.simulator:setup:110 - Web interface running at http://127.0.0.1:9000/app

    This address is (in most cases): `http://127.0.0.1:9000/app <http://127.0.0.1:9000/app>`_


Once you visit the GUI address you see an interface like this:

.. figure:: images/screen3.png
    :align: center
    :alt: GUI at startup

    GUI at startup

In the GUI you can see a map of the city on the right and a Control Panel with various options on the left:

#. A **Run** button that starts the simulation.

#. A **Stop** button to stop and reset the simulation.

#. A **Download** button to get the simulation events in json format.

#. A collapsable tree view with the transports and customers that are included in the simulation.

If the **Run** button is pressed the simulation shows how the transports move to the customers and deliver them to their
destinations.

.. figure:: images/madrid.png
    :align: center
    :alt: Simulation in progress

    Simulation in progress

The console will output the default logging information and you can terminate the simulator by pressing ``Ctrl+C``  or Stop
button in the GUI. When you terminate the simulator the results of the simulations are printed.

.. code-block:: console

    $ simfleet --config myconfig.json
    2024-11-25 16:35:15.429 | INFO     | simfleet.config.settings:load_config:134 - Reading config 4c-2t-1f_input.json
    2024-11-25 16:35:15.710 | INFO     | simfleet.simulator:__init__:89 - Starting SimFleet (taxi_simulation)
    2024-11-25 16:35:15.722 | INFO     | simfleet.simulator:load_icons:467 - Reading icons /simfleet/templates/data/img_transports.json
    2024-11-25 16:35:15.934 | INFO     | simfleet.common.agents.directory:setup:63 - Directory agent directory running
    2024-11-25 16:35:15.935 | INFO     | simfleet.simulator:__init__:119 - Creating 1 managers, 2 transports, 4 customers, 0 stations and 0 vehicles.
    2024-11-25 16:35:15.935 | INFO     | simfleet.simulator:load_scenario:169 - Loading scenario...
    2024-11-25 16:35:15.937 | INFO     | simfleet.simulator:load_scenario:192 - Loading lines...
    2024-11-25 16:35:16.061 | SUCCESS  | simfleet.simulator:gather_batch:258 - All agents gathered
    2024-11-25 16:35:16.278 | INFO     | simfleet.common.agents.fleetmanager:setup:56 - FleetManager agent fleet1 running
    2024-11-25 16:35:16.292 | INFO     | simfleet.simulator:setup:133 - Simulator agent running
    2024-11-25 16:35:16.295 | INFO     | simfleet.simulator:setup:151 - Web interface running at http://localhost:9000/app


    ^C

    2024-11-25 16:36:26.108 | INFO     | simfleet.simulator:stop:258 -
    Terminating... (0.0 seconds elapsed)
    Simulation Results:
    taxi_df stats
    ╒═════════════════╤══════════════╤═══════════════╤══════════════════╤═══════════════════════════╕
    │ name            │ class_type   │   assignments │   total_distance │   customer_total_distance │
    ╞═════════════════╪══════════════╪═══════════════╪══════════════════╪═══════════════════════════╡
    │ taxi1@localhost │ TaxiAgent    │             2 │          18527.9 │                   11370.3 │
    ├─────────────────┼──────────────┼───────────────┼──────────────────┼───────────────────────────┤
    │ taxi2@localhost │ TaxiAgent    │             2 │           8917.4 │                    5283.5 │
    ╘═════════════════╧══════════════╧═══════════════╧══════════════════╧═══════════════════════════╛

    taxicustomer_df stats
    ╒═════════════════════════╤═══════════════════╤════════════════╤══════════════╕
    │ name                    │ class_type        │   waiting_time │   total_time │
    ╞═════════════════════════╪═══════════════════╪════════════════╪══════════════╡
    │ taxicustomer1@localhost │ TaxiCustomerAgent │        5.45727 │      16.5522 │
    ├─────────────────────────┼───────────────────┼────────────────┼──────────────┤
    │ taxicustomer2@localhost │ TaxiCustomerAgent │        5.24561 │      11.3367 │
    ├─────────────────────────┼───────────────────┼────────────────┼──────────────┤
    │ taxicustomer3@localhost │ TaxiCustomerAgent │       17.2685  │      21.3368 │
    ├─────────────────────────┼───────────────────┼────────────────┼──────────────┤
    │ taxicustomer4@localhost │ TaxiCustomerAgent │       28.0921  │      38.1682 │
    ╘═════════════════════════╧═══════════════════╧════════════════╧══════════════╛


.. hint::
    To view the options available in SimFleet's command line interface, use the following command ``--help``

.. code-block:: console

    $ simfleet --help

    Usage: simfleet [OPTIONS]

  Console script for SimFleet.

    Options:
      -n, --name TEXT              Name of the simulation execution.
      -o, --output TEXT            Filename for saving simulation events in JSON format.
      -mt, --max-time INTEGER      Maximum simulation time (in seconds).
      -r, --autorun                Run simulation as soon as the agents are ready.
      -c, --config TEXT            Filename of JSON file with initial config.
      -v, --verbose                Show verbose debug level: -v level 1, -vv level
                                   2, -vvv level 3, -vvvv level 4
      --help                       Show this message and exit.
