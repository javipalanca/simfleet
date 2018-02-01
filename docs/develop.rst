
=========================
Developing new strategies
=========================

Introduction
============
It is possible to change the behavior of three different agent "types" inside Taxi Simulator: Coordinator, Taxi and Passenger.


Description of Coordinator Agent
--------------------------------

Strategy Behaviour
~~~~~~~~~~~~~~~~~~
Which are its goals. What it does. Possible states and semantics of each state.


Description of Taxi Agent
-------------------------

Strategy Behaviour
~~~~~~~~~~~~~~~~~~
Which are its goals. What it does. Possible states and semantics of each state.

Moving Behaviour
----------------
Goals, Actions, States.


Description of Passenger Agent
--------------------------------

Strategy Behaviour
~~~~~~~~~~~~~~~~~~
Which are its goals. What it does. Possible states and semantics of each state.

Travel Behaviour
~~~~~~~~~~~~~~~~
Goals, Actions, States.


How agents interact in the default strategies
---------------------------------------------
Description (and image) of Request Protocol (how some messages change agents' status)



How to implement your own strategies
====================================

SPADE
-----

Agent Model: Behaviors and Templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Communication API (and FIPA)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The Strategy Pattern
--------------------


Description of Coordinator Agent
--------------------------------

Code
~~~~
Coordinator strategies must inherit from `CoordinatorStrategyBehaviour`

Helpers
~~~~~~~


Description of Taxi Agent
-------------------------

Code
~~~~
Taxi strategies must inherit from `TaxiStrategyBehaviour`

Helpers
~~~~~~~
::

            def send_proposal(self, passenger_id, content=None)
            def cancel_proposal(self, passenger_id, content=None)
            def pick_up_passenger(self, passenger_id, origin, dest)


Description of Passenger Agent
------------------------------

Code
~~~~
Passenger strategies must inherit from `PassengerStrategyBehaviour`

Helpers
~~~~~~~
::

            def send_request(self, content=None)
            def accept_taxi(self, taxi_aid)
            def refuse_taxi(self, taxi_aid)
            def timeout_receive(self, timeout=5)

Other Helpers
-------------



How to Implement New Strategies (Level 1) -- Recommendations
============================================================

Load simulator with your custom strategies::

 $ taxi_simulator --taxi my_strategy_file.MyTaxiStrategyClass
                  --passenger my_strategy_file.MyPassengerStrategyClass
                  --coordinator my_strategy_file.MyCoordinatorStrategyClass



