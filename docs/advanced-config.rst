============
Usage Manual
============

The SimFleet platform employs JSON configuration files to define simulation scenarios. Once a configuration file has been
defined, its simulation can be launched by running the application from the console. SimFleet can be executed in two modes:
a **command-line interface (CLI)** and a **web-based graphical interface (GUI)**. You may execute simulations purely through the command
line or use the simpler and more intuitive graphical interface.

In this section, the structure and usage of SimFleet configuration files is described. First, we focus on the general structure.
Then, we present the currently included transportation modes and describe how to setup a simulation using its agents. Finally,
we indicate how to use **command-line interface (CLI)** to launch simulation scenarios with different execution options.


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

SimFleet is designed to give its users the tools to easily setup and execute complex transportation scenarios. In addition,
users may extend the provided agents to create new versions that adapt to their needs. However, the platform currently
provides two predefined transportation modes: Taxi/Electric Taxi service, and Urban Bus. Following, the agents employed in
each of the modes are briefly described, together with the necessary attributes to define them in a configuration file.

Taxi service simulation
-----------------------

This transportation mode represents a taxi service coordinated by a centralised manager. Customers of the service send
travel requests to the manager who, in turn, broadcasts them to all available transports in its fleet. Upon the reception
of a customer request, taxi agents may choose to serve such the issuing customer, which emcompases picking them up at their
current position and driving them to their destination. The scenario features three agents: A **FleetManager Agent**,
the **Taxi Agents**, and the **TaxiCustomer Agents**.


Agent description
^^^^^^^^^^^^^^^^^

* **TaxiCustomer Agents**

    TaxiCustomer agents represent people that need to go from one location of the city (their "current location") to
    another (their "destination").
    For doing so, each customer requests a single transport service and, once it is delivered to its destination,
    it ends its execution.

* **Taxi Agents**

    The Taxi agents represent vehicles which can transport TaxiCustomer agents from their current positions to their respective
    destinations. Taxis spawn available in given locations and react to customer requests received from their fleet manager.

* **FleetManager Agent**

    The FleetManager agent is responsible for putting in contact the TaxiCustomer agents that need a transport service, and the Taxi
    agents that may be available to offer these services. In short, the FleetManager Agent acts like a transport call center, accepting
    the incoming requests from customers and forwarding them to the (appropriate) taxis.
    In order to do so, the FleetManager features a registration protocol that allows Taxi agents to subscribe to their manager.
    This is process is automatically done when a Taxi agent starts its execution.


.. In the context of SimFleet, a "transport service" involves the following steps:

    .. The Taxi moves from its current position to the TaxiCustomer's location to pick them up.
    .. The Taxi transports the TaxiCustomer to their destination.


Configuration file
^^^^^^^^^^^^^^^^^^

Following, the necessary configuration file fields to define the taxi service agents are shown. These include a list of
taxi customers, taxi transports and the fleet manager.

A TaxiCustomer agent is defined with the following fields:

+--------------------------------------------------------------------------------------+
|  Taxi Customer                                                                       |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| class       |   Custom agent file in the format ``module.file.Class``                |
+-------------+------------------------------------------------------------------------+
| position    |   Initial coordinates of the customer (optional)                       |
+-------------+------------------------------------------------------------------------+
| destination |   Destination coordinates of the customer (optional)                   |
+-------------+------------------------------------------------------------------------+
| name        |   Name of the customer (unique)                                        |
+-------------+------------------------------------------------------------------------+
| password    |   Password for registering the customer in the platform (optional)     |
+-------------+------------------------------------------------------------------------+
| fleet_type  |   Fleet type that the customer wants to use                            |
+-------------+------------------------------------------------------------------------+
| icon        |   Custom icon (in base64 format) to be used by the customer (optional) |
+-------------+------------------------------------------------------------------------+
| strategy    |   Custom strategy file in the format ``module.file.Class`` (optional)  |
+-------------+------------------------------------------------------------------------+
| delay       |   Agent's execution time start, in seconds  (optional)                 |
+-------------+------------------------------------------------------------------------+

A Taxi agent is defined by the following fields:

+---------------------------------------------------------------------------------------------+
|  Taxi                                                                                       |
+------------------+--------------------------------------------------------------------------+
|  Field           |  Description                                                             |
+==================+==========================================================================+
| class            |   Custom agent file in the format ``module.file.Class``                  |
+------------------+--------------------------------------------------------------------------+
| position         |   Initial coordinates of the transport (optional)                        |
+------------------+--------------------------------------------------------------------------+
| name             |   Name of the transport (unique)                                         |
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
| delay            |   Agent's execution time start, in seconds  (optional)                   |
+------------------+--------------------------------------------------------------------------+

A FleetManager agent fields are defined as follows:

+--------------------------------------------------------------------------------------+
|  Fleet Manager                                                                       |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| name        |   Name of the manager (unique)                                         |
+-------------+------------------------------------------------------------------------+
| password    |   Password for registering the manager in the platform (optional)      |
+-------------+------------------------------------------------------------------------+
| fleet_type  |   Fleet type that the agent manages                                    |
+-------------+------------------------------------------------------------------------+
| icon        |   Custom icon (in base64 format) to be used by the manager  (optional) |
+-------------+------------------------------------------------------------------------+
| strategy    |   Custom strategy file in the format ``module.file.Class``  (optional) |
+-------------+------------------------------------------------------------------------+

Finally, we show an example of a taxi service configuration file featuring four customers, two transports and a fleet manager.
This configuration file includes:

    * One taxi with a fixed initial position and another with a random initial position.
    * One customer with fixed origin and destination coordinates.
    * Three customers with random origin and destination coordinates.

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

Electric taxi service simulation
--------------------------------

This transportation mode represents the same taxi service explained previously, with the modification that taxis are now
modeled as electric vehicles with a given autonomy level. A transport's autonomy will decrease as it serves customer requests.
The electric taxis check their autonomy level before each trip and may decide to recharge their batteries at a
charging station when necessary. Thus, this simulation scenarios introduces two new agents: the **ElectricTaxi Agents**
and the **ChargingStation Agents**; and keep the TaxiCustomer and the FleetManager agents previously described.

Agent description
^^^^^^^^^^^^^^^^^

* **ElectricTaxi Agents**

    The ElectricTaxi agents represent electric vehicles that can transport TaxiCustomer agents from their current positions to their respective destinations.
    In contrast with Taxi agents, ElectricTaxi agents have a limited battery autonomy and thus need to monitor their charge levels. When their battery is low, they
    travel to a ChargingStation to fully recharge before continuing to provide transportation services.

* **ChargingStation Agents**

    The ChargingStation agents represent locations where ElectricTaxi agents can recharge their batteries,
    enabling them to continue offering transport services.
    ChargingStations may have a limited availability of charging slots, which means ElectricTaxi agents may need to wait if the station
    they wish to use is full.


.. In the context of SimFleet, a "transport service" involves the following steps:

    .. . The ElectricTaxi moves from its current position to the TaxiCustomer's location to pick them up.
    .. . The ElectricTaxi transports the TaxiCustomer to their destination.
    .. . If the ElectricTaxi's battery is low after the trip, it travels to a ChargingStation to recharge before accepting another request.

Configuration file
^^^^^^^^^^^^^^^^^^

Following, the necessary configuration file fields to define the new agents that implement the electric taxi service are shown.
This includes a list of electric taxi transports and charging stations.

For ElectricTaxi agents, the fields are as follows:

+---------------------------------------------------------------------------------------------+
|  Electric Taxis                                                                             |
+------------------+--------------------------------------------------------------------------+
|  Field           |  Description                                                             |
+==================+==========================================================================+
| class            |   Custom agent file in the format ``module.file.Class``                  |
+------------------+--------------------------------------------------------------------------+
| position         |   Initial coordinates of the transport (optional)                        |
+------------------+--------------------------------------------------------------------------+
| name             |   Name of the transport (unique)                                         |
+------------------+--------------------------------------------------------------------------+
| password         |   Password for registering the transport in the platform (optional)      |
+------------------+--------------------------------------------------------------------------+
| speed            |   Speed of the transport (in meters per second)  (optional)              |
+------------------+--------------------------------------------------------------------------+
| service          |   Type of Service the transport requires from stations                   |
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
| delay            |   Agent's execution time start, in seconds  (optional)                   |
+------------------+--------------------------------------------------------------------------+

For ChargingStation agents the fields are as follows:

+--------------------------------------------------------------------------------------+
|  Charging stations                                                                   |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| class       |   Custom agent file in the format ``module.file.Class``                |
+-------------+------------------------------------------------------------------------+
| position    |   Initial coordinates of the customer (optional)                       |
+-------------+------------------------------------------------------------------------+
| name        |   Name of the station (unique)                                         |
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
| delay       |   Agent's execution time start, in seconds  (optional)                 |
+-------------+------------------------------------------------------------------------+

Finally, An example of a config file with four customers, two transports, one fleet manager and two stations.
This configuration file includes:

    * One ElectricTaxi with a fixed position and one with a random position.
    * Low initial autonomy for both ElectricTaxi agents.
    * One TaxiCustomer with fixed origin and destination coordinates.
    * Three TaxiCustomers with random positions.
    * Two ChargingStations, one with a fixed position and one with a random position.

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

Urban Bus simulation
--------------------

This transportation mode represents an urban bus service, where buses travel continuously following their assigned line, visiting
the stops that belong to such a line, in order. Customers make use of the bus service by walking to a stop and waiting
for their desired bus to arrive. The customer boards the bus travels inside it until the bus visits their desired destination stop.
Bus stops are modeled as agents that act as intermediaries between buses and customers, keeping waiting queues for each bus line
in which the stop is included, and informing waiting customers of each bus arrival. Optionally, the bus service may be
coordinated by a fleet manager.

The scenario features four types of agent: The **BusCustomer Agents**, the **Bus Agents**, the **BusStop Agents**, and a **FleetManager Agent**.


Agent description
^^^^^^^^^^^^^^^^^

* **BusCustomer Agents**

    The BusCustomer agents represent people who need to travel from one location in the city (their "current location") to another (their "destination").
    To achieve this, each BusCustomer agent knows the bus line it needs to use. Upon spawning, the customer walks to their
    nearest BusStop which belongs to their line, in order to catch a Bus transport. Once they are transported to their destination, customers end their execution.

* **Bus Agents**

    The Bus agents represent a bus transport that travels along the BusStops of a predefined route, indicated by its assigned line.
    Buses stop at the designated BusStops to pick up and drop off passengers.

* **BusStop Agents**

    The BusStop agents represent designated stopping points where buses can pick up and drop off BusCustomer agents. BusStops must belong to at least one line
    of the service, although they may belong to many lines. For each of their lines, the BusStop keeps a waiting queue where BusCustomer agents
    are registered upon arrival. In addition, BusStops inform their registered customers of the arrival of each Bus, and coordinates
    the processed of passenger de-boarding and boarding to the transport.

* **FleetManager Agent**

    The FleetManager acts as a central coordinator of the fleet of buses.
    In order to do so, the FleetManager has a registration protocol by which Bus agents subscribe to their fleet.

.. In the context of SimFleet, a "transport service" for buses involves:

    .. The Bus agent following its predefined route.
    .. Picking up BusCustomer agents waiting at BusStops.
    .. Dropping off BusCustomer agents at BusStops near their destinations.

Configuration file
^^^^^^^^^^^^^^^^^^

Following, the necessary configuration file fields to define the urban bus service agents are shown. These include a list of
bus customers, bus transports, bus stops, and the predefined lines of the service.

Each BusCustomer agent must include the following fields:

+--------------------------------------------------------------------------------------+
|  Bus Customer                                                                        |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| class       |   Custom agent file in the format ``module.file.Class``                |
+-------------+------------------------------------------------------------------------+
| position    |   Initial coordinates of the customer                                  |
+-------------+------------------------------------------------------------------------+
| destination |   Destination coordinates of the customer                              |
+-------------+------------------------------------------------------------------------+
| name        |   Name of the customer (unique)                                        |
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
| delay       |   Agent's execution time start, in seconds  (optional)                 |
+-------------+------------------------------------------------------------------------+

.. note::
    If the **speed** field is not defined, the customer will not be able to walk. In this case, the customer's position
    and destination must match positions of bus stops.

For Bus agents the fields are as follows:

+---------------------------------------------------------------------------------------------+
|  Bus                                                                                        |
+------------------+--------------------------------------------------------------------------+
|  Field           |  Description                                                             |
+==================+==========================================================================+
| class            |   Custom agent file in the format ``module.file.Class``                  |
+------------------+--------------------------------------------------------------------------+
| position         |   Initial coordinates of the transport                                   |
+------------------+--------------------------------------------------------------------------+
| name             |   Name of the transport (unique)                                         |
+------------------+--------------------------------------------------------------------------+
| password         |   Password for registering the transport in the platform (optional)      |
+------------------+--------------------------------------------------------------------------+
| speed            |   Speed of the transport (in meters per second)                          |
+------------------+--------------------------------------------------------------------------+
| line             |   Bus line assigned to the transport                                     |
+------------------+--------------------------------------------------------------------------+
| capacity         |   Number of customers that can be transported together                   |
+------------------+--------------------------------------------------------------------------+
| fleet_type       |   Fleet type of the transport                                            |
+------------------+--------------------------------------------------------------------------+
| optional         |   **fleet**: The fleet manager's JID to be subscribed to                 |
+------------------+--------------------------------------------------------------------------+
| icon             |   Custom icon (in base64 format) to be used by the transport  (optional) |
+------------------+--------------------------------------------------------------------------+
| strategy         |   Custom strategy file in the format ``module.file.Class``  (optional)   |
+------------------+--------------------------------------------------------------------------+
| delay            |   Agent's execution time start, in seconds  (optional)                   |
+------------------+--------------------------------------------------------------------------+

.. note::
    The bus agent's position must match one of the bus stops on its assigned line for correct operation.

For BusStop agents the fields are as follows:

+--------------------------------------------------------------------------------------+
|  Bus stop                                                                            |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| class       |   Custom agent file in the format ``module.file.Class``                |
+-------------+------------------------------------------------------------------------+
| position    |   Initial coordinates of the customer                                  |
+-------------+------------------------------------------------------------------------+
| id          |   Id of the station (unique)                                           |
+-------------+------------------------------------------------------------------------+
| name        |   Name of the stop                                                     |
+-------------+------------------------------------------------------------------------+
| password    |   Password for registering the station in the platform (optional)      |
+-------------+------------------------------------------------------------------------+
| lines       |   Bus lines to which the stops belongs                                 |
+-------------+------------------------------------------------------------------------+
| icon        |   Custom icon (in base64 format) to be used by the customer (optional) |
+-------------+------------------------------------------------------------------------+
| delay       |   Agent's execution time start, in seconds  (optional)                 |
+-------------+------------------------------------------------------------------------+

**Bus lines** are necessary auxiliary fields of the configuration file for urban bus simulations.
Their most relevant parameter are the list of stops that belong to it. Such a list must appear ordered, and
each stop is defined by its coordinates. Once a Bus transport reaches the last stop of its line, the line_type
indicates how it continues its operation.

+--------------------------------------------------------------------------------------+
|  Bus line                                                                           |
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
    The **line_type** field defined three types of bus behaviour upon reaching the end of its line:

        1) **circular:** The bus chooses the first stop of the line as next destination (circular routes).
        2) **end-to-end:** The bus inverses the stop list and choose previous stop as next destination (end-to-end lines).
        3) **teleport:** The bus teleports to the first stop of the line, and continues its operation.


Finally, we show an example of a configuration file with two customers, two transports, one fleet manager, and eleven stops that belong to the same line:
This configuration file includes:

    * Two Buses with a fixed position.
    * Two BusCustomer with fixed origin and destination positions.
    * One Line with eleven BusStops.

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


Vehicle transit simulation
--------------------------

SimFleet includes the so-called Vehicle agents which represent vehicles that move autonomously in the simulation scenario.
Vehicles are a simplified version of transports which do not provide transportation services. However, vehicles may be extended to make
use of the transportation infrastructure (stations) of the scenario, introducing simulation load. Following, we describe
the **Vehicle Agent** and its use.

Agent description
^^^^^^^^^^^^^^^^^

* **Vehicle Agents**

    These agents can autonomously travel from an origin point to a destination. They can either perform a single trip or continuously travel to new random destinations in a cyclic manner.


Configuration file
^^^^^^^^^^^^^^^^^^

Following, the necessary configuration file fields to define vehicle agents are shown. Each vehicle must include:

+--------------------------------------------------------------------------------------+
|  Vehicle                                                                             |
+-------------+------------------------------------------------------------------------+
|  Field      |  Description                                                           |
+=============+========================================================================+
| class       |   Custom agent file in the format ``module.file.Class``                |
+-------------+------------------------------------------------------------------------+
| position    |   Initial coordinates of the agent (optional)                          |
+-------------+------------------------------------------------------------------------+
| destination |   Destination coordinates of the agent (optional)                      |
+-------------+------------------------------------------------------------------------+
| name        |   Name of the agent (unique)                                           |
+-------------+------------------------------------------------------------------------+
| password    |   Password for registering the agent in the platform (optional)        |
+-------------+------------------------------------------------------------------------+
| speed       |   Speed of the vehicle (in meters per second)  (optional)              |
+-------------+------------------------------------------------------------------------+
| icon        |   Custom icon (in base64 format) to be used by the agent (optional)    |
+-------------+------------------------------------------------------------------------+
| strategy    |   Custom strategy file in the format ``module.file.Class``  (optional) |
+-------------+------------------------------------------------------------------------+
| delay       |   Agent's execution time start, in seconds  (optional)                 |
+-------------+------------------------------------------------------------------------+

Finally, we show an example of a configuration file with two autonomous vehicles.
This configuration file includes:

    * One autonomous vehicle with a fixed initial position and destination, following a cyclic behavior.
    * One autonomous vehicle without a specified initial position or destination, performing a one-shot behavior.

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


Command-line interface
======================

In the QuickStart guide, we covered how to quickly get started with SimFleet using the graphical interface. In this section, we will explore
in greater detail how to use the **Command-Line Interface (CLI)** to configure and launch transport simulation scenarios directly from the command line.
This guide explains the usage and available options of the ``simfleet`` command, making it easier to run simulations, debug processes, and save results.

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

.. note::
    To visualize the simulation scenario in the GUI while running simulator from the CLI, use the web interface address displayed in the output, such as:

    .. code-block:: console

        2024-11-25 16:29:07.229 | INFO     | simfleet.simulator:setup:110 - Web interface running at http://127.0.0.1:9000/app

    This address is (in most cases): `http://127.0.0.1:9000/app <http://127.0.0.1:9000/app>`_

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


* **Example 3: Simulation with Time Limit and Autorun**

.. code-block:: console

    $ simfleet --config myconfig.json --name "My Simulation" --output results.json --max-time 100 --autorun

In this example, the configuration file ``myconfig.json`` is used, and the simulation is named "My Simulation". The ``--autorun`` flag ensures the simulation starts automatically
as soon as the agents are ready. Additionally, the ``--max-time 100`` option limits the simulation duration to 100 seconds. The simulation events are saved to ``results.json``,
making it easy to review the results once the simulation concludes.
