=====
Usage
=====

Quickstart
==========

Using Taxi Simulator is as easy as running the application in a command line. There are two use modes: a command-line
interface and a graphical web-based view. You can run simulations using only the command line or using the more easy and
intuitive graphical user interface. Running Taxi Simulator without your own developed coordination strategies is posible
since the application comes with a set of default strategies. Let's explore how to use both user interfaces.

Command-line interface
======================

After installing Taxi Simulator open a command-line and type ``taxi_simulator``. This starts a simulator without any
options and runs the coordinator agent. The console will output the default logging information and you can terminate
the simulator by pressing ``Ctrl+C``. When you terminate the simulator the results of the simulations are printed.

.. code-block:: console

    $ taxi_simulator
    INFO:root:Starting Taxi Simulator
    INFO:CoordinatorAgent:Coordinator agent running
    INFO:CoordinatorAgent:Web interface running at http://127.0.0.1:9000/app
    INFO:root:Creating 0 taxis and 0 passengers.
    INFO:RouteAgent:Route agent running
    WARNING:RouteAgent:Could not load cache file.

    ^C
    INFO:root: Terminating... (0.0 seconds elapsed)
    Simulation Results
    ╒════════════════════╤══════════════════╤═══════════════════╤═══════════════════════╕
    │   Avg Waiting Time │   Avg Total Time │   Simulation Time │ Simulation Finished   │
    ╞════════════════════╪══════════════════╪═══════════════════╪═══════════════════════╡
    │                  0 │                0 │                 0 │ True                  │
    ╘════════════════════╧══════════════════╧═══════════════════╧═══════════════════════╛
    Passenger stats
    ╒════════╤════════════════╤══════════════╤══════════╕
    │ name   │ waiting_time   │ total_time   │ status   │
    ╞════════╪════════════════╪══════════════╪══════════╡
    ╘════════╧════════════════╧══════════════╧══════════╛
    Taxi stats
    ╒════════╤═══════════════╤════════════╤══════════╕
    │ name   │ assignments   │ distance   │ status   │
    ╞════════╪═══════════════╪════════════╪══════════╡
    ╘════════╧═══════════════╧════════════╧══════════╛

However, if you don't use some options when running the simulator there will be no default taxis nor passengers. That's
why stats are empty. To run a simulation with some parameters you can use the command-line interface options.

To show these options you can enter the ``--help`` command:

.. code-block:: console

    $ taxi_simulator --help

    Usage: taxi_simulator [OPTIONS]

      Console script for taxi_simulator.

    Options:
      -n, --name TEXT                Name of the simulation execution.
      -o, --output TEXT              Filename to save simulation results.
      -of, --oformat [json|excel]    Output format used to save simulation results. (default: json)
      -mt, --max-time INTEGER        Maximum simulation time (in seconds).
      -r, --autorun                  Run simulation as soon as the agents are ready.
      -t, --taxi TEXT                Taxi strategy class (default: AcceptAlwaysStrategyBehaviour).
      -p, --passenger TEXT           Passenger strategy class (default: AcceptFirstRequestTaxiBehaviour).
      -c, --coordinator TEXT         Coordinator strategy class (default: DelegateRequestTaxiBehaviour).
      --port INTEGER                 Web interface port (default: 9000).
      -nt, --num-taxis INTEGER       Number of initial taxis to create (default: 0).
      -np, --num-passengers INTEGER  Number of initial passengers to create (default: 0).
      --scenario TEXT                Filename of JSON file with initial scenario description.
      -cn, --coordinator-name TEXT   Coordinator agent name (default: coordinator).
      --passwd TEXT                  Coordinator agent password (default: coordinator_passwd).
      -bp, --backend-port INTEGER    Backend port (default: 5000).
      -v, --verbose                  Show verbose debug level: -v level 1, -vv level 2, -vvv level 3, -vvvv level 4
      --help                         Show this message and exit.

Running a simulation from the command-line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To run a quick simulation from the command-line you need to set up a few arguments: the number of taxis, the number of
passengers and (optionally) the maximum time of simulation.
The argument ``--num-taxis`` (or ``-nt``` initializates the specified number of taxis in random positions of the map.
The argument ``--num-passengers`` (or ``-np``` initializates the specified number of passengers in random positions of
the map and with a random destination for each one. If you want limit the simulation time tou can use the ``--max-time``
argument (or ``-mt``) to set the maximum number of seconds after which the simulation will end. Finally, the
``--autorun`` argument (or ``-r``) automatically runs the simulation (this argument is important when you are not using
the graphical interface, since it is the only way to start the simulation).

Example:

.. code-block:: console

    $ taxi_simulator --num-taxis 2 --num-passengers 2 --max-time 60 --autorun
    INFO:root:Starting Taxi Simulator
    INFO:CoordinatorAgent:Coordinator agent running
    INFO:CoordinatorAgent:Web interface running at http://127.0.0.1:9000/app
    INFO:root:Creating 2 taxis and 2 passengers.
    INFO:RouteAgent:Route agent running
    INFO:CoordinatorAgent:Simulation started.
    INFO:PassengerAgent:Passenger michelle08 asked for a taxi to [39.469057, -0.406452].
    INFO:PassengerAgent:Passenger schapman asked for a taxi to [39.465762, -0.382746].
    INFO:TaxiAgent:Taxi stevencortez sent proposal to passenger michelle08
    INFO:TaxiAgent:Taxi austin05 sent proposal to passenger michelle08
    INFO:PassengerAgent:Passenger michelle08 accepted proposal from taxi stevencortez@127.0.0.1
    INFO:PassengerAgent:Passenger michelle08 refused proposal from taxi austin05@127.0.0.1
    INFO:TaxiAgent:Taxi stevencortez on route to passenger michelle08
    INFO:PassengerAgent:Passenger michelle08 informed of status: 11
    INFO:PassengerAgent:Passenger michelle08 waiting for taxi.
    INFO:TaxiAgent:Taxi stevencortez has arrived to destination.
    INFO:PassengerAgent:Passenger schapman asked for a taxi to [39.465762, -0.382746].
    INFO:TaxiAgent:Taxi austin05 sent proposal to passenger schapman
    INFO:PassengerAgent:Passenger schapman accepted proposal from taxi austin05@127.0.0.1
    INFO:TaxiAgent:Taxi austin05 on route to passenger schapman
    INFO:PassengerAgent:Passenger schapman informed of status: 11
    INFO:PassengerAgent:Passenger schapman waiting for taxi.
    INFO:TaxiAgent:Taxi stevencortez has picked up the passenger michelle08@127.0.0.1.
    INFO:PassengerAgent:Passenger michelle08 informed of status: 12
    INFO:PassengerAgent:Passenger michelle08 in taxi.
    INFO:TaxiAgent:Taxi stevencortez has arrived to destination.
    INFO:TaxiAgent:Taxi stevencortez has dropped the passenger michelle08@127.0.0.1 in destination.
    INFO:PassengerAgent:Passenger michelle08 informed of status: 22
    INFO:PassengerAgent:Passenger michelle08 arrived to destination after 10.8725750446 seconds.
    INFO:TaxiAgent:Taxi austin05 has arrived to destination.
    INFO:TaxiAgent:Taxi austin05 has picked up the passenger schapman@127.0.0.1.
    INFO:PassengerAgent:Passenger schapman informed of status: 12
    INFO:PassengerAgent:Passenger schapman in taxi.
    INFO:TaxiAgent:Taxi austin05 has arrived to destination.
    INFO:TaxiAgent:Taxi austin05 has dropped the passenger schapman@127.0.0.1 in destination.
    INFO:PassengerAgent:Passenger schapman informed of status: 22
    INFO:PassengerAgent:Passenger schapman arrived to destination after 22.221298933 seconds.
    INFO:root:
    Terminating... (22.7 seconds elapsed)
    INFO:CoordinatorAgent:Stopping taxi stevencortez
    INFO:CoordinatorAgent:Stopping taxi austin05
    INFO:CoordinatorAgent:Stopping passenger michelle08
    INFO:CoordinatorAgent:Stopping passenger schapman
    Simulation Results
    ╒════════════════════╤══════════════════╤═══════════════════╤════════════╤═══════════════════════╕
    │   Avg Total Time   │ Avg Waiting Time │   Simulation Time │   Max Time │ Simulation Finished   │
    ╞════════════════════╪══════════════════╪═══════════════════╪════════════╪═══════════════════════╡
    │              22.69 │            16.55 │           22.6766 │         60 │ True                  │
    ╘════════════════════╧══════════════════╧═══════════════════╧════════════╧═══════════════════════╛
    Passenger stats
    ╒══════════════════════╤════════════════╤══════════════╤═══════════════════╕
    │ name                 │  total_time    │ waiting_time │ status            │
    ╞══════════════════════╪════════════════╪══════════════╪═══════════════════╡
    │ michelle08@127.0.0.1 │        22.685  │      10.8726 │ PASSENGER_IN_DEST │
    ├──────────────────────┼────────────────┼──────────────┼───────────────────┤
    │ schapman@127.0.0.1   │        22.6845 │      22.2213 │ PASSENGER_IN_DEST │
    ╘══════════════════════╧════════════════╧══════════════╧═══════════════════╛
    Taxi stats
    ╒════════════════════════╤═══════════════╤════════════╤══════════════╕
    │ name                   │   assignments │   distance │ status       │
    ╞════════════════════════╪═══════════════╪════════════╪══════════════╡
    │ stevencortez@127.0.0.1 │             1 │     4835.1 │ TAXI_WAITING │
    ├────────────────────────┼───────────────┼────────────┼──────────────┤
    │ austin05@127.0.0.1     │             1 │     7885.2 │ TAXI_WAITING │
    ╘════════════════════════╧═══════════════╧════════════╧══════════════╛

By analyzing the output of the simulation we can see what events have occurred and how the simulation has been
developed. There were created two taxis ( ``stevencortez`` and ``austin05``) and two passengers (``michelle08`` and
``schapman``). After the negotiation provided by the default strategies included in Taxi Simulator, taxi ``stevencortez``
was assigned to passenger ``michelle08`` and taxi ``austin05`` was assigned to passenger ``schapman``. After 22 seconds
of simulation both passengers were delivered in their destinations and taxis are free again to attend more passenger
requests.

The output of the simulation also shows some statistics of the simulation, with the `Average Total Time`, which
represents the average time of passengers from the moment they request a taxi until they are delivered to their
destination, and the `Average Waiting Time`, which is the average time of passengers from requesting a taxi to being
picked up. This information is also shown  for each passenger along with their status at the end of the simulation.

In the case of taxis, the shown information includes the number of assignments of each taxi (how many passengers it has
delivered), the total distance it has traveled and its final status.

This information is going to be useful for the development of new strategies that improve the system balancing or for
debugging errors if a taxi or a passenger gets stuck or any other unexpected situation occurs.


Saving the simulation results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to store the results of simulation in a file you may use the ``--output`` option (or ``-o``) to specify the
name of the file where the simulation results will be saved. The ``--oformat`` (``-of``) allows you to choose the output
format between json (default) or excel. It is also useful to use the ``--name`` (or ``-n``) to name the simulation.

Example:

.. code-block:: console

    $ taxi_simulator --name "My Simulation" --output results.xls --oformat excel


Advanced options
~~~~~~~~~~~~~~~~

There are other options that are less common and that you probably don't need to use very often. These are options that
allow you to change connection ports or default name and password of the coordinator agent. Use them only if there is a
port or name conflict.

The last but no less important option is the verbosity option. It allows you to specify how verbose you want the
simulator to be. The number of ``v`` letters you pass to the option indicates the level of verbosity (e.g. ``-v`` is
**DEBUG** verbosity and ``-vvvv`` is the highest level of verbosity where the internal messages of the platform are
shown).


.. note::
    You may have noticed that we haven't discussed three very important options that are: ``--taxi``, ``--passenger``,
    and ``--coordinator``. These options are used to inject new strategies to the simulator and we'll be discussed in a
    later chapter.
    Also, the ``--scenario`` option will be fully explained in a later section.


Graphical User Interface
========================


Advanced Features
=================


Loading Scenarios
-----------------

