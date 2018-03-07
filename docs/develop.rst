
=========================
Developing new strategies
=========================

.. contents:: Table of Contents

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



Agent Foundations
=================
The architecture of Taxi Simulator is built on top of a multi-agent system platform called SPADE. Although it is not necessary to
build new agents in order to develop new coordination strategies (the simulator provides all the necessary agents), it
is interesting to know how they work and what methods they provide for the creation of coordination strategies.

Next we will present the SPADE platform and its main features. For more documentation you can visit their website
https://github.com/javipalanca/spade.

SPADE
-----
`SPADE` (Smart Python multi-Agent Development Environment) is a multi-agent system (MAS) platform based on the
`XMPP <http://www.xmpp.org>`_ technology and written in the `Python <http://www.python.org/>`_ programming language.
This technology offers by itself many features and facilities that ease the construction of MAS, such as an existing
communication channel, the concepts of users (agents) and servers (platforms) and an extensible communication protocol
based on XML.

Extensible Messaging and Presence Protocol (XMPP) is an open, XML-inspired protocol for near-real-time, extensible
instant messaging (IM) and presence information. The protocol is built to be open and free, asynchronous, decentralized,
secure, extensible and flexible. These last two features allow XMPP not only to be an instant messaging protocol, but
it can also be extended and used for many tasks and situations (`IoT <https://xmpp.org/uses/internet-of-things.html>`_,
`WebRTC <https://xmpp.org/uses/webrtc.html>`_, `social <https://xmpp.org/uses/social.html>`_, ...). SPADE itself uses
some XMPP extensions to provide extended features to its agents, like remote procedure calls between agents
(`Jabber-RPC <https://xmpp.org/extensions/xep-0009.html>`_), file transfer
(`In-Band Bytestreams <https://xmpp.org/extensions/xep-0047.html>`_), an so on.


In order to fully understand how SPADE works, it is necessary to know how the agents are made up and how they
communicate. In the following sections we will see the SPADE agent model and its communication API.

Agent Model: Behaviors
~~~~~~~~~~~~~~~~~~~~~~
SPADE agents are threaded-based objects that can be run concurrently and that are connected to a SPADE platform which
internally runs an XMPP server. Each agent must provide an ID and password for its connection to the platform. This is
called the JID and has the form of an email: a user name string plus a "`@`" character plus the IP of the SPADE server
(e.g. `my_agent@127.0.0.1`).

The internal components of the SPADE agents that conduct their intelligence are the **Behaviors**. A behavior is a task
that an agent can run using different repeating patterns. SPADE agents can run several behaviors simultaneously. The
most basic behavior type is the cyclic behavior, which repeatedly executes the same method over and over again
indefinitely. This is the way to develop behaviors that wait for a perception, reason about it and finally execute an
action and wait again for the next perception.

The following example is a sample of an agent with a cyclic behavior (:class:`spade.Behaviour.Behaviour` type) that waits for
a perception of the keyboard input, reasons on it and executes an action, indefinitely until the user presses Ctrl+C.
To build a behavior you must inherit from the type of behavior you want (in the case of this example the cyclic
behaviour is implemented in the class :class:`spade.Behaviour.Behaviour`) and overload the method :func:`_process`
where the body of the behavior is implemented. If needed you can also overload the :func:`onStart` and :func:`onEnd`
methods to perform actions on the initialization or shutdown of a behavior

.. code-block:: python

    import spade
    import datetime
    import time

    class MyAgent(spade.Agent.Agent):
        class MyBehavior(spade.Behaviour.Behaviour):

            def onStart(self):
                print("Initialization of behavior")

            def _process(self):
                # wait for perception, raw_input is a blocking call
                perception = raw_input("What's your birthday year?")
                # reason about the perception
                age = datetime.datetime.now().year - perception
                # execute an action
                print("You are " + str(age) + " years old.")

            def onEnd(self):
                print("Shutdown of behavior")

        def _setup(self):
            # Create behavior
            behavior = self.MyBehavior()
            # Register behavior in agent
            self.addBehaviour(behavior)

    if __name__ == "__main__":
        a = MyAgent(agentjid="agent@127.0.0.1", password="secret")
        a.start()
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
        a.stop()


There are also other types of behaviors like one-shot behaviors, periodic behaviors, finite-state machine behaviors, etc.

Communication API, Messages and Templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Communication is one of the cornerstones of a multi-agent system and SPADE is no exception. Agents can send and receive
messages using a simple API and even more, they can receive them in certain behaviors according to templates they can
define.

A :class:`spade.ACLMessage.ACLMessage` is the class that needs to be filled in order to send a message. It follows the
`FIPA Agent Communication Language` specifications or `FIPA ACL <http://www.fipa.org/repository/aclspecs.html>`_. An
ACLMessage may be filled with several information, but the most important fields are the receiver, the content, the
performative and the protocol. The receiver must be filled with an :class:`spade.AID.aid` object, which is an AgentID.
The content is a string-based body of the message. The performative and protocol both add semantic information to the
conversation. They are usually used to represent the action and the rules that determine how the agents are going to
communicate in a specific semantic context.

.. tip::
    It's usually recommended to use a representation language for the content of the message. There are semantic
    languages like OWL or RDF, but in the case of this simulator we use JSON representation for ease of use.

All these fields have a getter and setter function. An example is shown next:

.. code-block:: python

    import spade

    receiver_aid = spade.AID.aid(name="receiver_agent@127.0.0.1",
                                 addresses=["xmpp://receiver_agent@127.0.0.1"])
    msg = spade.ACLMessage.ACLMessage()
    msg.addReceiver(receiver_aid)  # a message may be sent to multiple receivers
    msg.setPerformative("request")
    msg.setProtocol("my_custom_protocol")
    msg.setBody("{'a_key': 'a_value'}")

.. hint::
    Other fields that can be filled in the message are the content language (:func:`setLanguage`), the ontology
    (:func:`setOntology`) and so on.

The next step is to send the message. This is done with the :func:`send` method provided by a :class:`Behaviour`.
See an example:

.. code-block:: python

    import spade


    class SenderAgent(spade.Agent.Agent):
        class SendBehav(spade.Behaviour.OneShotBehaviour):

            def _process(self):
                receiver = spade.AID.aid(name="receiver@127.0.0.1",
                                         addresses=["xmpp://127.0.0.1"])

                msg = spade.ACLMessage.ACLMessage()
                msg.setPerformative("inform")
                msg.setOntology("myOntology")
                msg.setLanguage("OWL-S")
                msg.addReceiver(receiver)
                msg.setContent("Hello World")

                self.send(msg)  # send the message

        def _setup(self):
            print "MyAgent starting..."
            behav = self.SendBehav()
            self.addBehaviour(behav)


Since only behaviours can receive messages SPADE provides a mechanism to configure which behavior must receive each type
of message. This is done with `ACLTemplates`. When an agent receives a new message it checks if the message matches each
of the behaviors using a template with which they where registered. If there is a match, the message is delivered to the
mailbox of the corresponding behavior and will be read when the behavior executes the :func:`receive` method. Otherwise,
the message will be delivered to a default behaviour if it was registered (the default behavior is registered with the
:func:`setDefaultBehaviour` method instead of :func:`addBehaviour`).

.. note::
    The :func:`receive` method accepts an optional parameter: **timeout=seconds** to be a blocking method until the
    specified number of seconds has elapsed. If timeout is reached without a message, then ``None`` is returned. If timeout
    is 0, then the :func:`receive` function is non-blocking and returns a :class:`spade.ACLMessage.ACLMessage` or ``None``.

An :class:`spade.Behaviour.ACLTemplate` is created using the same API of :class:`spade.Behaviour.ACLMessage`:

.. code-block:: python

    import spade
    template = spade.Behaviour.ACLTemplate()
    template.setOntology("myOntology")


`ACLTemplates` must be wrapped with the :class:`spade.Behavior.MessageTemplate` to be registered with a behavior.

.. note::
    A :class:`spade.Behavior.MessageTemplate` accepts boolean operators to combine `ACLTemplates`
    (e.g. ``my_tpl = Message Template( template1 & template2)``)

At this point we can already see how to build an agent that registers a behavior with a template and receives messages
that match that template:

.. code-block:: python

    import spade
    import time

    class RecvAgent(spade.Agent.Agent):
        class ReceiveBehav(spade.Behaviour.Behaviour):

            def _process(self):
                msg = self.receive(timeout=10)

                # Check wether the message arrived
                if msg is not None:
                    assert "myOntology" == msg.getOntology()
                    print("I got a message with the ontology 'myOntology'")
                else:
                    print("I waited 10 seconds but got no message")
                    time.sleep(1)

        def _setup(self):
            recv_behav = self.ReceiveBehav()
            template = spade.Behaviour.ACLTemplate()
            template.setOntology("myOntology")
            msg_tplt = spade.Behaviour.MessageTemplate(template)

            self.addBehaviour(recv_behav, msg_tplt)


These are the basics of SPADE programming. To use `Taxi Simulator` you would not need to create all these structures,
templates and classes. But it is always better to know the foundations before we get down to business.

How to implement your own strategies
====================================

Taxi simulator is designed to allow students to implement and test new strategies that lead to system optimization. The
goal of this educational simulator is to maker easier for students to work with new coordination strategies without going
down to the mud. With this purpose, Taxi Simulator implements the Strategy design pattern, which allows students to test
new coordination strategies without having to make major modifications in the application.

The Strategy Pattern
--------------------

The **Strategy pattern** is a design pattern that enables selecting an algorithm at runtime. When in an application we
have to implement different versions of an algorithm and we want to select at runtime a specific version of the
algorithm, then the Strategy Pattern is the best choice for that purpose. With this pattern you can define a separate
strategy in an object that encapsulates the algorithm. The application that executes the algorithm **must** define an
interface that every implementation of the strategy will follow, as can be viewed in next figure:

.. figure:: images/strategy.png
    :align: center
    :alt: The Strategy Pattern UML

    The Strategy Pattern UML

Following this implementation the context object can call the current strategy implementation without knowing how the
algorithm was implemented. This design pattern was created among others by a group of authors commonly known as the
**Gang of Four** (E. Gamma, R. Helm, R. Johnson and J. Vlissides) and is well presented in [GangOfFour95]_.

Taxi Simulator uses the *Strategy Pattern* to allow students to implement three different strategies (one for the
coordinator agent, one for the taxi agent and one for the passenger agent) without having to develop new agents or
entering in the complexity of the simulator. Thanks to this pattern students can develop their strategies in an external
file and pass it as an argument when the simulator is run.

Taxi Simulator implements three interfaces for these agents and each interface provides also some helper functions that
intend to make easier some common actions that each subclassed agent usually has to do. These three interfaces inherit
from the :class:`StrategyBehaviour` class and are called: :class:`CoordinatorStrategyBehaviour`,
:class:`TaxiStrategyBehaviour` and :class:`PassengerStrategyBehaviour`.

.. figure:: images/strategybehavior.png
    :align: center
    :alt: The StrategyBehaviour class and their inherited interfaces

    The StrategyBehaviour class and their inherited interfaces


The Strategy Behaviour
----------------------

The :class:`StrategyBehaviour` is the metaclass from which interfaces are created for the strategies of each agent in
the simulator. It inherits from a :class:`spade.Behaviour.Behaviour` class, so when implementing it you will have to
overload the :func:`_process` method that will run cyclically endlessly until the agent stops.

Helpers
~~~~~~~

The Strategy Behaviour provides also some helper functions that are widely useful for any kind of agent in the simulator.
We have already read about the :func:`send` and :func:`receive` functions, that allow agents to comunicate with each
other. The rest of the helper functions allow to store and retrieve information in the agent and to log messages.

.. code-block:: python

    def receive(self, timeout=5)
    def send(self, message)

    def store_value(self, key, value)
    def get_value(self, key)
    def has_value(self, key)


.. danger::
    Don't store information in the Behaviour itself since it is a cyclic behaviour and is run by calling repeteadly the
    :func:`_process` function, so the context of the function is not persisted.

The :func:`store_value`, :func:`get_value` and :func:`has_value` functions allow to store persistent information in the
agent and to recover it at any moment. The store uses a *key-value* interface to store your data.

There is also a very useful helper function which is the **logger**. This is not really a function but a system of logs
which can be used to generate debug information at different levels. There are four levels of logging which are, in
order of importance, the following:

* **DEBUG**
    Used with ``self.logger.debug("my debug message")``. These messages are only shown when the simulator is
    called with the ``-v`` option. This is usually superfluous information.
* **INFO**
    Used with ``self.logger.info("my info message")``. These messages are always shown and are the regular
    information shown in logs.
* **WARNING**
    Used with ``self.logger.warn("my warning message")``. These messages are always shown and are used to
    show warnings to the user.
* **ERROR**
    Used with ``self.logger.error("my error message")``. These messages are always shown are are used to show
    errors to the user.


Developing the Coordinator Agent Strategy
-----------------------------------------

To develop a new strategy for the Coordinator Agent you need to create a class that inherits
:class:`CoordinatorStrategyBehaviour`. Since this is a cyclic behaviour class that follows the *Strategy Pattern* and
that inherits from the :class:`StrategyBehaviour`, it has all the previously presented helper functions for
communication and storing data inside the agent.

Following the *REQUEST* protocol, the Coordinator agent is supposed to receive every request for a taxi from passengers
and to carry out the action that your strategy determines (remember that in the default strategy
:class:`DelegateRequestTaxiBehaviour` the coordinator delegates the decision to all the taxis by redirecting all
requests to all taxis without any previous or or further reasoning).

The place in the code where your coordinator strategy must be coded is the :func:`_process` function. This
function is executed in an infinite loop until the agent stops. In addition, you may overload also the :func:`onStart`
and the :func:`onEnd` functions to execute code before the creation of the strategy or after its destruction.

Code
~~~~
As an example, this is the code of the default coordinator strategy :class:`DelegateRequestTaxiBehaviour`:

.. code-block:: python

    from taxi_simulator.coordinator import CoordinatorStrategyBehaviour
    from taxi_simulator.helpers import coordinator_aid

    class DelegateRequestTaxiBehaviour(CoordinatorStrategyBehaviour):
        def _process(self):
            msg = self.receive(timeout=60)
            if msg:
                msg.removeReceiver(coordinator_aid)
                for taxi in self.get_taxi_agents():
                    msg.addReceiver(taxi.getAID())
                    self.logger.debug("Coordinator sent request to taxi {}".format(taxi.getName()))
                self.send(msg)


Helpers
~~~~~~~

To make it easier for the student, the coordinator agent has two helper functions that allow her to recover a list of
all the taxi agents and passenger agents registered in the system. These functions are:

* :func:`get_taxi_agents`

    Returns a list of the taxi agents.

* :func:`get_passenger_agents`

    Returns a list of the passenger agents.

Developing the Taxi Agent Strategy
----------------------------------
To develop a new strategy for the Taxi Agent you need to create a class that inherits
:class:`TaxiStrategyBehaviour`. Since this is a cyclic behaviour class that follows the *Strategy Pattern* and
that inherits from the :class:`StrategyBehaviour`, it has all the previously presented helper functions for
communication and storing data inside the agent.

The taxi strategy is intended to receive requests from passengers, forwarded by the coordinator agent, and to send proposals
to that passengers in order to be selected by the corresponding passenger. If the taxi proposal is accepted, then it
begins the process of going to the passenger's place, picking her up and taking her to the requested destination.

.. warning::
    The process that implies a taxi movement is out of the scope of the strategy and should not be addressed by the
    strategy implementation. This pasenger transfer process is automatically triggered when the strategy executes the
    helper function :func:`pick_up_passenger` (which is supposed to be the last action of a taxi strategy).

The place in the code where your taxi strategy must be coded is the :func:`_process` function. This
function is executed in an infinite loop until the agent stops. In addition, you may overload also the :func:`onStart`
and the :func:`onEnd` functions to execute code before the creation of the strategy or after its destruction.

Code
~~~~
The default strategy of a taxi is to accept every passenger's requests if the taxi is not assigned to any other passenger
or waiting a confirmation from any passenger.
As an example, this is the code of the default taxi strategy :class:`AcceptAlwaysStrategyBehaviour`:

.. code-block:: python

    from taxi_simulator.taxi import TaxiStrategyBehaviour

    class AcceptAlwaysStrategyBehaviour(TaxiStrategyBehaviour):
        def _process(self):
            # wait for a message
            msg = self.receive(timeout=60)
            if not msg:
                # return if no new message
                return
            content = content_to_json(msg)  # deserialize string content to JSON
            performative = msg.getPerformative()

            self.logger.debug("Taxi {} received request protocol from passenger {}."
                              .format(self.myAgent.agent_id, content["passenger_id"]))
            # a new request from a passenger has arrived
            if performative == REQUEST_PERFORMATIVE:
                if self.myAgent.status == TAXI_WAITING:
                    # send a proposal with an empty content and wait for approval
                    self.send_proposal(content["passenger_id"], {})
                    self.myAgent.status = TAXI_WAITING_FOR_APPROVAL

            # my proposal has been accepted (Hooray!)
            elif performative == ACCEPT_PERFORMATIVE:
                # I should only receive an ACCEPT if I was waiting for it
                if self.myAgent.status == TAXI_WAITING_FOR_APPROVAL:
                    self.logger.debug("Taxi {} got accept from {}"
                                      .format(self.myAgent.agent_id, content["passenger_id"]))
                    try:
                        # Change my status to MOVING and trigger pick_up_passenger. Strategy is done.
                        self.myAgent.status = TAXI_MOVING_TO_PASSENGER
                        self.pick_up_passenger(content["passenger_id"], content["origin"], content["dest"])

                    except PathRequestException:
                        # If taxi is not able to get a path to the passenger, then it is forced to cancel
                        self.logger.error("Taxi {} could not get a path to passenger {}. Cancelling..."
                                          .format(self.myAgent.getName(), content["passenger_id"]))
                        self.myAgent.status = TAXI_WAITING
                        self.cancel_proposal(content["passenger_id"])

                    except Exception as e:
                        self.logger.error("Unexpected error in taxi {name}: {exception}"
                                          .format(name=self.myAgent.getName(), exception=e))
                        self.cancel_proposal(content["passenger_id"])
                        self.myAgent.status = TAXI_WAITING

                else:  # If I was not waiting for an ACCEPT then cancel proposal with the passenger
                    self.cancel_proposal(content["passenger_id"])

            # my proposal has been refused. Don't worry, return to WAITING status and get over it.
            elif performative == REFUSE_PERFORMATIVE:
                self.logger.debug("Taxi {} got refusal from {}".format(self.myAgent.agent_id,
                                                                       content["passenger_id"]))
                self.myAgent.status = TAXI_WAITING
Helpers
~~~~~~~

In the example below there are some helper functions that are specific for the taxi strategy. These are:

.. code-block:: python

            def send_proposal(self, passenger_id, content=None)
            def cancel_proposal(self, passenger_id, content=None)
            def pick_up_passenger(self, passenger_id, origin, dest)


Let's present each one of them.

* :func:`send_proposal`

    This helper function simplifies the composition and sending of a message to a passenger with a proposal. It sends an
    :class:`ACLMessage` to ``passenger_id`` using the **REQUEST_PROTOCOL** and a **PROPOSE_PERFORMATIVE**. It optionally
    accepts a `content` parameter where you can include any information you may want the receiver to analyze.

* :func:`cancel_proposal`

    This helper function simplifies the composition and sending of a message to a passenger to cancel a proposal. It sends an
    :class:`ACLMessage` to ``passenger_id`` using the **REQUEST_PROTOCOL** and a **CANCEL_PERFORMATIVE**. It optionally
    accepts a `content` parameter where you can include any information you may want the receiver to analyze.

* :func:`pick_up_passenger`

    This helper function triggers the **TRAVEL_PROTOCOL** of a taxi, which is the protocol that is used to transfer a
    passenger from its origin to its destination. This is an important function since it is usually the last action that a
    taxi strategy does, since from this point an alternative behaviour of the agent to transport the passenger begins and
    the strategy has finished its purpose (until the taxi is free again and receives a new request from a new passenger).

    The :func:`pick_up_passenger` helper function receives as parameters the id of the passenger and the coordinates of the
    passenger's current position (``origin``) and its destination (``dest``).


Developing the Passenger Agent Strategy
---------------------------------------

To develop a new strategy for the Passenger Agent you need to create a class that inherits
:class:`PassengerStrategyBehaviour`. Since this is a cyclic behaviour class that follows the *Strategy Pattern* and
that inherits from the :class:`StrategyBehaviour`, it has all the previously presented helper functions for
communication and storing data inside the agent.

The passenger strategy is intended to ask for a taxi to the coordinator agent, then wait for taxi proposals and, after
evaluating them, choosing a taxi proposal to be taken to her destination.

The place in the code where your passenger strategy must be coded is the :func:`_process` function. This
function is executed in an infinite loop until the agent stops. In addition, you may overload also the :func:`onStart`
and the :func:`onEnd` functions to execute code before the creation of the strategy or after its destruction.


Code
~~~~
The default strategy of a Passenger agent is a dummy strategy that accepts the first proposal it receives.
As an example, this is the code of the default passenger strategy :class:`AcceptFirstRequestTaxiBehaviour`:

.. code-block:: python

    from taxi_simulator.passenger import PassengerStrategyBehaviour

    class AcceptFirstRequestTaxiBehaviour(PassengerStrategyBehaviour):
        def _process(self):
            # If I'm waiting then send a new request
            if self.myAgent.status == PASSENGER_WAITING:
                self.send_request(content={})

            # wait 5 seconds for a proposal
            msg = self.timeout_receive(timeout=5)

            if msg:
                performative = msg.getPerformative()
                taxi_aid = msg.getSender()

                # If I got a proposal then I blindly accept it
                if performative == PROPOSE_PERFORMATIVE:
                    # But I accept it only if I was waiting for a proposal
                    if self.myAgent.status == PASSENGER_WAITING:
                        self.logger.debug("Passenger {} received proposal from taxi {}"
                                          .format(self.myAgent.agent_id, taxi_aid.getName()))
                        self.accept_taxi(taxi_aid)
                        self.myAgent.status = PASSENGER_ASSIGNED
                    else:
                        # Otherwise I refuse the proposal (since I wasn't waiting for it)
                        self.refuse_taxi(taxi_aid)

                # If I receive a CANCEL performative it means my taxi has given up and I'm waiting again
                elif performative == CANCEL_PERFORMATIVE:
                    if self.myAgent.taxi_assigned == taxi_aid.getName():
                        self.logger.warn("Passenger {} received a CANCEL performative from Taxi {}."
                                         .format(self.myAgent.agent_id, taxi_aid.getName()))
                        self.myAgent.status = PASSENGER_WAITING

Helpers
~~~~~~~
In the example below there are some helper functions that are specific for the passenger strategy. These are:

.. code-block:: python

    def send_request(self, content=None)
    def accept_taxi(self, taxi_aid)
    def refuse_taxi(self, taxi_aid)


Let's present each one of them.

* :func:`send_request`

    This helper is useful to make a new request without building the whole message (the helper functions makes it for you).
    It creates an `ACLMessage` with a **REQUEST** performative and sends it to the coordinator agent. In addition you can
    append a content to the request message to be used by the coordinator agent or the taxi agents (e.g. your origin
    coordinates or your destination coordinates).

* :func:`accept_taxi`

    This is a helper function to quickly send an acceptance message to a ``taxi_id``. It sends an `ACLMessage` with an
    **ACCEPT** performative to the selected taxi.

* :func:`refuse_taxi`

    This is a helper function to quickly refuse a proposal from a ``taxi_id``. It sends an `ACLMessage` with an **REFUSE**
    performative to the taxi whose proposal is being refused.

Other Helpers
-------------
Taxi Simulator comes also with a :mod:`helpers` module to provide some transversal support methods that may be useful
for any agent. In this section we are showing each one of them.

* :func:`build_aid`


    This function helps to create an :class:`spade.AID.aid` object using the name of an agent as a parameter. This helps to
    create a structure that is very used when working with spade agents. It accepts a string with the name of the agent
    (e.g. "coordinator") and returns a :class:`spade.AID.aid` instance to be used in a :class:`spade.ACLMessage.ACLMessage`.

    Example:

    .. code-block:: python

        taxi_aid = build_aid("taxi_1234")

        assert taxi_aid.getName() == "taxi_1234@127.0.0.1"
        assert taxi_aid.getAddresses() == ["xmpp://taxi_1234@127.0.0.1"]


* :const:`coordinator_aid`

    Since the coordinator agent is a very common agent and needed by almost every passenger and taxi agent, the
    :mod:`helpers` module provides a static :class:`spade.AID.aid` instance to communicate with the coordinator agent.

* :func:`content_to_json`

    Taxi Simulator uses the `JSON <https://www.json.org>`_ data-interchange format to use as the content language of the
    messages (however, you can use the language you want, like RDF, XML, OWL, etc.). To facilitate the use of the JSON
    format we provide this helper function that receives a :class:`spade.ACLMessage.ACLMessage` and returns the content
    of the message if JSON format (which is actually a :obj:`dict` object in Python).

    Example:

    .. code-block:: python

        msg = self.receive()

        assert msg.getContent() == "{'my_coords': [39.253, -0.341]}"
        assert content_to_json(msg) == {"my_coords": [39.253, -0.341]}

* :func:`random_position`

    This helper function returns a random position in the map for being used if you need to create a new coordinate.

    Example:

    .. code-block:: python

        assert random_position() == [39.253, -0.341]

* :func:`are_close`

    This helper function facilitates working with distances in maps. This helper function accepts two coordinates
    (:attr:`coord1` and :attr:`coord2`) and an optional parameter to set the tolerance in meters. It returns ``True`` if
    both coordinates are closer than the tolerance in meters (10 meters by default). Otherwise it returns ``False``.

    Example:

    .. code-block:: python

        assert are_close([39.253, -0.341], [39.351, -0.333], 1000) == True

* :func:`distance_in_meters`

    This helper function returns the distance in meters between two points.

    Example:

    .. code-block:: python

        assert distance_in_meters([-0.37565, 39.44447], [-0.40392, 39.45293]) == 3264.7134341427977


How to Implement New Strategies (Level 1) -- Recommendations
============================================================

At this point is time for you to implement your own strategies to optimize the problem of dispatching taxis to passengers.
In this chapter we have shown you the tools to create these strategies. You have to create a file (in this example we
are using ``my_strategy_file.py``) and develop the strategies to be tested following the next template:

.. code-block:: python

    from taxi_simulator.coordinator import CoordinatorStrategyBehaviour
    from taxi_simulator.passenger import PassengerStrategyBehaviour
    from taxi_simulator.taxi import TaxiStrategyBehaviour

    ################################################################
    #                                                              #
    #                     Coordinator Strategy                     #
    #                                                              #
    ################################################################
    class MyCoordinatorStrategy(CoordinatorStrategyBehaviour):
        def _process(self):
           # Your code here

    ################################################################
    #                                                              #
    #                         Taxi Strategy                        #
    #                                                              #
    ################################################################
    class MyTaxiStrategy(TaxiStrategyBehaviour):
        def _process(self):
           # Your code here

    ################################################################
    #                                                              #
    #                       Passenger Strategy                     #
    #                                                              #
    ################################################################
    class MyPassengerStrategy(PassengerStrategyBehaviour):
        def _process(self):
           # Your code here


In this file, three strategies have been created for the three types of agent handled by the simulator. We have called
these strategies :class:`MyCoordinatorStrategy`, :class:`MyTaxiStrategy` and :class:`MyPassengerStrategy`.

To run the simulator with your new strategies the command line interface accepts three parameters with the name of the
file (without extension) and the name of the class of each strategy.

.. code-block:: bash

 $ taxi_simulator --taxi my_strategy_file.MyTaxiStrategy
                  --passenger my_strategy_file.MyPassengerStrategy
                  --coordinator my_strategy_file.MyCoordinatorStrategy

.. warning::
    The file must be in the current working directory and it must be referenced *without* the extension (if the file is
    named ``my_strategy_file.py`` use ``my_strategy_file`` when calling the simulator.

Once run the simulator you can test your strategies using the graphical web interface or by inspecting the output of the
logs in the command line.

.. [GangOfFour95] E. Gamma, R. Helm, R. Johnson, and J. Vlissides. Design Patterns, Elements of Reusable Object Oriented Software. Addison-Wesley, 1995.

