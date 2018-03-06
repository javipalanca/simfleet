
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
methods to perform actions on the initialization or shutdown of a behavior::

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

.. note::
    It's usually recommended to use a representation language for the content of the message. There are semantic
    languages like OWL or RDF, but in the case of this simulator we use JSON representation for ease of use.

All these fields have a getter and setter function. An example is shown next::

    import spade

    receiver_aid = spade.AID.aid(name="receiver_agent@127.0.0.1",
                                 addresses=["xmpp://receiver_agent@127.0.0.1"])
    msg = spade.ACLMessage.ACLMessage()
    msg.addReceiver(receiver_aid)  # a message may be sent to multiple receivers
    msg.setPerformative("request")
    msg.setProtocol("my_custom_protocol")
    msg.setBody("{'a_key': 'a_value'}")


.. note::
    Other fields that can be filled in the message are the content language (:func:`setLanguage`), the ontology
    (:func:`setOntology`) and so on.

The next step is to send the message. This is done with the :func:`send` method provided by a :class:`Behaviour`.
See an example::


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

An :class:`spade.Behaviour.ACLTemplate` is created using the same API of :class:`spade.Behaviour.ACLMessage`::

    import spade
    template = spade.Behaviour.ACLTemplate()
    template.setOntology("myOntology")


`ACLTemplates` must be wrapped with the :class:`spade.Behavior.MessageTemplate` to be registered with a behavior.

.. note::
    A :class:`spade.Behavior.MessageTemplate` accepts boolean operators to combine `ACLTemplates`
    (e.g. ``my_tpl = Message Template( template1 & template2)``)

At this point we can already see how to build an agent that registers a behavior with a template and receives messages
that match that template::

    import spade
    import time

    class RecvAgent(spade.Agent.Agent):
        class ReceiveBehav(spade.Behaviour.Behaviour):

            def _process(self):
                msg = self.receive(block=True, timeout=10)

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

It also provides some helper functions that are widely useful for any kind of agent in the simulator. We have already
read about the :func:`send` and :func:`receive` functions, that allow agents to comunicate with each other. The rest of
the helper functions allow to store and retrieve information in the agent.

.. warning::
    Don't store information in the Behaviour itself since it is a cyclic behaviour and is run by calling repeteadly the
    :func:`_process` function, so the context of the function is not persisted.

The :func:`store_value`, :func:`get_value` and :func:`has_value` functions allow to store persistent information in the
agent and to recover it at any moment. The store uses a *key-value* interface to store your data.


Description of Coordinator Agent
--------------------------------

Code
~~~~
Coordinator strategies must inherit from :class:`CoordinatorStrategyBehaviour`

Helpers
~~~~~~~


Description of Taxi Agent
-------------------------

Code
~~~~
Taxi strategies must inherit from :class:`TaxiStrategyBehaviour`

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
Passenger strategies must inherit from :class:`PassengerStrategyBehaviour`

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





.. [GangOfFour95] E. Gamma, R. Helm, R. Johnson, and J. Vlissides. Design Patterns, Elements of Reusable Object Oriented Software. Addison-Wesley, 1995.
