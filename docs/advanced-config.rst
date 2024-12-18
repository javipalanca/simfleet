============
Usage Manual
============

Using SimFleet is straightforward and can be done by running the application from the command line. There are two modes of use:
a **command-line interface (CLI)** and a **web-based graphical interface (GUI)**. You can execute simulations purely through the command
line or use the simpler and more intuitive graphical interface.

SimFleet supports a wide variety of urban mobility scenarios, as the simulator includes predefined agents and strategies. In this section,
we will explore how to use both interfaces of advance mode and the different simulation scenarios available.


The Config file: Structure
==========================

The configuration file for a SimFleet simulation follows a JSON structure that defines the agents, simulation settings, and strategies used. Here's an explanation of each field:

+--------------------------------------------------------------------------------------+
|  Agents and Their Lists                                                              |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| fleets      |   A list of fleet manager agents                                       |
+-------------+------------------------------------------------------------------------+
| transports  |   A list of transport agents                                           |
+-------------+------------------------------------------------------------------------+
| customers   |   A list of customer agents                                            |
+-------------+------------------------------------------------------------------------+
| stations    |   A list of mobility infrastructure agents                             |
+-------------+------------------------------------------------------------------------+
| stops       |   A list of bus stop agents                                            |
+-------------+------------------------------------------------------------------------+
| lines       |   A list of predefined bus lines or routes that buses follow           |
+-------------+------------------------------------------------------------------------+
| vehicles    |   A list of autonomous vehicle agents                                  |
+-------------+------------------------------------------------------------------------+



+---------------------------------------------------------------------------------------------+
|  Simulation Settings                                                                        |
+------------------+--------------------------------------------------------------------------+
|  Field           |  Description                                                             |
+==================+==========================================================================+
| simulation_name  |   The name of the simulation scenario                                    |
+------------------+--------------------------------------------------------------------------+
| max_time         |   The maximum duration (in seconds) for which the simulation will run    |
+------------------+--------------------------------------------------------------------------+
| coords           |   The initial geographic coordinates for the simulation map              |
+------------------+--------------------------------------------------------------------------+
| zoom             |   The initial zoom level of the simulation map                           |
+------------------+--------------------------------------------------------------------------+

.. note::
    The **coords** field can use the name of a city, town, neighbourhood or a specific coordinate, e.g. ‘Valencia’ or [39.4697065, -0.3763353]. This reference point centres the simulation on the map.
    In addition, the **zoom** field controls the scale of the bounding box for the random creation of positions of an agent on the map.


+--------------------------------------------------------------------------------------------------+
|  Default Strategies                                                                              |
+-----------------------+--------------------------------------------------------------------------+
|  Field                |  Description                                                             |
+=======================+==========================================================================+
| transport_strategy    |   The behavior strategy used by transport agents                         |
+-----------------------+--------------------------------------------------------------------------+
| customer_strategy     |   The behavior strategy used by customer agents                          |
+-----------------------+--------------------------------------------------------------------------+
| fleetmanager_strategy |   The behavior strategy used by fleet manager                            |
+-----------------------+--------------------------------------------------------------------------+
| directory_strategy    |   The behavior strategy used by directory agent                          |
+-----------------------+--------------------------------------------------------------------------+
| station_strategy      |   The behavior strategy used by charging stations                        |
+-----------------------+--------------------------------------------------------------------------+
| vehicle_strategy      |   The behavior strategy used by vehicle agents                           |
+-----------------------+--------------------------------------------------------------------------+


+--------------------------------------------------------------------------------------------------+
|  Metrics, Credentials and Network Settings                                                       |
+-----------------------+--------------------------------------------------------------------------+
|  Field                |  Description                                                             |
+=======================+==========================================================================+
| mobility_metrics      |   Custom class used to collect mobility statistics during the simulation |
+-----------------------+--------------------------------------------------------------------------+
| fleetmanager_name     |   Name for registering the fleet manager agent in the XMPP server        |
+-----------------------+--------------------------------------------------------------------------+
| fleetmanager_password |   Password for registering the fleet manager agent in the XMPP server    |
+-----------------------+--------------------------------------------------------------------------+
| directory_name        |   Name for registering the directory agent in the XMPP server            |
+-----------------------+--------------------------------------------------------------------------+
| directory_password    |   Password for registering the directory agent in the XMPP server        |
+-----------------------+--------------------------------------------------------------------------+
| route_host            |   The URL of the OSRM routing service used for calculating optimal routes|
+-----------------------+--------------------------------------------------------------------------+
| host                  |   The XMPP host address where the simulation platform is running         |
+-----------------------+--------------------------------------------------------------------------+
| xmpp_port             |   The port for XMPP communication                                        |
+-----------------------+--------------------------------------------------------------------------+
| http_port             |   The port for the HTTP server used in the simulation (GUI)              |
+-----------------------+--------------------------------------------------------------------------+
| http_ip               |   IP address for the HTTP server used in the simulation (GUI)            |
+-----------------------+--------------------------------------------------------------------------+

This structure provides a flexible framework for creating different scenarios. An example of a config file structure:

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
    "coords": Valencia,
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

This modular approach allows for easy customization and expansion to fit diverse simulation needs.

Taxi simulation scenario
========================

In this scenario, SimFleet there are three types of agent that interact among them during simulations. These are the **FleetManager agent**,
the **Taxi agent**, and the **TaxiCustomer agent**.


Description of the Agents
-------------------------

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
| class       |   Custom agent file in the format module.file.Class                    |
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
| strategy    |   Custom strategy file in the format module.file.Class  (optional)     |
+-------------+------------------------------------------------------------------------+
| delay       |   Intentional agent pause in seconds  (optional)                       |
+-------------+------------------------------------------------------------------------+

For taxis the fields are as follows:

+---------------------------------------------------------------------------------------------+
|  Taxi                                                                                       |
+------------------+--------------------------------------------------------------------------+
|  Field           |  Description                                                             |
+==================+==========================================================================+
| class            |   Custom agent file in the format module.file.Class                      |
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
| strategy         |   Custom strategy file in the format module.file.Class  (optional)       |
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
| strategy    |   Custom strategy file in the format module.file.Class  (optional)     |
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

    The TaxiCustomer agents represent people that need to go from one location in the city (their "current location") to another (their "destination").
    To achieve this, each TaxiCustomer agent requests a transport service. Once they are transported to their destination, they reach their final state and end their execution.

* **ElectricTaxi Agents**

    The ElectricTaxi agents represent electric vehicles that can transport TaxiCustomer agents from their current positions to their respective destinations.
    Unlike traditional taxis, ElectricTaxi agents have a limited battery capacity and need to monitor their charge levels. When their battery is low, they must
    go to a ChargingStation to recharge before continuing to provide transportation services.

* **ChargingStation Agents**

    The ChargingStation agents represent locations where ElectricTaxi agents can recharge their batteries. These stations allow ElectricTaxi agents to restore their battery level,
    enabling them to continue offering transport services.
    ChargingStations may have limited availability or charging slots, which means ElectricTaxi agents may need to wait if the station is occupied.

* **FleetManager Agent**

    The FleetManager Agent is responsible for putting in contact the TaxiCustomer agents that need a transport service, and the Taxi
    agents that may be available to offer these services. In short, the FleetManager Agent acts like a transport call center, accepting
    the incoming requests from customers (TaxiCustomer agents) and forwarding these requests to the (appropriate) Taxi agents.
    In order to do so, the FleetManager has a registration protocol by which Taxi agents subscribe to the Fleet Manager
    that represents their fleet. This is automatically done when a Taxi agent is started.

In the context of SimFleet, a "transport service" involves the following steps:

    #. The ElectricTaxi moves from its current position to the TaxiCustomer's location to pick them up.
    #. The ElectricTaxi transports the TaxiCustomer to their destination.
    #. If the ElectricTaxi's battery is low after the trip, it travels to a ChargingStation to recharge before accepting another request.

The Config file
---------------

The most important fields that the Electric taxi simulation scenario file must include are a taxi customers list, a taxis list and a stations list.
Each taxi customer must include the following fields:

+--------------------------------------------------------------------------------------+
|  Taxi Customers                                                                      |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| class       |   Custom agent file in the format module.file.Class                    |
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
| strategy    |   Custom strategy file in the format module.file.Class  (optional)     |
+-------------+------------------------------------------------------------------------+
| delay       |   Intentional agent pause in seconds  (optional)                       |
+-------------+------------------------------------------------------------------------+

For electric taxis the fields are as follows:

+---------------------------------------------------------------------------------------------+
|  Electric Taxis                                                                             |
+------------------+--------------------------------------------------------------------------+
|  Field           |  Description                                                             |
+==================+==========================================================================+
| class            |   Custom agent file in the format module.file.Class                      |
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
| strategy         |   Custom strategy file in the format module.file.Class  (optional)       |
+------------------+--------------------------------------------------------------------------+
| delay            |   Intentional agent pause in seconds  (optional)                         |
+------------------+--------------------------------------------------------------------------+

For charging stations the fields are as follows:

+--------------------------------------------------------------------------------------+
|  Charging stations                                                                   |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| class       |   Custom agent file in the format module.file.Class                    |
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
| strategy    |   Custom strategy file in the format module.file.Class  (optional)     |
+-------------+------------------------------------------------------------------------+
| delay       |   Intentional agent pause in seconds  (optional)                       |
+-------------+------------------------------------------------------------------------+

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
| strategy    |   Custom strategy file in the format module.file.Class  (optional)     |
+-------------+------------------------------------------------------------------------+

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
| class       |   Custom agent file in the format module.file.Class                    |
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
| strategy    |   Custom strategy file in the format module.file.Class  (optional)     |
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
| class            |   Custom agent file in the format module.file.Class                      |
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
| strategy         |   Custom strategy file in the format module.file.Class  (optional)       |
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
| class       |   Custom agent file in the format module.file.Class                    |
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
| strategy    |   Custom strategy file in the format module.file.Class  (optional)     |
+-------------+------------------------------------------------------------------------+

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
| class       |   Custom agent file in the format module.file.Class                    |
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
| strategy    |   Custom strategy file in the format module.file.Class  (optional)     |
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

After installing SimFleet open a command-line and type ``simfleet --config config_file.json``. This starts a
simulator with the configuration specified at the JSON file and runs the simulator agent. The console will output the default logging
information and you can terminate the simulator by pressing ``Ctrl+C``. When you terminate the simulator the results of
the simulations are printed.

Despues de instalar Simfleet podemos ejecutar nuestro archivo de configuración

.. code-block:: console

    $ simfleet --config vehicles.json
    2024-11-25 16:35:15.429 | INFO     | simfleet.config.settings:load_config:134 - Reading config vehicles.json
    2024-11-25 16:35:15.710 | INFO     | simfleet.simulator:__init__:89 - Starting SimFleet (simulation_drone)
    2024-11-25 16:35:15.722 | INFO     | simfleet.simulator:load_icons:467 - Reading icons /simfleet/templates/data/img_drones.json
    2024-11-25 16:35:15.934 | INFO     | simfleet.common.agents.directory:setup:63 - Directory agent directory running
    2024-11-25 16:35:15.935 | INFO     | simfleet.simulator:__init__:119 - Creating 0 managers, 0 transports, 0 customers, 0 stations and 2 vehicles.
    2024-11-25 16:35:15.935 | INFO     | simfleet.simulator:load_scenario:169 - Loading scenario...
    2024-11-25 16:35:15.937 | INFO     | simfleet.simulator:load_scenario:192 - Loading lines...
    2024-11-25 16:35:16.061 | SUCCESS  | simfleet.simulator:gather_batch:258 - All agents gathered
    2024-11-25 16:35:16.292 | INFO     | simfleet.simulator:setup:133 - Simulator agent running
    2024-11-25 16:35:16.295 | INFO     | simfleet.simulator:setup:151 - Web interface running at http://localhost:9000/app


    ^C

    2024-11-25 16:36:26.108 | INFO     | simfleet.simulator:stop:258 -
    Terminating... (17.3 seconds elapsed)

However, if you don't use some options when running the simulator there will be no default transports nor customers. That's
why stats are empty. To run a simulation with some parameters you must fill a configuration file where the simulation scenario
is defined.

To show he command line interface options you can enter the ``--help`` command:

.. code-block:: console

    $ simfleet --help

    Usage: simfleet [OPTIONS]

  Console script for SimFleet.

    Options:
      -n, --name TEXT              Name of the simulation execution.
      -o, --output TEXT            Filename to save simulation results.
      -of, --oformat [json|excel]  Output format used to save simulation results.
                                   (default: json)
      -mt, --max-time INTEGER      Maximum simulation time (in seconds).
      -r, --autorun                Run simulation as soon as the agents are ready.
      -c, --config TEXT            Filename of JSON file with initial config.
      -v, --verbose                Show verbose debug level: -v level 1, -vv level
                                   2, -vvv level 3, -vvvv level 4
      --help                       Show this message and exit.


The output of a simulation shows some statistics of the simulation, with the `Average Total Time`, which
represents the average time of customers from the moment they request a transport until they are delivered to their
destination, and the `Average Waiting Time`, which is the average time of customers from requesting a transport to being
picked up. This information is also shown for each customer along with their status at the end of the simulation.

In the case of transports, the shown information includes the number of assignments of each transport (how many customers it has
delivered), the total distance it has traveled and its final status.

This information is going to be useful for the development of new strategies that improve the system balancing or for
debugging errors if a transport or a customer gets stuck or any other unexpected situation occurs.

The last but no less important option is the verbosity option. It allows you to specify how verbose you want the
simulator to be. The number of ``v`` letters you pass to the option indicates the level of verbosity (e.g. ``-v`` is
**DEBUG** verbosity and ``-vvvv`` is the highest level of verbosity where the internal messages of the platform are
shown).

Saving the simulation results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to store the results of simulation in a file you may use the ``--output`` option (or ``-o``) to specify the
name of the file where the simulation results will be saved. The ``--oformat`` (``-of``) allows you to choose the output
format between json (default) or excel. It is also useful to use the ``--name`` (or ``-n``) to name the simulation.

Example:

.. code-block:: console

    $ simfleet --config myconfig.json --name "My Simulation" --output results.xls --oformat excel

Graphical User Interface
========================
A much more user-friendly way to use SimFleet is through the built-in graphical user interface. This interface is
accessed via any web browser and is designed as a viewer for your running simulations.
To open it just visit the address shown on the screen when you run the simulator and access that website.

.. hint::
    The Simulator agent is who raises the GUI and shows the address in the console output:

    .. code-block:: console

        2015-10-21 16:29:07.229 | INFO     | simfleet.simulator:setup:110 - Web interface running at http://127.0.0.1:9000/app

    This address is (in most cases): `http://127.0.0.1:9000/app <http://127.0.0.1:9000/app>`_

Once you visit the GUI address you see an interface like this:

.. figure:: images/screen3.png
    :align: center
    :alt: GUI at startup

    GUI at startup

In the GUI you can see a map of the city on the right and a Control Panel with various options on the left:

#. A **Run** button that starts the simulation.

#. A **Clear** button to stop and reset the simulation.

#. Stats of the waiting time and total time of the simulation in real time.

#. A **Download** button to get the stats of the simulation in excel or json format.

#. A collapsable tree view with the transports and customers that are included in the simulation, with a color bullet that indicates their current status.

If the **Run** button is pressed the simulation shows how the transports move to the customers and deliver them to their
destinations.

.. figure:: images/madrid.png
    :align: center
    :alt: Simulation in progress

    Simulation in progress

Notice that when a transport picks up a customer, the customer's icon disappears from the map view (since it
is inside the transport) and is no longer viewed (it's also not shown when it arrives to its destination). However, you can
check at any time your customers status in the tree view of the Control Panel.

The code colors in the tree view indicate the status of a transport or a customer. The legend of colors is as follows:

+--------------------------------------+---------------------------------+
|              Transports              |            Customers            |
+--------------+-----------------------+---------------+-----------------+
|  Bullet      |     Status            |  Bullet       |     Status      |
+==============+=======================+===============+=================+
| |positive|   | WAITING               | |active|      |  WAITING        |
+--------------+-----------------------+---------------+-----------------+
| |inter|      | WAITING FOR APPROVAL  | |inter|       |  ASSIGNED       |
+--------------+-----------------------+---------------+-----------------+
| |interpulse| | MOVING TO CUSTOMER    | |activepulse| |  IN TRANSPORT   |
+--------------+-----------------------+---------------+-----------------+
| |activepulse|| MOVING TO DESTINATION | |positive|    |  IN DESTINATION |
+--------------+-----------------------+---------------+-----------------+



.. |positive| image:: images/positive2.png
                :width: 36px

.. |inter| image:: images/inter2.png
                :width: 36px

.. |interpulse| image:: images/interpulse2.png
                :width: 36px

.. |activepulse| image:: images/activepulse2.png
                :width: 36px

.. |active| image:: images/active2.png
                :width: 36px

.. hint::
    Every time than a bullet is pulsing means that the agent is moving.


When a transport is moving it's also shown in the GUI the path that the transport is following. The color of the path indicates the
type of movement that the transport is doing. A yellow path indicates that the transport is going to pick up the customer.
On the other hand, a blue path indicates that the transport is taking the customer to his destination.


.. note::
    A simulation is finished when all transports are free (and waiting for new customers) and all customers are in their
    destinations (i.e. all bullets are green).
