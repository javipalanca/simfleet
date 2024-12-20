============
Usage Manual
============

Using SimFleet is straightforward and can be done by running the application from the command line. There are two modes of use:
a **command-line interface (CLI)** and a **web-based graphical interface (GUI)**. You can execute simulations purely through the command
line or use the simpler and more intuitive graphical interface.

SimFleet supports a wide variety of urban mobility scenarios, as the simulator includes predefined agents and strategies. In this section,
we will explore how to use **command-line interface (CLI)** of advance mode and the different simulation scenarios available.


The Configuration file's Structure
==========================

The configuration file of a SimFleet simulation fully characterizes the simulation scenario including the information of every agent.
The file follows a JSON structure, presenting one list per type of agent in the simulation, as well as some general configuration entries.
In turn, the list of each agent type contains individual agent definitions: one dictionary per agent, describing its necessary attributes.

Following, we present a description of each basic field present in default configuration files, splitting the information in sections.

**Agent settings**: Listings of agent definitions, split by specific agent types. Any combination of agents may be included in a simulation scenario,
although their interaction will be dependent on their strategic behaviour.

+--------------------------------------------------------------------------------------+
|  Agent definitions & settings                                                        |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| fleets      |   List of FleetManager agents                                          |
+-------------+------------------------------------------------------------------------+
| transports  |   List of Transport agents                                             |
+-------------+------------------------------------------------------------------------+
| customers   |   List of Customer agents                                              |
+-------------+------------------------------------------------------------------------+
| stations    |   List of Station (infrastructure) agents                              |
+-------------+------------------------------------------------------------------------+
| stops       |   List of BusStop agents (for urban bus simulations)                   |
+-------------+------------------------------------------------------------------------+
| *lines*     |   List of bus lines (for urban bus simulation)                         |
+-------------+------------------------------------------------------------------------+
| vehicles    |   List of autonomous Vehicle agents                                    |
+-------------+------------------------------------------------------------------------+

.. note::
    The field *lines* does not define agents. It is an auxiliary configuration field for bus transportation simulations.

**Default Strategies**: The behaviour of an agent during the simulation is governed by its so-called Strategy.
The configuration file allows for the definition of a specific strategy for each of the introduced agents. However, in most cases,
all agents of the same type will behave in the same manner. For that, the configuration file includes the following fields.

+--------------------------------------------------------------------------------------------------+
|  Default strategic behaviours                                                                    |
+-----------------------+--------------------------------------------------------------------------+
|  Field                |  Description                                                             |
+=======================+==========================================================================+
| transport_strategy    |   The strategic behaviour used by Transport agents                       |
+-----------------------+--------------------------------------------------------------------------+
| customer_strategy     |   The strategic behaviour used by Customer agents                        |
+-----------------------+--------------------------------------------------------------------------+
| fleetmanager_strategy |   The strategic behaviour used by Fleet manager                          |
+-----------------------+--------------------------------------------------------------------------+
| station_strategy      |   The strategic behaviour used by Station agents                         |
+-----------------------+--------------------------------------------------------------------------+
| vehicle_strategy      |   The strategic behaviour used by Vehicle agents                         |
+-----------------------+--------------------------------------------------------------------------+
| directory_strategy    |   The strategic behaviour used by the Directory agent                    |
+-----------------------+--------------------------------------------------------------------------+

**Simulation settings**: General settings for the localization of a scenario and the duration of its simulation.

+---------------------------------------------------------------------------------------------+
|  Simulation settings                                                                        |
+------------------+--------------------------------------------------------------------------+
|  Field           |  Description                                                             |
+==================+==========================================================================+
| simulation_name  |   Name of the simulation defined by this configuration file              |
+------------------+--------------------------------------------------------------------------+
| max_time         |   Maximum time (in seconds) for which the simulation will run            |
+------------------+--------------------------------------------------------------------------+
| coords           |   The initial geographic coordinates for the simulation map              |
+------------------+--------------------------------------------------------------------------+
| zoom             |   The initial zoom level of the simulation map                           |
+------------------+--------------------------------------------------------------------------+

.. note::
    The **coords** field can use the name of a city, town, neighbourhood or a specific coordinate, e.g. ‘Valencia’ or [39.4697065, -0.3763353]. This reference point centres the simulation on the map.
    In addition, the **zoom** field controls the scale of the bounding box for the random creation of positions of an agent on the map.

**Metrics and Server settings:** Among the remaining fields, we highlight **mobility_metrics**, which accepts a path to the file that defines the metrics to be calculated at the end of a simulation.
The rest refer to parameters necessary for the communication of SimFleet agents with the routing server and the XMPP server.
We recommend keeping their default values, which appear in the example configuration files.

+--------------------------------------------------------------------------------------------------------------+
|  Metrics, Credentials and Network Settings                                                                   |
+-----------------------+--------------------------------------------------------------------------------------+
|  Field                |  Description                                                                         |
+=======================+======================================================================================+
| mobility_metrics      |   Custom class for the computation of simulation metrics at the end of the execution |
+-----------------------+--------------------------------------------------------------------------------------+
| fleetmanager_name     |   Name for registering the fleet manager agent in the XMPP server                    |
+-----------------------+--------------------------------------------------------------------------------------+
| fleetmanager_password |   Password for registering the fleet manager agent in the XMPP server                |
+-----------------------+--------------------------------------------------------------------------------------+
| directory_name        |   Name for registering the directory agent in the XMPP server                        |
+-----------------------+--------------------------------------------------------------------------------------+
| directory_password    |   Password for registering the directory agent in the XMPP server                    |
+-----------------------+--------------------------------------------------------------------------------------+
| route_host            |   URL of the OSRM routing service used for calculating agent movement                |
+-----------------------+--------------------------------------------------------------------------------------+
| host                  |   The XMPP host address where the simulation platform is running                     |
+-----------------------+--------------------------------------------------------------------------------------+
| xmpp_port             |   Port for XMPP communication                                                        |
+-----------------------+--------------------------------------------------------------------------------------+
| http_port             |   Port for the HTTP server used for the simulator's GUI                              |
+-----------------------+--------------------------------------------------------------------------------------+
| http_ip               |   IP address for the HTTP server used for the simulator's GUI                        |
+-----------------------+--------------------------------------------------------------------------------------+

This structure provides a flexible framework for creating different scenarios. You may find an empty configuration file below,
to be used as a template for the development of custom simulation scenarios.

.. code-block:: json

    {
    "fleets": [],
    "transports": [],
    "customers": [],
    "stations": [],
    "stops": [],
    "lines": [],
    "vehicles": [],
    "simulation_name": "my_city",
    "max_time": 1000,
    "coords": "Valencia",
    "zoom": 12,
    "transport_strategy": "simfleet.module.file.TransportBehaviourClass",
    "customer_strategy": "simfleet.module.file.CustomerBehaviourClass",
    "fleetmanager_strategy": "simfleet.module.file.FleetManagerBehaviourClass",
    "directory_strategy": "simfleet.module.file.DirectoryBehaviourClass",
    "station_strategy": "simfleet.module.file.StationBehaviourClass",
    "vehicle_strategy": "simfleet.module.file.VehicleBehaviourClass",
    "mobility_metrics": "simfleet.module.file.MyMetricsClass",
    "fleetmanager_name": "fleetmanager",
    "fleetmanager_password": "fleetmanager_passwd",
    "route_host": "http://router.project-osrm.org/",
    "directory_name": "directory",
    "directory_password": "directory_passwd",
    "host": "localhost",
    "xmpp_port": 5222,
    "http_port": 9000,
    "http_ip": "localhost"
    }

Transportation simulation modes
===============================

Taxi simulation scenario
------------------------

In this scenario, SimFleet there are three types of agent that interact among them during simulations. These are the **FleetManager agent**,
the **Taxi agent**, and the **TaxiCustomer agent**.


Description of the Agents
^^^^^^^^^^^^^^^^^^^^^^^^^

* **TaxiCustomer Agents**

    The TaxiCustomer agents represent people that need to go from one location of the city (their "current location") to
    another (their "destination").
    For doing so, each Taxi customer agent requests a single transport service and, once it is transported to its destination,
    it reaches its final state and ends its execution.

* **Taxi Agents**

    The Taxi agents represent vehicles which can transport Taxi customer agents from their current positions to their respective
    destinations.

* **FleetManager Agent**

    The FleetManager Agent is responsible for putting in contact the TaxiCustomer agents that need a transport service, and the Taxi
    agents that may be available to offer these services. In short, the FleetManager Agent acts like a transport call center, accepting
    the incoming requests from customers (TaxiCustomer agents) and forwarding these requests to the (appropriate) Taxi agents.
    In order to do so, the FleetManager has a registration protocol by which Taxi agents subscribe to the Fleet Manager
    that represents their fleet. This is automatically done when a Taxi agent is started.

In the context of SimFleet, a "transport service" involves the following steps:

    #. The Taxi moves from its current position to the TaxiCustomer's location to pick them up.
    #. The Taxi transports the TaxiCustomer to their destination.

The Config file
---------------

The most important fields that the Taxi simulation scenario file must include are a taxi customers list and a taxis list. Each taxi customer must include the
following fields:

+--------------------------------------------------------------------------------------+
|  Taxi Customers                                                                      |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| class       |   Custom agent file in the format ``module.file.Class``                |
+-------------+------------------------------------------------------------------------+
| position    |   Initial coordinates of the customer (optional)                       |
+-------------+------------------------------------------------------------------------+
| destination |   Destination coordinates of the customer (optional)                   |
+-------------+------------------------------------------------------------------------+
| name        |   Name of the customer                                                 |
+-------------+------------------------------------------------------------------------+
| password    |   Password for registering the customer in the platform (optional)     |
+-------------+------------------------------------------------------------------------+
| fleet_type  |   Fleet type that the customer wants to use                            |
+-------------+------------------------------------------------------------------------+
| icon        |   Custom icon (in base64 format) to be used by the customer (optional) |
+-------------+------------------------------------------------------------------------+
| strategy    |   Custom strategy file in the format ``module.file.Class`` (optional)  |
+-------------+------------------------------------------------------------------------+
| delay       |   Intentional agent pause in seconds  (optional)                       |
+-------------+------------------------------------------------------------------------+

For taxis the fields are as follows:

+---------------------------------------------------------------------------------------------+
|  Taxi                                                                                       |
+------------------+--------------------------------------------------------------------------+
|  Field           |  Description                                                             |
+==================+==========================================================================+
| class            |   Custom agent file in the format ``module.file.Class``                  |
+------------------+--------------------------------------------------------------------------+
| position         |   Initial coordinates of the transport (optional)                        |
+------------------+--------------------------------------------------------------------------+
| name             |   Name of the transport                                                  |
+------------------+--------------------------------------------------------------------------+
| password         |   Password for registering the transport in the platform (optional)      |
+------------------+--------------------------------------------------------------------------+
| speed            |   Speed of the transport (in meters per second)  (optional)              |
+------------------+--------------------------------------------------------------------------+
| fleet_type       |   Fleet type that the customer wants to use                              |
+------------------+--------------------------------------------------------------------------+
| optional         |   **fleet**: The fleet manager's JID to be subscribed to (optional)      |
+------------------+--------------------------------------------------------------------------+
| icon             |   Custom icon (in base64 format) to be used by the transport  (optional) |
+------------------+--------------------------------------------------------------------------+
| strategy         |   Custom strategy file in the format ``module.file.Class`` (optional)    |
+------------------+--------------------------------------------------------------------------+
| delay            |   Intentional agent pause in seconds  (optional)                         |
+------------------+--------------------------------------------------------------------------+

For fleet managers the fields are as follows:

+--------------------------------------------------------------------------------------+
|  Fleet managers                                                                      |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| name        |   Name of the manager                                                  |
+-------------+------------------------------------------------------------------------+
| password    |   Password for registering the manager in the platform (optional)      |
+-------------+------------------------------------------------------------------------+
| fleet_type  |   Fleet type that the agent manages                                    |
+-------------+------------------------------------------------------------------------+
| icon        |   Custom icon (in base64 format) to be used by the manager  (optional) |
+-------------+------------------------------------------------------------------------+
| strategy    |   Custom strategy file in the format ``module.file.Class``  (optional) |
+-------------+------------------------------------------------------------------------+

An example of a config file with four customers, two transports and one fleet manager:

.. code-block:: json

    {
    "fleets": [
        {
            "name": "fleet1",
            "password": "secret",
            "fleet_type": "taxi"
        }
    ],
    "transports": [
        {
            "class": "simfleet.common.lib.transports.models.taxi.TaxiAgent",
            "position": [
                39.470390,
                -0.356541
            ],
            "name": "taxi1",
            "password": "secret",
            "speed": 2000,
            "fleet_type": "taxi",
            "optional": {
                "fleet": "fleet1@localhost"
            },
            "icon": "taxi",
            "delay": 0
        },
        {
            "class": "simfleet.common.lib.transports.models.taxi.TaxiAgent",
            "name": "taxi2",
            "password": "secret",
            "speed": 2000,
            "fleet_type": "taxi",
            "optional": {
                "fleet": "fleet1@localhost"
            },
            "icon": "taxi"
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
            "name": "taxicustomer1",
            "password": "secret",
            "fleet_type": "taxi",
            "delay": 5
        },
        {
            "class": "simfleet.common.lib.customers.models.taxicustomer.TaxiCustomerAgent",
            "name": "taxicustomer2",
            "password": "secret",
            "fleet_type": "taxi",
            "delay": 5
        },
        {
            "class": "simfleet.common.lib.customers.models.taxicustomer.TaxiCustomerAgent",
            "name": "taxicustomer3",
            "password": "secret",
            "fleet_type": "taxi",
            "delay": 7
        },
        {
            "class": "simfleet.common.lib.customers.models.taxicustomer.TaxiCustomerAgent",
            "name": "taxicustomer4",
            "password": "secret",
            "fleet_type": "taxi",
            "delay": 10
        }
    ],
    "stations": [],
    "stops": [],
    "lines": [],
    "vehicles": [],
    "simulation_name": "taxis",
    "max_time": 100,
    "transport_strategy": "simfleet.common.lib.transports.strategies.taxi.FSMTaxiBehaviour",
    "customer_strategy": "simfleet.common.lib.customers.strategies.taxicustomer.AcceptFirstRequestBehaviour",
    "fleetmanager_strategy": "simfleet.common.lib.fleet.strategies.fleetmanager.DelegateRequestBehaviour",
    "fleetmanager_name": "fleetmanager",
    "fleetmanager_password": "fleetmanager_passwd",
    "host": "localhost",
    "http_port": 9000,
    "http_ip": "localhost"
    }

This configuration file includes:

    * One taxi with a fixed position and another with a random position.
    * One customer with fixed origin and destination coordinates.
    * Three customers with random origin and destination coordinates.

Electric taxi simulation scenario
=================================

In this scenario, SimFleet includes four types of agents that interact with each other during simulations. These are the
**FleetManager agent**, the **ElectricTaxi agent**, the **TaxiCustomer agent**, and the **ChargingStation agent**.

Description of the Agents
-------------------------

* **TaxiCustomer Agents**

    Function identically to the Taxi simulation scenario.

* **ElectricTaxi Agents**

    The ElectricTaxi agents represent electric vehicles that can transport TaxiCustomer agents from their current positions to their respective destinations.
    Unlike traditional taxis, ElectricTaxi agents have a limited battery capacity and need to monitor their charge levels. When their battery is low, they must
    go to a ChargingStation to recharge before continuing to provide transportation services.

* **ChargingStation Agents**

    The ChargingStation agents represent locations where ElectricTaxi agents can recharge their batteries. These stations allow ElectricTaxi agents to restore their battery level,
    enabling them to continue offering transport services.
    ChargingStations may have limited availability or charging slots, which means ElectricTaxi agents may need to wait if the station is occupied.

* **FleetManager Agent**

    Functions identically to the Taxi simulation scenario.

In the context of SimFleet, a "transport service" involves the following steps:

    #. The ElectricTaxi moves from its current position to the TaxiCustomer's location to pick them up.
    #. The ElectricTaxi transports the TaxiCustomer to their destination.
    #. If the ElectricTaxi's battery is low after the trip, it travels to a ChargingStation to recharge before accepting another request.

The Config file
---------------

The most important fields that the Electric taxi simulation scenario file must include are a taxi customers list, a taxis list and a stations list.

Each taxi customer must include the following fields:

*(Same fields as the Taxi simulation scenario)*

For electric taxis the fields are as follows:

+---------------------------------------------------------------------------------------------+
|  Electric Taxis                                                                             |
+------------------+--------------------------------------------------------------------------+
|  Field           |  Description                                                             |
+==================+==========================================================================+
| class            |   Custom agent file in the format ``module.file.Class``                  |
+------------------+--------------------------------------------------------------------------+
| position         |   Initial coordinates of the transport (optional)                        |
+------------------+--------------------------------------------------------------------------+
| name             |   Name of the transport                                                  |
+------------------+--------------------------------------------------------------------------+
| password         |   Password for registering the transport in the platform (optional)      |
+------------------+--------------------------------------------------------------------------+
| speed            |   Speed of the transport (in meters per second)  (optional)              |
+------------------+--------------------------------------------------------------------------+
| service          |   Type of Service requiring transport                                    |
+------------------+--------------------------------------------------------------------------+
| autonomy         |   The maximum autonomy of the transport (in km)                          |
+------------------+--------------------------------------------------------------------------+
| current_autonomy |   The initial autonomy of the transport (in km)                          |
+------------------+--------------------------------------------------------------------------+
| fleet_type       |   Fleet type that the customer wants to use                              |
+------------------+--------------------------------------------------------------------------+
| optional         |   **fleet**: The fleet manager's JID to be subscribed to (optional)      |
+------------------+--------------------------------------------------------------------------+
| icon             |   Custom icon (in base64 format) to be used by the transport  (optional) |
+------------------+--------------------------------------------------------------------------+
| strategy         |   Custom strategy file in the format ``module.file.Class`` (optional)    |
+------------------+--------------------------------------------------------------------------+
| delay            |   Intentional agent pause in seconds  (optional)                         |
+------------------+--------------------------------------------------------------------------+

For charging stations the fields are as follows:

+--------------------------------------------------------------------------------------+
|  Charging stations                                                                   |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| class       |   Custom agent file in the format ``module.file.Class``                |
+-------------+------------------------------------------------------------------------+
| position    |   Initial coordinates of the customer (optional)                       |
+-------------+------------------------------------------------------------------------+
| name        |   Name of the station                                                  |
+-------------+------------------------------------------------------------------------+
| password    |   Password for registering the station in the platform (optional)      |
+-------------+------------------------------------------------------------------------+
| services    |   **type:** Type of Service offered by the station                     |
|             +------------------------------------------------------------------------+
|             |   **behaviour:** Custom behaviour file in the format module.file.Class |
|             +------------------------------------------------------------------------+
|             |   **slots:** Number of recharge slots available                        |
|             +------------------------------------------------------------------------+
|             |   **args:** Extra arguments such as: **Power**                         |
+-------------+------------------------------------------------------------------------+
| icon        |   Custom icon (in base64 format) to be used by the customer (optional) |
+-------------+------------------------------------------------------------------------+
| strategy    |   Custom strategy file in the format ``module.file.Class`` (optional)  |
+-------------+------------------------------------------------------------------------+
| delay       |   Intentional agent pause in seconds  (optional)                       |
+-------------+------------------------------------------------------------------------+

For fleet managers the fields are as follows:

*(Same fields as the Taxi simulation scenario)*

An example of a config file with four customers, two transports, one fleet manager and two stations:

.. code-block:: json

    {
    "fleets": [
        {
            "password": "secret",
            "name": "fleet1",
            "fleet_type": "electric-taxi"
        }
    ],
    "transports": [
        {
            "class": "simfleet.common.lib.transports.models.electrictaxi.ElectricTaxiAgent",
            "position": [
                39.457364,
                -0.401621
            ],
            "name": "taxi1",
            "password": "secret",
            "speed": 2000,
            "service": "electricity",
            "autonomy": 30,
            "current_autonomy": 5,
            "fleet_type": "electric-taxi",
            "optional": {
                "fleet": "fleet1@localhost"
            },
            "icon": "taxi",
            "delay": 0
        },
        {
            "class": "simfleet.common.lib.transports.models.electrictaxi.ElectricTaxiAgent",
            "name": "taxi2",
            "password": "secret",
            "speed": 2000,
            "service": "electricity",
            "autonomy": 20,
            "current_autonomy": 5,
            "fleet_type": "electric-taxi",
            "optional": {
                "fleet": "fleet1@localhost"
            },
            "icon": "taxi"
        }
    ],
    "customers": [
        {
            "class": "simfleet.common.lib.customers.models.taxicustomer.TaxiCustomerAgent",
            "position": [
                39.494655,
                -0.361639
            ],
            "destination": [
                39.43038,
                -0.354089
            ],
            "name": "customer1",
            "password": "secret",
            "fleet_type": "electric-taxi",
            "delay": 0
        },
        {
            "class": "simfleet.common.lib.customers.models.taxicustomer.TaxiCustomerAgent",
            "name": "customer2",
            "password": "secret",
            "fleet_type": "electric-taxi"
        },
        {
            "class": "simfleet.common.lib.customers.models.taxicustomer.TaxiCustomerAgent",
            "name": "customer3",
            "password": "secret",
            "fleet_type": "electric-taxi",
            "delay": 5
        },
        {
            "class": "simfleet.common.lib.customers.models.taxicustomer.TaxiCustomerAgent",
            "name": "customer4",
            "password": "secret",
            "fleet_type": "electric-taxi",
            "delay": 5
        }
    ],
    "stations": [
        {
            "class": "simfleet.common.lib.stations.models.chargingstation.ChargingStationAgent",
            "position": [
                39.45874369,
                -0.34011479
            ],
            "name": "station1",
            "password": "secret",
            "services": [
                {
                    "type": "electricity",
                    "behaviour": "simfleet.common.lib.stations.models.chargingstation.ChargingService",
                    "slots": 1,
                    "args": {
                        "power": 5
                    }
                }
            ],
            "icon": "electric_station"
        },
        {
            "class": "simfleet.common.lib.stations.models.chargingstation.ChargingStationAgent",
            "name": "station2",
            "password": "secret",
            "services": [
                {
                    "type": "electricity",
                    "behaviour": "simfleet.common.lib.stations.models.chargingstation.ChargingService",
                    "slots": 1,
                    "args": {
                        "power": 10
                    }
                }
            ],
            "icon": "electric_station"
        }
    ],
    "vehicles": [],
    "simulation_name": "electrictaxi",
    "max_time": 200,
    "transport_strategy": "simfleet.common.lib.transports.strategies.electrictaxi.FSMElectricTaxiBehaviour",
    "customer_strategy": "simfleet.common.lib.customers.strategies.taxicustomer.AcceptFirstRequestBehaviour",
    "fleetmanager_strategy": "simfleet.common.lib.fleet.strategies.fleetmanager.DelegateRequestBehaviour",
    "station_strategy": "simfleet.common.lib.stations.models.chargingstation.ChargingService",
    "fleetmanager_name": "fleetmanager",
    "fleetmanager_password": "fleetmanager_passwd",
    "directory_name": "directory",
    "directory_password": "directory_passwd",
    "host": "localhost",
    "http_port": 9000,
    "http_ip": "localhost"
    }

This configuration file includes:

    * One ElectricTaxi with a fixed position and one with a random position.
    * Low autonomy for both ElectricTaxis.
    * One TaxiCustomer with fixed origin and destination coordinates.
    * Three TaxiCustomers with random positions.
    * Two ChargingStations, one with a fixed position and one with a random position.

Bus simulation scenario
=======================

In this scenario, SimFleet includes four types of agents that interact with each other during simulations. These are the **FleetManager agent**,
the **Bus agent**, the **BusCustomer agent**, and the **BusStop agent**.


Description of the Agents
-------------------------

* **BusCustomer Agents**

    The BusCustomer agents represent people who need to travel from one location in the city (their "current location") to another (their "destination").
    To achieve this, each BusCustomer agent requests a transport service. Unlike TaxiCustomer agents, BusCustomer agents have the option to walk to the
    nearest BusStop to catch a bus. Once they are transported to their destination, they enter a final state and end their execution.

* **Bus Agents**

    The Bus agents represent public transport vehicles that can pick up and transport BusCustomer agents along predefined routes. Buses stop at designated BusStops to pick up and drop off passengers.
    Each Bus agent operates based on a fixed route, and they only provide transport services to BusCustomer agents who are waiting at BusStops.

* **BusStop Agents**

    The BusStop agents represent designated stopping points where buses can pick up and drop off BusCustomer agents. BusCustomers can move to the nearest BusStop to catch a bus.
    BusStops are essential for coordinating the pickup and drop-off of passengers.

* **FleetManager Agent**

    The FleetManager acts as a central system that manages the fleet of buses, ensuring that they operate smoothly and follow their routes.
    In order to do so, the FleetManager has a registration protocol by which Bus agents subscribe to the Fleet Manager that represents their fleet.

In the context of SimFleet, a "transport service" for buses involves:

    #. The Bus agent following its predefined route.
    #. Picking up BusCustomer agents waiting at BusStops.
    #. Dropping off BusCustomer agents at BusStops near their destinations.

The Config file
---------------

The most important fields that the Bus simulation scenario file must include are a BusCustomers list, a Buses list, a BusStops list and a Lines list.
Each bus customer must include the following fields:

+--------------------------------------------------------------------------------------+
|  Bus Customers                                                                       |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| class       |   Custom agent file in the format ``module.file.Class``                |
+-------------+------------------------------------------------------------------------+
| position    |   Initial coordinates of the customer                                  |
+-------------+------------------------------------------------------------------------+
| destination |   Destination coordinates of the customer                              |
+-------------+------------------------------------------------------------------------+
| name        |   Name of the customer                                                 |
+-------------+------------------------------------------------------------------------+
| password    |   Password for registering the customer in the platform (optional)     |
+-------------+------------------------------------------------------------------------+
| speed       |   Speed of the customer (in meters per second)  (optional)             |
+-------------+------------------------------------------------------------------------+
| line        |   Bus line that the customer wants to use                              |
+-------------+------------------------------------------------------------------------+
| fleet_type  |   Fleet type that the customer wants to use                            |
+-------------+------------------------------------------------------------------------+
| icon        |   Custom icon (in base64 format) to be used by the customer (optional) |
+-------------+------------------------------------------------------------------------+
| strategy    |   Custom strategy file in the format ``module.file.Class``  (optional) |
+-------------+------------------------------------------------------------------------+
| delay       |   Intentional agent pause in seconds  (optional)                       |
+-------------+------------------------------------------------------------------------+

.. note::
    If the **speed** field is not used, the customer's position and destination must match the origin and destination positions of the bus stops.

For buses the fields are as follows:

+---------------------------------------------------------------------------------------------+
|  Buses                                                                                      |
+------------------+--------------------------------------------------------------------------+
|  Field           |  Description                                                             |
+==================+==========================================================================+
| class            |   Custom agent file in the format ``module.file.Class``                  |
+------------------+--------------------------------------------------------------------------+
| position         |   Initial coordinates of the transport                                   |
+------------------+--------------------------------------------------------------------------+
| name             |   Name of the transport                                                  |
+------------------+--------------------------------------------------------------------------+
| password         |   Password for registering the transport in the platform (optional)      |
+------------------+--------------------------------------------------------------------------+
| speed            |   Speed of the transport (in meters per second)                          |
+------------------+--------------------------------------------------------------------------+
| line             |   Bus line that the transport wants to use                               |
+------------------+--------------------------------------------------------------------------+
| capacity         |   Capacity of customer that can be transported                           |
+------------------+--------------------------------------------------------------------------+
| fleet_type       |   Fleet type that the customer wants to use                              |
+------------------+--------------------------------------------------------------------------+
| optional         |   **fleet**: The fleet manager's JID to be subscribed to                 |
+------------------+--------------------------------------------------------------------------+
| icon             |   Custom icon (in base64 format) to be used by the transport  (optional) |
+------------------+--------------------------------------------------------------------------+
| strategy         |   Custom strategy file in the format ``module.file.Class``  (optional)   |
+------------------+--------------------------------------------------------------------------+
| delay            |   Intentional agent pause in seconds  (optional)                         |
+------------------+--------------------------------------------------------------------------+

.. note::
    The bus agent's position must match one of the stops on its assigned line for correct operation.

For bus stops the fields are as follows:

+--------------------------------------------------------------------------------------+
|  Bus stops                                                                           |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| class       |   Custom agent file in the format ``module.file.Class``                |
+-------------+------------------------------------------------------------------------+
| position    |   Initial coordinates of the customer                                  |
+-------------+------------------------------------------------------------------------+
| id          |   Id of the station                                                    |
+-------------+------------------------------------------------------------------------+
| name        |   Name of the station                                                  |
+-------------+------------------------------------------------------------------------+
| password    |   Password for registering the station in the platform (optional)      |
+-------------+------------------------------------------------------------------------+
| lines       |   Bus line that the bus stop wants to use                              |
+-------------+------------------------------------------------------------------------+
| icon        |   Custom icon (in base64 format) to be used by the customer (optional) |
+-------------+------------------------------------------------------------------------+
| delay       |   Intentional agent pause in seconds  (optional)                       |
+-------------+------------------------------------------------------------------------+

For bus lines the fields are as follows:

+--------------------------------------------------------------------------------------+
|  Bus lines                                                                           |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| id          |   Id of the line                                                       |
+-------------+------------------------------------------------------------------------+
| line_type   |   Line type that the bus want to use                                   |
+-------------+------------------------------------------------------------------------+
| stops       |   Stop list that the line wants to use                                 |
+-------------+------------------------------------------------------------------------+

.. note::
    The **line_type** field supports three types of routes:

        1) **circular:** The bus choose first stop of the route as next destination (circular routes).
        2) **end-to-end:** The bus inverse stop list and choose previous destination as next destination (end-to-end lines).
        3) **teleport:** The bus "teleport" to first stop and choose next destination.

For fleet managers the fields are as follows:

*(Same fields as the Taxi simulation scenario)*

An example of a config file with two customers, two transports, one fleet manager and eleven stops:

.. code-block:: json

    {
    "fleets": [
        {
            "password": "secret",
            "name": "fleet1",
            "fleet_type": "bus"
        }
    ],
    "transports": [
        {
            "class": "simfleet.common.lib.transports.models.bus.BusAgent",
            "position": [
                39.4783129,
                -0.3476785
            ],
            "name": "bus1",
            "password": "secret",
            "speed": 1500,
            "line": 18,
            "capacity": 60,
            "fleet_type": "bus",
            "optional": {
                "fleet": "fleet1@localhost"
            },
            "icon": "bus",
            "delay": 0
        },
        {
            "class": "simfleet.common.lib.transports.models.bus.BusAgent",
            "position": [
                39.4541141,
                -0.3689441
            ],
            "name": "bus2",
            "password": "secret",
            "speed": 1500,
            "line": 18,
            "capacity": 60,
            "fleet_type": "bus",
            "optional": {
                "fleet": "fleet1@localhost"
            },
            "icon": "bus"
        }
    ],
    "customers": [
        {
	        "class": "simfleet.common.lib.customers.models.buscustomer.BusCustomerAgent",
            "position": [
                39.4570888,
                -0.3561952
            ],
            "destination": [
                39.4819241,
                -0.3501210
            ],
            "name": "buscustomer1",
            "password": "secret",
            "speed": 400,
	        "line": 18,
            "fleet_type": "bus",
            "delay": 5
        },
        {
	        "class": "simfleet.common.lib.customers.models.buscustomer.BusCustomerAgent",
            "position": [
                39.4653021,
                -0.3595032
            ],
            "destination": [
                39.4540184,
                -0.3727660
            ],
	        "line": 18,
            "name": "buscustomer2",
            "password": "secret",
            "speed": 400,
            "fleet_type": "bus",
            "delay": 5
        }
    ],
    "stops": [
        {
            "class": "simfleet.common.lib.stations.models.busstop.BusStopAgent",
            "position": [
                39.4541141,
                -0.3689441
            ],
            "id": 1,
            "name": "Parc Central de Bombers",
            "password": "secret",
            "lines": [
                18
            ],
            "icon": "bus_stop"
        },
        {
            "class": "simfleet.common.lib.stations.models.busstop.BusStopAgent",
            "position": [
                39.4582910,
                -0.3602457
            ],
            "id": 2,
            "name": "Escultor J. Capuz (imparell) - la Plata",
            "password": "secret",
            "lines": [
                18
            ],
            "icon": "bus_stop"
        },
        {
            "class": "simfleet.common.lib.stations.models.busstop.BusStopAgent",
            "position": [
                39.4613975,
                -0.3623484
            ],
            "id": 3,
            "name": "Centre d'Especialitats Montolivet",
            "password": "secret",
            "lines": [
                18
            ],
            "icon": "bus_stop"
        },
        {
            "class": "simfleet.common.lib.stations.models.busstop.BusStopAgent",
            "position": [
                39.4645590,
                -0.3576047
            ],
            "id": 4,
            "name": "Eduard Bosca - Balears",
            "password": "secret",
            "lines": [
                18
            ],
            "icon": "bus_stop"
        },
        {
            "class": "simfleet.common.lib.stations.models.busstop.BusStopAgent",
            "position": [
                39.4742214,
                -0.3528733
            ],
            "id": 5,
            "name": "Cardenal Benlloch - Dr. Vicente Pallares",
            "password": "secret",
            "lines": [
                18
            ],
            "icon": "bus_stop"
        },
        {
            "class": "simfleet.common.lib.stations.models.busstop.BusStopAgent",
            "position": [
                39.4801655,
                -0.3471697
            ],
            "id": 6,
            "name": "Tarongers - Facultat de Magisteri",
            "password": "secret",
            "lines": [
                18
            ],
            "icon": "bus_stop"
        },
        {
            "class": "simfleet.common.lib.stations.models.busstop.BusStopAgent",
            "position": [
                39.4783129,
                -0.3476785
            ],
            "id": 7,
            "name": "Albalat dels Tarongers - Vinalopo",
            "password": "secret",
            "lines": [
                18
            ],
            "icon": "bus_stop"
        },
        {
            "class": "simfleet.common.lib.stations.models.busstop.BusStopAgent",
            "position": [
                39.4741881,
                -0.3531690
            ],
            "id": 8,
            "name": "Cardenal Benlloch - Ciutat de Mula",
            "password": "secret",
            "lines": [
                18
            ],
            "icon": "bus_stop"
        },
        {
            "class": "simfleet.common.lib.stations.models.busstop.BusStopAgent",
            "position": [
                39.4646234,
                -0.3578487
            ],
            "id": 9,
            "name": "Eduard Bosca - Passeig de l'Albereda",
            "password": "secret",
            "lines": [
                18
            ],
            "icon": "bus_stop"
        },
        {
            "class": "simfleet.common.lib.stations.models.busstop.BusStopAgent",
            "position": [
                39.4603469,
                -0.3618095
            ],
            "id": 10,
            "name": "Escultor J. Capuz - Pere Aleixandre",
            "password": "secret",
            "lines": [
                18
            ],
            "icon": "bus_stop"
        },
        {
            "class": "simfleet.common.lib.stations.models.busstop.BusStopAgent",
            "position": [
                39.4543455,
                -0.3691169
            ],
            "id": 11,
            "name": "la Plata - Alberola",
            "password": "secret",
            "lines": [
                18
            ],
            "icon": "bus_stop"
        }
    ],
    "lines": [
        {
            "id": 18,
            "line_type": "circular",
            "stops": [
                [
                39.4541141,
                -0.3689441
            	],
                [
                39.4582910,
                -0.3602457
            	],
            	[
                39.4613975,
                -0.3623484
            	],
            	[
                39.4645590,
                -0.3576047
            	],
            	[
                39.4742214,
                -0.3528733
            	],
            	[
                39.4801655,
                -0.3471697
            	],
            	[
                39.4783129,
                -0.3476785
            	],
            	[
                39.4741881,
                -0.3531690
            	],
            	[
                39.4646234,
                -0.3578487
            	],
            	[
                39.4603469,
                -0.3618095
            	],
            	[
                39.4543455,
                -0.3691169
            	]
             ]
         }
     ],
    "vehicles": [],
    "simulation_name": "bus",
    "max_time": 200,
    "transport_strategy": "simfleet.common.lib.transports.strategies.bus.FSMBusBehaviour",
    "customer_strategy": "simfleet.common.lib.customers.strategies.buscustomer.FSMBusCustomerBehaviour",
    "fleetmanager_name": "fleetmanager",
    "fleetmanager_password": "fleetmanager_passwd",
    "host": "localhost",
    "http_port": 9000,
    "http_ip": "localhost"
    }

This configuration file includes:

    * Two Buses with a fixed position.
    * Two BusCustomer with fixed origin and destination positions.
    * Eleven BusStops with fixed positions.
    * One Line with eleven BusStop.

Another simulation scenario
===========================

SimFleet includes vehicle agents to create an autonomous vehicle simulation scenario.

Description of the Agent
-------------------------

* **Vehicle Agents**

    These agents can autonomously travel from an origin point to a destination. They can either perform a single trip or continuously travel to new random destinations in a cyclic manner.


The Config file
---------------

The most important field that the autonomous vehicle simulation scenario file must include is a Vehicles list.
Each vehicles must include the following fields:

+--------------------------------------------------------------------------------------+
|  Vehicles                                                                            |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| class       |   Custom agent file in the format ``module.file.Class``                |
+-------------+------------------------------------------------------------------------+
| position    |   Initial coordinates of the customer (optional)                       |
+-------------+------------------------------------------------------------------------+
| destination |   Destination coordinates of the customer (optional)                   |
+-------------+------------------------------------------------------------------------+
| name        |   Name of the customer                                                 |
+-------------+------------------------------------------------------------------------+
| password    |   Password for registering the customer in the platform (optional)     |
+-------------+------------------------------------------------------------------------+
| speed       |   Speed of the vehicle (in meters per second)  (optional)              |
+-------------+------------------------------------------------------------------------+
| icon        |   Custom icon (in base64 format) to be used by the customer (optional) |
+-------------+------------------------------------------------------------------------+
| strategy    |   Custom strategy file in the format ``module.file.Class``  (optional) |
+-------------+------------------------------------------------------------------------+
| delay       |   Intentional agent pause in seconds  (optional)                       |
+-------------+------------------------------------------------------------------------+

An example of a config file with two autonomous vehicles:

.. code-block:: json

    {
    "fleets": [],
    "transports": [],
    "customers": [],
    "stations": [],
    "vehicles": [
        {
            "class": "simfleet.common.lib.vehicles.models.vehicle.VehicleAgent",
            "strategy": "simfleet.common.lib.vehicles.strategies.vehicle.FSMCycleVehicleBehaviour",
            "position": [
                39.457364,
                -0.401621
            ],
            "destination": [
                39.45333818,
                -0.33223699
            ],
            "name": "drone1",
            "password": "secret",
            "speed": 2000,
            "icon": "drone"
        },
        {
            "class": "simfleet.common.lib.vehicles.models.vehicle.VehicleAgent",
            "strategy": "simfleet.common.lib.vehicles.strategies.vehicle.FSMOneShotVehicleBehaviour",
            "name": "drone2",
            "password": "secret",
            "speed": 2000,
            "icon": "drone"
        }
	],
    "simulation_name": "drone",
    "max_time": 30,
    "host": "localhost",
    "http_port": 9000

    }

This configuration file includes:

    * One autonomous vehicle with a fixed initial position and destination, following a cyclic behavior.
    * One autonomous vehicle without a specified initial position or destination, performing a one-shot behavior.


Command-line interface
======================

In the QuickStart guide, we covered how to quickly get started with SimFleet using the graphical interface. In this section, we will explore
in greater detail how to use the **Command-Line Interface (CLI)** to configure and launch transport simulation scenarios directly from the command line.
This guide explains the usage and available options for the ``simfleet`` command, making it easier to start simulations, debug processes, and save results.

.. hint::
    To view the options available in SimFleet's command line interface, use the following command ``--help``

This will display the following output:

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


The simfleet command initializes and starts simulations using custom configurations and customizable options. You can specify simulation parameters such as the execution name,
output file, maximum simulation time, and verbosity level. This flexibility allows for efficient control and debugging of your SimFleet simulations.


Examples of CLI Execution
-------------------------

* **Example 1: Basic Simulation with Output File**

.. code-block:: console

    $ simfleet --config myconfig.json --name "My Simulation" --output results.json

In this example, the simulation uses the configuration file ``myconfig.json``, sets the simulation name to "My Simulation", and saves all the simulation events to a file named ``results.json``.
This setup is ideal for running a simple simulation and storing the output for later analysis. The output of the simulation captures a series of events generated by agents as they execute
their strategies. Each event represents a key action within the simulation.

An example of the output would be:

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

* **Example 2: Simulation with Maximum Verbosity**

.. code-block:: console

    $ simfleet --config myconfig.json --name "My Simulation" --vvvv

This example uses the configuration file ``myconfig.json`` and sets the simulation name to "My Simulation". The ``--vvvv`` option enables the highest verbosity level (level 4), providing
detailed debug information during execution. This is particularly useful for troubleshooting and understanding the internal workings of the simulation. For instance, ``-v`` represents
**DEBUG** verbosity, while ``-vvvv`` displays the most detailed internal messages of the platform.


.. note::
    To start the simulation scenario in the GUI while running simulator from the CLI, use the web interface address displayed in the output, such as:

    .. code-block:: console

        2024-11-25 16:29:07.229 | INFO     | simfleet.simulator:setup:110 - Web interface running at http://127.0.0.1:9000/app

    This address is (in most cases): `http://127.0.0.1:9000/app <http://127.0.0.1:9000/app>`_

* **Example 3: Simulation with Time Limit and Autorun**

.. code-block:: console

    $ simfleet --config myconfig.json --name "My Simulation" --output results.json --max-time 100 --autorun

In this example, the configuration file ``myconfig.json`` is used, and the simulation is named "My Simulation". The ``--autorun`` flag ensures the simulation starts automatically
as soon as the agents are ready. Additionally, the ``--max-time 100`` option limits the simulation duration to 100 seconds. The simulation events are saved to ``results.json``,
making it easy to review the results once the simulation concludes.

