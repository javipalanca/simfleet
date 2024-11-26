=================
Agent Foundations
=================

The architecture of SimFleet is built on top of a multi-agent system platform called SPADE. Although it is not necessary to
build new agents in order to develop new coordination strategies (the simulator provides all the necessary agents), it
is interesting to know how they work and what methods they provide for the creation of coordination strategies.

Next we will present the SPADE platform and its main features. For more documentation you can visit their website
https://github.com/javipalanca/spade.

SPADE
=====
`SPADE` (Smart Python multi-Agent Development Environment) is a multi-agent system (MAS) platform based on the
`XMPP <http://www.xmpp.org>`_ technology and written in the `Python <http://www.python.org/>`_ programming language.
This technology offers by itself many features and facilities that ease the construction of MAS, such as an existing
communication channel, the concepts of users (agents) and servers (platforms) and an extensible communication protocol
based on XML.

Extensible Messaging and Presence Protocol (XMPP) is an open, XML-inspired protocol for near-real-time, extensible
instant messaging (IM) and presence information. The protocol is built to be open and free, asynchronous, decentralized,
secure, extensible and flexible. The latter two features allow XMPP not only to be an instant messaging protocol, but
also to be extended and used for many tasks and situations (`IoT <https://xmpp.org/uses/internet-of-things.html>`_,
`WebRTC <https://xmpp.org/uses/webrtc.html>`_, `social <https://xmpp.org/uses/social.html>`_, ...). SPADE itself uses
some XMPP extensions to provide extended features to its agents, such as remote procedure calls between agents
(`Jabber-RPC <https://xmpp.org/extensions/xep-0009.html>`_), file transfer
(`In-Band Bytestreams <https://xmpp.org/extensions/xep-0047.html>`_), an so on.


In order to fully understand how SPADE works, it is necessary to know how the agents are made up and how they
communicate. In the following sections we will summarize the SPADE agent model and its communication API.

Agent Model: Behaviours
=======================
SPADE agents are threaded-based objects that can be run concurrently and that are connected to a SPADE platform, which
internally runs an XMPP server. Each agent must provide an ID and password in order to be allowed to connect to the platform.
The agent ID is called JID and has the form of an email: a user name string plus a "`@`" character plus the IP address
of the SPADE server to connect to (e.g. `my_agent@127.0.0.1`).

The internal components of the SPADE agents that provide their intelligence are the **Behaviours**. A behaviour is a task
that an agent can run using some pre-defined repeating pattern. For example, the most basic behaviour type (pattern) is the so-called
cyclic behaviour, which repeatedly executes the same method over and over again, indefinitely. This is the way to develop
typical behaviours that wait for a perception, reason about it and finally execute an action, and then wait for the next
perception.

The following example is a sample of an agent with a cyclic behaviour (``spade.behaviour.CyclicBehaviour`` type) that waits for
a perception from the keyboard input, reasons on it and executes an action, and continues to do so indefinitely until
the user presses Ctrl+C. In order to build a behaviour, you need to inherit from the type of behaviour you want
(in the case of this example, the cyclic behaviour is implemented in the class ``spade.behaviour.CyclicBehaviour``)
and overload the coroutine ``run`` where the body of the behaviour is implemented. If needed, you can also overload
the ``on_start`` and ``on_end`` coroutines in order to execute actions on the initialization or shutdown of a behaviour,
respectively.

.. code-block:: python

    import spade
    import datetime
    import time

    class MyAgent(spade.agent.Agent):
        class MyBehaviour(spade.behaviour.CyclicBehaviour):

            async def on_start(self):
                print("Initialization of behaviour")

            async def run(self):
                # wait for perception, raw_input is a blocking call
                perception = raw_input("What's your birthday year?")
                # reason about the perception
                age = datetime.datetime.now().year - perception
                # execute an action
                print("You are {age} years old.".format(age=age))

            async def on_end(self):
                print("Shutdown of behaviour")

        async def setup(self):
            # Create behaviour
            behaviour = self.MyBehaviour()
            # Register behaviour in agent
            self.add_behaviour(behaviour)

    if __name__ == "__main__":
        a = MyAgent(jid="agent@127.0.0.1", password="secret")
        a.start()
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
        a.stop()

Along with the cyclic repeating pattern (or type), SPADE also provides several other types of behaviours, such as
like one-shot behaviours, periodic behaviours, finite-state machine behaviours, etc. It is important to note that
SPADE agents can execute many behaviours simultaneously, from the same or different types.


Communication API, Messages and Templates
=========================================
Communication is one of the cornerstones of any multi-agent system, and SPADE is no exception. Agents can send and receive
messages using a simple API, and more importantly, they can receive them in certain behaviours according to templates they can
define.

A ``spade.message.Message`` is the class that needs to be filled in order to send a message. A
Message may be filled with several pieces of information, but the most important fields are the receiver, the content, the
performative and the protocol. The receiver must be filled with a `jid` address , which is a string.
The content is the (string-based) body of the message. The performative and protocol both add semantic information to the
message in the context of a conversation: they are normally used to represent the action and the rules that determine
how the agents are going to communicate in a specific semantic context and they are represented as metadata.

.. tip::
    It is usually recommended to use a representation language for the content of the message. Although semantic
    languages like OWL or RDF are normally used for this purpose, in this simulator JSON is used instead, for the sake of
    simplicity.

All these fields have a getter and setter function. An example is shown next:

.. code-block:: python

    import spade

    msg = spade.message.Message()
    msg.to = "receiver_agent@127.0.0.1"
    msg.set_metadata("performative", "request")
    msg.set_metadata("protocol", "my_custom_protocol")
    msg.body = "{'a_key': 'a_value'}"

.. hint::
    Other metadata fields that can be filled in the message are the content language, the ontology, and so on.

The next step is to send the message. This is done with the ``send`` coroutine provided by a `Behaviour`.
For example:

.. code-block:: python

    import spade


    class SenderAgent(spade.agent.Agent):
        class SendBehav(spade.behaviour.OneShotBehaviour):

            async def run(self):
                msg = spade.message.Message()
                msg.to = "receiver@127.0.0.1"
                msg.set_metadata("performative", "inform")
                msg.set_metadata("ontology", "myOntology")
                msg.set_metadata("language", "OWL-S")
                msg.body = "Hello World"

                await self.send(msg)  # send the message

        async def setup(self):
            print "MyAgent starting..."
            behav = self.SendBehav()
            self.add_behaviour(behav)

The reception of messages is particular in SPADE, since messages can only be received by behaviours, and so
SPADE provides each behaviour executed by any agent with its own mailbox, and defines a mechanism in
order to configure the particular behaviour that must receive each message, according to the message type.
This mechanism is carried out with `Templates`. When an agent receives a new message it checks if the message matches each
of the behaviours using a template with which they where registered. If there is a match, the message is delivered to the
mailbox of the corresponding behaviour, and will be read when the behaviour executes the ``receive`` method. Otherwise,
the message will be dropped.

.. note::
    The ``receive`` coroutine accepts an optional parameter: **timeout=seconds**, which allows the coroutine to be
    blocking until the specified number of seconds have elapsed. If the timeout is reached without a message being
    received, then ``None`` is returned. If the timeout is set to 0, then the :func:`receive` function is non-blocking
    and (immediately) returns either a ``spade.message.Message`` or ``None``.

A ``spade.template.Template`` is created using the same API of ``spade.message.Message``:

.. code-block:: python

    import spade
    template = spade.template.Template()
    template.set_metadata("ontology", "myOntology")

.. note::
    A ``spade.template.Template`` accepts boolean operators to combine `Templates`
    (e.g. ``my_tpl = Template( template1 & template2)``)

At this point we can present a full example on how to build an agent that registers a behaviour with a template and receives messages
that match that template:

.. code-block:: python

    import spade
    import asyncio

    class RecvAgent(spade.agent.Agent):
        class ReceiveBehav(spade.behaviour.CyclicBehaviour):

            async def run(self):
                await msg = self.receive(timeout=10)

                # Check wether the message arrived
                if msg is not None:
                    assert "myOntology" == msg.get_metadata("ontology")
                    print("I got a message with the ontology 'myOntology'")
                else:
                    print("I waited 10 seconds but got no message")

        async def setup(self):
            recv_behav = self.ReceiveBehav()
            template = spade.template.Template()
            template.set_metadata("ontology", "myOntology")

            self.add_behaviour(recv_behav, template)


These are the basics of SPADE programming. You will not need to create all these structures, templates and classes
in order to use `SimFleet`, but it is always better to know the foundations before getting down to business.
