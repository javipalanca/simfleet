=====
Usage
=====

Introduction
============
General description on how to use taxi_simulator (command + graphical interface). Reference to default strategies.

Command-line interface
======================

To use Taxi Simulator in a project::

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



Graphical User Interface
========================


Advanced Features
=================


Loading Scenarios
-----------------

