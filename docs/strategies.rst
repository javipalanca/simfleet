
======================
Customising Strategies
======================


Why Add Strategies to Agents?
=============================

`Adding strategies to an agent is like giving a script to an actor in a complex play. It’s not enough for the actor to`
`have the perfect costume and the necessary skills—they also need a clear purpose and a set of instructions to react to`
`each scene.`

Strategies represent the behaviour and logic that guide an agent’s decisions within its environment. Without a strategy,
an agent would be like a talented actor lost on stage, unsure of how to respond to events. Strategies turn agents into
active and effective participants in their narrative, ensuring their performance aligns with the ultimate goal of the play.

The Strategy Pattern
====================

The **Strategy Pattern** is a design pattern that enables selecting an algorithm at runtime. The Strategy Pattern is
the best practice when an application incorporates different, alternative versions of an algorithm and we want to be
able to select any of these versions to be executed at run time. With this pattern, you can define a separate
strategy (implementation of the algorithm) in an object that encapsulates the algorithm. The application that executes
the algorithm **must** define an interface that every strategy (implementation) will follow, as it can be seen in
the following figure:

.. figure:: images/strategy.png
    :align: center
    :alt: The Strategy Pattern UML

    The Strategy Pattern UML.

Following this implementation, the context object can call the current strategy implementation without knowing how the
algorithm was implemented. This design pattern was created, among others, by a group of authors commonly known as the
**Gang of Four** (E. Gamma, R. Helm, R. Johnson and J. Vlissides), and it is well presented in [GangOfFour95]_.

SimFleet uses the *Strategy Pattern* in order to enable users to implement three different strategies (one for the
fleet manager agent, one for the transport agent and one for the customer agent) without having to develop new agents or
entering in the complexity of the simulator. Thanks to this pattern, users can develop their strategies in an external
file and pass it as an argument when the simulator is run.

The Strategy Pattern is a common design in programming that allows for the dynamic selection of algorithms at runtime,
promoting flexibility and code reuse. In this context, strategies are represented as specific classes that inherit from
generic behaviours and extend or redefine specific functionalities. This pattern is particularly useful in the realm of
intelligent agents, where decisions and behaviours may vary depending on the requirements.

Below are two main classes related to the Strategy Pattern found in the `abstractstrategies.py` module:


The Strategy Behaviour
----------------------

The StrategyBehaviour class is a base class designed to implement the Strategy Pattern. It provides a framework that
allows the customization of behaviors for agents. It ensures that all strategies inherit from a common parent, making
it easier to define and manage lifecycle events like initialization, execution, and cleanup.

.. figure:: images/strategies/StrategyBehaviour-dc.png
    :align: center
    :alt: The StrategyBehaviour class and their inherited interfaces

    The StrategyBehaviour class and their inherited interfaces

Key Characteristics:
~~~~~~~~~~~~~~~~~~~~

* **Inheritance Structure:** The StrategyBehaviour class extends the ``spade.behaviour.CyclicBehaviour`` from SPADE (a multi-agent framework) and uses an ABCMeta metaclass to enforce abstract methods.

* **Lifecycle Management:** It includes ``on_start()`` and ``on_end()`` methods to manage pre- and post-execution events. These methods log lifecycle events and provide hooks for custom statistics tracking.

* **Abstract Run Method:** The ``run()`` method is abstract and must be implemented by all subclasses. This enforces the definition of agent-specific behaviors when designing strategies.

Example Implementation:
~~~~~~~~~~~~~~~~~~~~~~~

For instance, the :class:`TaxiCustomerStrategyBehaviour` class inherits from StrategyBehaviour and defines:

* ``send_request()`` Sends transport requests to FleetManager agents.

* ``accept_transport()`` Accepts a transport proposal from a transport agent.

* ``refuse_transport()``: Refuses a transport proposal from a transport agent.

The strategy can be further specialized. For example:

* :class:`AcceptFirstRequestBehaviour` of `TaxiCustomer`: Accepts the first valid transport offer received from a taxi.

The Strategy Behaviour decouples the strategy logic from the agent's core, allowing agents to switch strategies dynamically
at runtime. It enables modularity and extensibility in multi-agent systems


The FSM Simfleet Behaviour
--------------------------

The :class:`FSMSimfleetBehaviour` class extends the base Strategy Behaviour by combining it with Finite State Machine (FSM) logic,
enabling agents to transition between discrete states while maintaining a defined lifecycle.

.. figure:: images/strategies/FSMSimfleetBehaviour-dc.png
    :align: center
    :alt: The FSMSimfleetBehaviour class and their inherited interfaces

    The FSMSimfleetBehaviour class and their inherited interfaces

Key Characteristics:
~~~~~~~~~~~~~~~~~~~~

* **FSM Framework:** This class leverages the ``spade.behaviour.FSMBehaviour`` framework to implement agents with multiple states. Each state corresponds to a specific stage in the agent's operation (e.g., a taxi waiting for customers, moving to a destination, or charging).

* **Lifecycle Management:** Similar to `StrategyBehaviour`, it includes ``on_start()`` and ``on_end()`` methods, ensuring consistency in event tracking across all states.

* **State Definition and Transition:** The ``setup()`` method is overridden to define the states and transitions for an FSM. Transitions dictate how the agent progresses between states based on certain conditions or events.

Example Implementation:
~~~~~~~~~~~~~~~~~~~~~~~

An :class:`ElectricTaxiAgent` uses the :class:`FSMSimfleetBehaviour` to handle multiple states such as:

* Waiting for a Customer: :class:`ElectricTaxiWaitingState()`.

* Moving to a Customer: :class:`ElectricTaxiMovingToCustomerState()`.

* Charging at a Station: :class:`ElectricTaxiChargingState()`.

.. hint::
    The State class provides a structure for defining individual states, including the on_start and run methods,
    which control what happens when the state is entered and its main behavior, respectively. By extending State,
    the :class:`ElectricTaxiStrategyBehaviour` class ensures compatibility with FSMBehavior while adding domain-specific functionality.
