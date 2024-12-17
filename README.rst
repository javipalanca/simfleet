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


Simfleet is a multi-agent simulation and fleet management platform that facilitates the training, optimization, and operation
of transportation systems within virtual environments. Its primary purpose is to study mobility in realistic scenarios without
the need for physical testing.

Simfleet includes three predefined types of transportation (taxi, electric taxi, and bus), two types of infrastructure
(taxi charging station and bus stop), and two types of clients (taxi customer and bus customer) to enable quick and
efficient simulations.

However, for advanced users, the platform allows extending the study cases by developing additional types of agents.
This flexibility is made possible by Simfleet's architecture, which supports the implementation of custom agents tailored
to the user's specific needs.

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
