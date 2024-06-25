import datetime
import json
import time
from asyncio import CancelledError

from loguru import logger
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template


from simfleet.communications.protocol import (
        ACCEPT_PERFORMATIVE,
        INFORM_PERFORMATIVE,
        REGISTER_PROTOCOL,
        REQUEST_PERFORMATIVE,
        TRAVEL_PROTOCOL,
        REQUEST_PROTOCOL
)

from simfleet.common.queuestationagent import QueueStationAgent
from simfleet.utils.utils_old import StrategyBehaviour, TRANSPORT_IN_CUSTOMER_PLACE



class BusStopAgent(QueueStationAgent):
    def __init__(self, agentjid, password, **kwargs):
        super().__init__(agentjid, password)

        #self.fleetmanager_id = kwargs.get('fleet', None)        # vehicle.py

        # Bus stop attributes
        self.stop_name = None
        self.position = None            #GeolocationAgent - current_pos
        self.lines = None

        #self.position = None
        #self.lines = None

        # Customer registry
        self.registered_customers = {}

        # Statistics
        self.total_customers = 0
        self.num_customers = [0]

        # Atribut afegit perque funcione
        self.type = None

    async def setup(self):
        await super().setup()
        logger.info("Stop agent {} running".format(self.name))
        self.set_type("stop")
        self.set_status()
        try:
            template1 = Template()
            template1.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = RegistrationBehaviour()

            template2 = Template()
            template2.set_metadata("protocol", REQUEST_PROTOCOL)
            template2.set_metadata("performative", INFORM_PERFORMATIVE)
            bus_stop_strategy_behaviour = BusStopStrategyBehaviour()

            self.add_behaviour(register_behaviour, template1)
            self.add_behaviour(bus_stop_strategy_behaviour, template2)
            while not self.has_behaviour(register_behaviour):
                logger.warning(
                    "Station {} could not create RegisterBehaviour. Retrying...".format(
                        self.agent_id
                    )
                )
                self.add_behaviour(register_behaviour, template1)


        except Exception as e:
            logger.error(
                "EXCEPTION creating RegisterBehaviour in Station {}: {}".format(
                    self.agent_id, e
                )
            )
        self.ready = True

    def set_name(self, name):
        self.stop_name = name

    def set_status(self, state=None):
        self.status = state

    def set_type(self, station_type):
        self.type = station_type

    def set_lines(self, lines):
        self.lines = lines

    def to_json(self):
        return {
            "id": self.agent_id,
            "name": self.stop_name,
            #"position": self.position,
            "position": self.get("current_pos"),
            "lines": self.lines,
            "icon": self.icon,
        }

    def run_strategy(self):
        """
        Sets the strategy for the stop agent.
        """
        if not self.running_strategy:
            #template = Template()
            #template.set_metadata("protocol", REQUEST_PROTOCOL)
            #self.add_behaviour(self.strategy(), template)
            self.running_strategy = True


class RegistrationBehaviour(CyclicBehaviour):
    async def on_start(self):
        logger.debug("Strategy {} started in directory".format(type(self).__name__))

    def set_registration(self, decision):
        self.agent.registration = decision

    async def send_registration(self):
        """
        Send a ``spade.message.Message`` with a proposal to directory to register.
        """
        logger.info(
            "Bus stop {} sent proposal to register to directory {}".format(
                self.agent.name, self.agent.directory_id
            )
        )

        content = {
            "jid": str(self.agent.jid),
            "type": "stops",
            "stop_name": self.agent.stop_name,
            #"position": self.agent.position,
            "position": self.get("current_pos"),
            "lines": self.agent.lines,
        }
        msg = Message()
        msg.to = str(self.agent.directory_id)
        msg.set_metadata("protocol", REGISTER_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

    async def run(self):
        try:
            if not self.agent.registration:
                await self.send_registration()
            msg = await self.receive(timeout=10)
            if msg:
                performative = msg.get_metadata("performative")
                if performative == ACCEPT_PERFORMATIVE:
                    self.set_registration(True)
                    logger.debug("Registration in the directory")
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error(
                "EXCEPTION in RegisterBehaviour of Station {}: {}".format(
                    self.agent.name, e
                )
            )

class BusStopStrategyBehaviour(CyclicBehaviour):
    """
    Class from which to inherit to create a stop strategy.
    You must overload the ```run`` coroutine
    """

    async def on_start(self):
        logger.debug(
            "Strategy {} started in transport {}".format(
                type(self).__name__, self.agent.name
            )
        )

    async def dequeue_customers(self, sender, line, list_of_stops=None):        #ADAPTAR A QUEUESTATIONAGENT
        """
        Sends a message to the all customers whose destination is in list_of_stops

        Args:
            list_of_stops (list): list of coordinates for each stop in the transport's route
        """
        sender = str(sender)

        if list_of_stops is not None:
            inform_to = []

            if self.agent.queuebehaviour.total_queue_size(line)>0:
                queue = self.agent.queuebehaviour.get_queue(line)

                for agent_info in queue:
                    if agent_info is not None:
                        agent, kwargs = agent_info

                        if kwargs["destination_stop"] in list_of_stops:          #Analizar el Kwargs de la estación
                            inform_to.append(agent)

                if len(inform_to) == 0:
                    logger.debug("Stop {} has no registered customer with destination in {}".format(self.agent.name,
                                                                                                    list_of_stops))
                await self.inform_customers(inform_to, sender)

            else:
                logger.debug("Stop {} on line {} has no customers waiting in the queue.".format(self.agent.name,
                                                                                                line))
        else:
            #DEPURACION
            logger.info(
                "DEPURACION busstop - sender: {},  line: {}, waitin_list: {}".format(
                    sender,
                    line,
                    self.agent.waiting_lists[line]
                )
            )
            self.agent.queuebehaviour.dequeue_agent_to_waiting_list(line, sender)


    async def inform_customers(self, inform_to, sender):

        for customer in inform_to:
            data = {"status": TRANSPORT_IN_CUSTOMER_PLACE, "transport": sender}
            msg = Message()
            msg.to = customer
            msg.set_metadata("protocol", REQUEST_PROTOCOL)
            msg.set_metadata("performative", INFORM_PERFORMATIVE)
            msg.body = json.dumps(data)
            await self.send(msg)


    async def run(self):

        msg = await self.receive(timeout=30)
        logger.debug("Bus stop {} received message: {}".format(self.agent.jid, msg))
        if msg:
            sender = msg.sender
            performative = msg.get_metadata("performative")
            content = json.loads(msg.body)
            # else if sender is transport
            if performative == INFORM_PERFORMATIVE:
                line = content["line"]

                #if content["list_of_stops"]:
                if "list_of_stops" in content:
                    list_of_stops = content["list_of_stops"]
                else:
                    list_of_stops = None

                logger.debug("Stop {} received message from transport {}, informing customers...".format(
                    self.agent.name, sender))
                # Content is list of line stops
                await self.dequeue_customers(sender, line, list_of_stops)

                #if msg.body is None: # Content is empty, indicating the customer is not in the station anymore
                #if content["dequeue_one"]:
                #    await self.delete_customer(sender)
                #else:
                    #if sender is transport
                    #content = json.loads(msg.body)
                #    logger.debug("Stop {} received message from transport {}, informing customers...".format(
                #        self.agent.name, sender))
                    # Content is list of line stops
                #    await self.inform_customers(sender, content)

# ORIGINAL
# class StopStrategyBehaviour(StrategyBehaviour):
#     """
#     Class from which to inherit to create a stop strategy.
#     You must overload the ```run`` coroutine
#     """
#
#     async def on_start(self):
#         logger.debug(
#             "Strategy {} started in transport {}".format(
#                 type(self).__name__, self.agent.name
#             )
#         )
#
#     async def register_customer(self, customer, destinationStop):       #ADAPTAR A QUEUESTATIONAGENT
#
#         self.agent.registered_customers[str(customer)] = destinationStop.get("destination")
#         logger.info("Stop {} registered customer {} --> {}".format(self.agent.name, customer,
#                                                                    destinationStop.get("destination")))
#         # Update statistics
#         self.agent.total_customers += 1
#         self.agent.num_customers.append(len(self.agent.registered_customers))
#         await self.accept_customer_register(customer)
#
#
#
#     async def accept_customer_register(self, customer, data=None):
#         """
#         Sends a message to the confirming the register of a customer
#
#         Args:
#             customer (string): jid of the customer to which the stop replies
#             data (dict, optional): complementary info about the status
#         """
#         if data is None:
#             data = {}
#         msg = Message()
#         msg.to = str(customer)
#         msg.set_metadata("protocol", REQUEST_PROTOCOL)
#         msg.set_metadata("performative", ACCEPT_PERFORMATIVE)
#         msg.body = json.dumps(data)
#         await self.send(msg)
#
#     async def delete_customer(self, customer):                      #ADAPTAR A QUEUESTATIONAGENT
#         logger.info("Stop {} deleted customer {} from registry".format(self.agent.name, customer))
#         del self.agent.registered_customers[str(customer)]
#
#     async def inform_customers(self, sender, list_of_stops):        #ADAPTAR A QUEUESTATIONAGENT
#         """
#         Sends a message to the all customers whose destination is in list_of_stops
#
#         Args:
#             list_of_stops (list): list of coordinates for each stop in the transport's route
#         """
#         sender = str(sender)
#
#         inform_to = []
#         for customer in self.agent.registered_customers.keys():
#             if self.agent.registered_customers.get(customer) in list_of_stops:
#                 inform_to.append(customer)
#
#         if len(inform_to) == 0:
#             logger.debug("Stop {} has no registered customer with destination in {}".format(self.agent.name,
#                                                                                             list_of_stops))
#         for customer in inform_to:
#             data = {"status": TRANSPORT_IN_CUSTOMER_PLACE, "transport": sender}
#             msg = Message()
#             msg.to = customer
#             msg.set_metadata("protocol", REQUEST_PROTOCOL)
#             msg.set_metadata("performative", INFORM_PERFORMATIVE)
#             msg.body = json.dumps(data)
#             await self.send(msg)
#
#     async def run(self):
#
#         msg = await self.receive(timeout=30)
#         logger.debug("Bus stop {} received message: {}".format(self.agent.jid, msg))
#         if msg:
#             sender = msg.sender
#             performative = msg.get_metadata("performative")
#             # if sender is customer
#             if performative == REQUEST_PERFORMATIVE:
#                 if msg.body is None: # Content is empty, indicating the customer is not in the station anymore
#                     await self.delete_customer(sender)
#                 else:
#                     # Content is destination stop
#                     content = json.loads(msg.body)
#                     if content["destination"] is not None:
#                         await self.register_customer(sender, content)
#             # else if sender is transport
#             elif performative == INFORM_PERFORMATIVE:
#                 content = json.loads(msg.body)
#                 logger.debug("Stop {} received message from transport {}, informing customers...".format(
#                     self.agent.name, sender))
#                 # Content is list of line stops
#                 await self.inform_customers(sender, content)
