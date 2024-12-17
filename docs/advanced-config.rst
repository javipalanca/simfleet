====================
Configuration Manual
====================

Using SimFleet is straightforward and can be done by running the application from the command line. There are two modes of use:
a **command-line interface (CLI)** and a **web-based graphical interface (GUI)**. You can execute simulations purely through the command
line or use the simpler and more intuitive graphical interface.

SimFleet supports a wide variety of urban mobility scenarios, as the simulator includes predefined agents and strategies. In this section,
we will explore how to use both interfaces of advance mode and the different simulation scenarios available.


Taxi simulation scenario
========================

In this scenario, SimFleet there are three types of agent that interact among them during simulations. These are the FleetManager
agent, the Taxi agent, and the TaxiCustomer agent.


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

    In the context of SimFleet, a "transport service" involves, once a particular TaxiCustomer and Taxi agents have reached
    an agreement, the movement of the Taxi agent from its current position to the TaxiCustomer's position in
    order to pick the Customer up, and then the transportation of the TaxiCustomer agent to its destination.

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
| optional         |   **fleet**: The fleet manager's JID to be subscribed to (optional)        |
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

Electric taxi simulation scenario
=================================


Bus simulation scenario
=======================


Another simulation scenario
===========================


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
