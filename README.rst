========
SimFleet
========


.. image:: https://img.shields.io/pypi/v/simfleet.svg
        :target: https://pypi.python.org/pypi/simfleet

.. image:: https://img.shields.io/pypi/pyversions/simfleet.svg
    :target: https://pypi.python.org/pypi/simfleet

.. image:: https://img.shields.io/tokei/lines/github/javipalanca/simfleet?label=lines
    :alt: Total Lines
    :target: https://pepy.tech/project/simfleet

.. image:: https://img.shields.io/github/languages/count/javipalanca/simfleet?label=languages
    :alt: Languages
    :target: https://pepy.tech/project/simfleet

.. image:: https://img.shields.io/github/languages/code-size/javipalanca/simfleet
    :alt: Code Size
    :target: https://pepy.tech/project/simfleet

.. image:: https://img.shields.io/apm/l/atomic-design-ui.svg?
    :target: https://opensource.org/licenses/MIT
    :alt: MIT License

.. image:: https://pepy.tech/badge/simfleet
    :target: https://pepy.tech/project/simfleet
    :alt: Downloads

.. image:: https://readthedocs.org/projects/simfleet/badge/?version=latest
        :target: https://simfleet.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


SimFleet is a multi-agent simulation platform for the orchestration and execution of transportation services.
All actors of a transportation system are represented by agents whose behaviours define the operation of the service and
its internal communication, enabling users to configure and test their own agent strategies.
This platform facilitates the study of mobility in realistic scenarios without the need for physical testing.

SimFleet includes predefined agent classes that represent the core components of any transportation service: Customers,
Transports, Fleet Managers, and Stations.

    * **Customer Agents**: People or goods that require transportation.
    * **Transport Agents**: Vehicles that provide displacement services to Customers.
    * **FleetManager Agents**: Service provider that manages a fleet of Transports.
    * **Station Agents**: Locations representing transportation infrastructure, such as bus stops or charging stations.

These agents can be extended and customized to represent a specific transportation mode. Currently, the platform
provides two predefined transportation services: Taxi/Electric Taxi service, and Urban Bus. These systems count with
their own implementation of Transport and Customer agents, as well as the necessary infrastructure: Electric Charging
Stations and Bus Stops. Using the predefined agents, SimFleet users may easily create and execute their own simulation
scenarios.

As for advanced users, however, the extension of predefined agents is encouraged to develop new agent types.
SimFleet's architecture, based on modularity, simplifies the implementation of custom agents and agent behaviours
tailored to the user's specific needs.


* Free software: MIT license
* Documentation: https://simfleet.readthedocs.io.


Features
--------

* Open Fleets simulator
* Strategy pattern
* Continuous simulator
* Load scenarios
* Multi-agent system built with SPADE_
* XMPP communications

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _SPADE: https://github.com/javipalanca/spade
