=======
History
=======

1.0.0 (2019-11-05)
------------------

* Moved from a taxi simulator to a generic fleet simulator.
* Updated documentation.
* Added support for different cities.
* Directory agent now sends all the info.
* Fixed bug of staying the corresponding time in the station when charging.
* Changed logger to loguru library.
* Removed fuel from transport popup, now is current_autonomy/max_autonomy.
* Concurrent charging in stations now allowed through TimeoutBehavior.
* Custom icons added.
* Removed agents introduction from GUI.
* Added specific parameters in scenario file (now config file).
* CLI simplified.
* Changed cli to config file.
* Control of free places and status for StationAgent.
* Fuel refill behavior between TransportAgent and StationAgent.
* Refactoring from passenger to Customer
* Refactoring from taxi to Transport
* Refactoring from coordinator to fleet manager

0.4.1 (2019-01-07)
------------------

* Fixed bug when checking if the simulation is finished.

0.4.0 (2018-10-25)
------------------

* Improved the concurrent creation of agents.
* Added stop and clear buttons to the interface.
* Added download button for getting results in excel and json formats.
* Documentation updated.

0.3.0 (2018-10-01)
------------------

* Migrated to SPADE 3.
* Documentation highly improved.
* Helper functions added and refined.
* Javascript framework included: VueJS
* Routes centralized with a Route agent.
* UI improved.

0.2 (2017-11-15)
------------------

* Added scenario loading feature.

0.1.3 (2017-11-15)
------------------

* Fixed minor bugs.

0.1.1 (2017-11-14)
------------------

* Added documentation.

0.1.0 (2017-11-03)
------------------

* First release on PyPI.

