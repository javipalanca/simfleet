import asyncio
import json
import time
from asyncio import CancelledError
from collections import defaultdict

from loguru import logger
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template

from simfleet.utils.helpers import new_random_position
from simfleet.utils.utils_old import (
    CUSTOMER_WAITING,
    CUSTOMER_IN_DEST,
    TRANSPORT_MOVING_TO_CUSTOMER,
    CUSTOMER_IN_TRANSPORT,
    TRANSPORT_IN_CUSTOMER_PLACE,
    CUSTOMER_LOCATION,
    StrategyBehaviour,
    request_path,
    status_to_str,
)

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    TRAVEL_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    QUERY_PROTOCOL,
)

#from simfleet.common.agents.customer import CustomerAgent
#from simfleet.common.movable import MovableMixin

from simfleet.common.extensions.customers.models.pedestrian import PedestrianAgent

#class BusCustomerAgent(MovableMixin, CustomerAgent):
#class BusCustomerAgent(CustomerAgent):
class BusCustomerAgent(PedestrianAgent):
    def __init__(self, agentjid, password):
        #CustomerAgent.__init__(self, agentjid, password)
        #MovableMixin.__init__(self)
        super().__init__(agentjid, password)

        # Bus line attributes
        self.__observers = defaultdict(list)
        self.current_stop = None
        self.destination_stop = None
        self.type_service = "stops"
        self.registered_in = None
        self.stop_dic = None
        self.in_transport_time = None
        self.total_sim_time = None
        self.alternative_transports = []

        #New atribute
        self.line = None
        self.arguments = {}

        # Transport in stop event
        self.set("arrived_to_destination", None)  # new
        self.customer_arrived_to_destination_event = asyncio.Event(loop=self.loop)

        def customer_arrived_to_destination_callback(old, new):
            if not self.customer_arrived_to_destination_event.is_set() and new is True:
                self.customer_arrived_to_destination_event.set()

        self.customer_arrived_to_destination_callback = customer_arrived_to_destination_callback

    def set_line(self, line):
        self.line = line

    def run_strategy(self):
        """import json
        Runs the strategy for the customer agent.
        """
        if not self.running_strategy:
            template1 = Template()
            template1.set_metadata("protocol", REQUEST_PROTOCOL)
            # template2 = Template()
            # template2.set_metadata("protocol", QUERY_PROTOCOL)
            # self.add_behaviour(self.strategy(), template1 | template2)
            self.add_behaviour(self.strategy(), template1)
            self.running_strategy = True

    # Bus line
    def get_waiting_time_bus(self):
        if self.waiting_for_pickup_time is not None:
            return self.waiting_for_pickup_time
        elif self.init_time is not None:
            if self.pickup_time is not None:
                return self.pickup_time - self.init_time
            else:
                return time.time() - self.init_time
        else:
            return None

    def in_transport_time_bus(self):
        if self.pickup_time:
            if self.end_time:
                return self.end_time - self.pickup_time
            else:
                return time.time() - self.pickup_time
        else:
            return None

    def get_waiting_for_pickup_time(self):
        return self.waiting_for_pickup_time

    def get_in_transport_time(self):
        return self.in_transport_time

    def get_total_sim_time(self):
        return self.total_sim_time

    def get_pickup_time(self):
        """
        Returns the time that the customer was waiting to be picked up since it has been assigned to a transport.

        Returns:
            float: The time that the customer was waiting to a transport since it has been assigned.
        """
        if self.pickup_time:
            return self.pickup_time - self.waiting_for_pickup_time
        return None


    def watch_value(self, key, callback):
        """
        Registers an observer callback to be run when a value is changed

        Args:
            key (str): the name of the value
            callback (function): a function to be called when the value changes. It receives two arguments: the old and the new value.
        """
        self.__observers[key].append(callback)


    async def set_position(self, coords=None):      #ANALIZAR CAMBIO - NOTAS
        """
        Sets the position of the customer. If no position is provided it is located in a random position.

        Args:
            coords (list): a list coordinates (longitude and latitude)
        """
        await super().set_position(coords)
        self.set("current_pos", coords)

        #if coords == self.dest:

        #if self.is_in_destination():
        if self.destination_stop[1] == self.get_position():

            logger.success("Customer {} arrived to its destination {}".format(self.name, self.destination_stop[1]))
            self.status = CUSTOMER_IN_DEST
            self.set("arrived_to_destination", True)  # launch callback, awake FSMStrategyBehaviour
            self.end_time = time.time()


    async def setup(self):
        await super().setup()

        # ORIGINAL CODE - BUS
        # try:
        #     template = Template()
        #     template.set_metadata("protocol", TRAVEL_PROTOCOL)
        #     travel_behaviour = BusTravelBehaviour()
        #     self.add_behaviour(travel_behaviour, template)
        #     while not self.has_behaviour(travel_behaviour):
        #         logger.warning(
        #             "Customer {} could not create TravelBehaviour. Retrying...".format(
        #                 self.agent_id
        #             )
        #         )
        #         self.add_behaviour(travel_behaviour, template)
        #     self.ready = True
        # except Exception as e:
        #     logger.error(
        #         "EXCEPTION creating TravelBehaviour in Customer {}: {}".format(
        #             self.agent_id, e
        #         )
        #     )



# Bus line
class BusTravelBehaviour(CyclicBehaviour):
    """
    This is the internal behaviour that manages the movement of the customer.
    It is triggered when the transport informs the customer that it is going to the
    customer's position until the customer is dropped in its destination.
    """

    async def on_start(self):
        logger.debug("Customer {} started Bus Travel Behavior.".format(self.agent.name))

    async def run(self):
        try:
            msg = await self.receive(timeout=5)
            if not msg:
                return
            content = json.loads(msg.body)
            # logger.debug("Customer {} informed of: {}".format(self.agent.name, content))
            if "status" in content:
                status = content["status"]
                if status != CUSTOMER_LOCATION:
                    logger.debug(
                        "Customer {} informed of status: {}".format(
                            self.agent.name, status_to_str(status)
                        )
                    )
                if status == CUSTOMER_LOCATION:
                    coords = content["location"]
                    self.agent.set_position(coords)
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error(
                "EXCEPTION in Bus Travel Behaviour of Customer {}: {}".format(
                    self.agent.name, e
                )
            )

class BusCustomerStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a transport strategy.
    You must overload the ``run`` coroutine

    Helper functions:
        * ``send_request``
        * ``accept_transport``
        * ``refuse_transport``
    """

    async def on_start(self):
        """
        Initializes the logger and timers. Call to parent method if overloaded.
        """
        logger.debug(
            "Strategy {} started in customer {}".format(
                type(self).__name__, self.agent.name
            )
        )
        # Bus line
        # self.agent.init_time = time.time()

    async def send_get_managers(self, content=None):
        """
        Sends an ``spade.message.Message`` to the DirectoryAgent to request a managers.
        It uses the QUERY_PROTOCOL and the REQUEST_PERFORMATIVE.
        If no content is set a default content with the type_service that needs
        Args:
            content (dict): Optional content dictionary
        """
        if content is None or len(content) == 0:
            content = self.agent.fleet_type
        msg = Message()
        msg.to = str(self.agent.directory_id)
        msg.set_metadata("protocol", QUERY_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = content
        await self.send(msg)

        logger.info(
            "Customer {} asked for managers to directory {} for type {}.".format(
                self.agent.name, self.agent.directory_id, self.agent.type_service
            )
        )

    async def send_request(self, content=None):
        """
        Sends an ``spade.message.Message`` to the fleetmanager to request a transport.
        It uses the REQUEST_PROTOCOL and the REQUEST_PERFORMATIVE.
        If no content is set a default content with the customer_id,
        origin and target coordinates is used.

        Args:
            content (dict): Optional content dictionary
        """
        if not self.agent.customer_dest:
            self.agent.customer_dest = new_random_position(self.agent.boundingbox, self.agent.route_host)
        if content is None or len(content) == 0:
            content = {
                "customer_id": str(self.agent.jid),
                "origin": self.agent.get("current_pos"),
                "dest": self.agent.customer_dest,
            }

        if self.agent.fleetmanagers is not None:
            for (
                fleetmanager
            ) in self.agent.fleetmanagers.keys():  # Send a message to all FleetManagers
                msg = Message()
                msg.to = str(fleetmanager)
                msg.set_metadata("protocol", REQUEST_PROTOCOL)
                msg.set_metadata("performative", REQUEST_PERFORMATIVE)
                msg.body = json.dumps(content)
                await self.send(msg)
            logger.info(
                "Customer {} asked for a transport to {}.".format(
                    self.agent.name, self.agent.customer_dest
                )
            )
        else:
            logger.warning("Customer {} has no fleet managers.".format(self.agent.name))

    async def accept_transport(self, transport_id):
        """
        Sends a ``spade.message.Message`` to a transport to accept a travel proposal.
        It uses the REQUEST_PROTOCOL and the ACCEPT_PERFORMATIVE.

        Args:
            transport_id (str): The Agent JID of the transport
        """
        reply = Message()
        reply.to = str(transport_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
        content = {
            "customer_id": str(self.agent.jid),
            "origin": self.agent.get("current_pos"),
            "dest": self.agent.dest,
        }
        reply.body = json.dumps(content)
        await self.send(reply)
        self.agent.transport_assigned = str(transport_id)
        logger.info(
            "Customer {} accepted proposal from transport {}".format(
                self.agent.name, transport_id
            )
        )

    async def refuse_transport(self, transport_id):
        """
        Sends an ``spade.message.Message`` to a transport to refuse a travel proposal.
        It uses the REQUEST_PROTOCOL and the REFUSE_PERFORMATIVE.

        Args:
            transport_id (str): The Agent JID of the transport
        """
        reply = Message()
        reply.to = str(transport_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", REFUSE_PERFORMATIVE)
        content = {
            "customer_id": str(self.agent.jid),
            "origin": self.agent.get("current_pos"),
            "dest": self.agent.dest,
        }
        reply.body = json.dumps(content)

        await self.send(reply)
        logger.info(
            "Customer {} refused proposal from transport {}".format(
                self.agent.name, transport_id
            )
        )

    # Bus line
    async def send_get_stops(self, content=None):
        """
        Sends an ``spade.message.Message`` to the DirectoryAgent to request the list of stops in the system.
        It uses the QUERY_PROTOCOL and the REQUEST_PERFORMATIVE.
        If no content is set a default content with the type_service that needs
        Args:
            content (dict): Optional content dictionary
        """
        if content is None or len(content) == 0:
            content = "stops"
        msg = Message()
        msg.to = str(self.agent.directory_id)
        msg.set_metadata("protocol", QUERY_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = content
        await self.send(msg)

        logger.info(
            "Customer {} asked for stops to directory {} for type {}.".format(
                self.agent.name, self.agent.directory_id, self.agent.type_service
            )
        )

    # def setup_stops_original(self):
    #     for jid in self.agent.stop_dic.keys():
    #         stop_info = self.agent.stop_dic.get(jid)
    #         # Set origin stop
    #         if stop_info.get("position") == self.agent.get("current_pos"):
    #             self.agent.current_stop = stop_info
    #         # Set destination stop
    #         if stop_info.get("position") == self.agent.dest:
    #             self.agent.destination_stop = stop_info
    #     logger.debug("Customer {} set current_stop {} and destination_stop {}".format(self.agent.name,
    #                                                                                   self.agent.current_stop.get(
    #                                                                                       "jid"),
    #                                                                                   self.agent.destination_stop.get(
    #                                                                                       "jid")))

    def setup_stops(self):
        if self.agent.current_stop is None and self.agent.destination_stop is None:
            # current_bus_stop, current_position = self.agent.nearst_agent(self.agent.stop_dic, self.agent.get_position())
            self.agent.current_stop = self.agent.nearst_agent(self.agent.stop_dic, self.agent.get_position())

            # destination_bus_stop, destination_position = self.agent.nearst_agent(self.agent.stop_dic, self.agent.dest)
            self.agent.destination_stop = self.agent.nearst_agent(self.agent.stop_dic, self.agent.dest)

            logger.debug("Customer {} set current_stop {} and destination_stop {}".format(self.agent.name,
                                                                                      self.agent.current_stop[0],
                                                                                      self.agent.destination_stop[0]))

    async def register_to_stop(self, content):  # ANALIZAR Y REDISEÑO
        # content = {"destination": self.agent.destination_stop.get("position")}
        if content is None:
            content = {}
        msg = Message()
        # msg.to = self.agent.current_stop.get("jid")
        msg.to = self.agent.current_stop[0]
        msg.set_metadata("protocol", REQUEST_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        logger.debug("Customer {} asked to register to stop {} with destination {}".format(self.agent.name,
                                                                                           self.agent.current_stop[0],
                                                                                           self.agent.destination_stop[
                                                                                               1]))
        await self.send(msg)

    async def board_transport(self, transport):
        content = {
            "customer_id": str(self.agent.jid),
            "origin": self.agent.get("current_pos"),
            #"dest": self.agent.dest,
            "dest": self.agent.destination_stop[1],
        }
        msg = Message()
        msg.body = json.dumps(content)
        msg.to = str(transport)
        msg.set_metadata("protocol", REQUEST_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        await self.send(msg)

    async def inform_stop(self, content):

        if content is None:
            content = {}
        msg = Message()
        #msg.to = self.agent.current_stop.get("jid")
        msg.to = self.agent.current_stop[0]
        msg.set_metadata("protocol", REQUEST_PROTOCOL)
        #msg.set_metadata("performative", REQUEST_PERFORMATIVE)     #CHANGE - FOR DEQUEUE IN QUEUESTATIONAGENT
        msg.set_metadata("performative", INFORM_PERFORMATIVE)
        #msg.body = None                                            #CHANGE - FOR DEQUEUE IN QUEUESTATIONAGENT
        msg.body = json.dumps(content)
        await self.send(msg)

    async def run(self):
        raise NotImplementedError
