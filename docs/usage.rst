=====
Usage
=====

To use Taxi Simulator in a project::

    Usage: taxi_simulator [OPTIONS]

      Console script for taxi_simulator.

    Options:
      -t, --taxi TEXT                Taxi strategy class (default:
                                     AcceptAlwaysStrategyBehaviour).
      -p, --passenger TEXT           Passenger strategy class (default:
                                     AcceptFirstRequestTaxiBehaviour).
      -c, --coordinator TEXT         Coordinator strategy class (default:
                                     DelegateRequestTaxiBehaviour).
      --port INTEGER                 Web interface port (default: 9000).
      -nt, --num-taxis INTEGER       Number of initial taxis to create (default:
                                     0).
      -np, --num-passengers INTEGER  Number of initial passengers to create
                                     (default: 0).
      --scenario TEXT                Filename of JSON file with initial scenario
                                     description.
      --name TEXT                    Coordinator agent name (default:
                                     coordinator).
      --passwd TEXT                  Coordinator agent password (default:
                                     coordinator_passwd).
      -bp, --backend-port INTEGER    Backend port (default: 5000).
      -v, --verbose                  Show verbose debug.
      --help                         Show this message and exit.


=========================
Developing new strategies
=========================

To develop new strategies:

   * Taxi strategies must inherit from `TaxiStrategyBehaviour`
        * Helper functions::

            def send_proposal(self, passenger_id, content=None)
            def cancel_proposal(self, passenger_id, content=None)
            def pick_up_passenger(self, passenger_id, origin, dest)

   * Passenger strategies must inherit from `PassengerStrategyBehaviour`
        * Helper functions::

            def send_request(self, content=None)
            def accept_taxi(self, taxi_aid)
            def refuse_taxi(self, taxi_aid)
            def timeout_receive(self, timeout=5)

   * Coordinator strategies must inherit from `CoordinatorStrategyBehaviour`


Load simulator with your custom strategies::

 $ taxi_simulator --taxi my_strategy_file.MyTaxiStrategyClass
                  --passenger my_strategy_file.MyPassengerStrategyClass
                  --coordinator my_strategy_file.MyCoordinatorStrategyClass

