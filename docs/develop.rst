
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
Taxi simulator is designed to allow students to implement and test new strategies that lead to system optimization. The
architecture of the simulator is built on a multi-agent system platform called SPADE. Although it is not necessary to
build new agents in order to develop new negotiation strategies (the simulator provides all the necessary agents), it
is interesting to know how they work and what methods they provide for the creation of negotiation strategies.

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

The following example is a sample of an agent with a cyclic behavior (spade. Behaviour. Behaviour type) that waits for
a perception of the keyboard input, reasons on it and executes an action, indefinitely until the user presses Ctrl+C::

    import spade
    import datetime
    import time

    class MyAgent(spade.Agent.Agent):
        class MyBehavior(spade.Behaviour.Behaviour):
            def _process(self):
                # wait for perception
                perception = input("What's your birthday year?") # this is a blocking call
                # reason about the perception
                age = datetime.datetime.now().year - perception
                # execute an action
                print("You are " + str(age) + " years old.")

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



