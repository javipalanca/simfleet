import asyncio
import json
import sys

from loguru import logger
from asyncio import CancelledError
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template

from simfleet.utils.helpers import (
    #random_position,
    distance_in_meters,
    kmh_to_ms,
    PathRequestException,
    AlreadyInDestination,
)

from simfleet.utils.utils_old import (
    TRANSPORT_WAITING,
    TRANSPORT_MOVING_TO_CUSTOMER,
    TRANSPORT_IN_CUSTOMER_PLACE,
    TRANSPORT_MOVING_TO_DESTINATION,
    TRANSPORT_IN_STATION_PLACE,
    TRANSPORT_CHARGING,
    CUSTOMER_IN_DEST,
    CUSTOMER_LOCATION,
    TRANSPORT_MOVING_TO_STATION,
    chunk_path,
    request_path,
    StrategyBehaviour,
    TRANSPORT_NEEDS_CHARGING,
)

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    TRAVEL_PROTOCOL,
    PROPOSE_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    REGISTER_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
    QUERY_PROTOCOL,
)

from simfleet.common.agents.transport import TransportAgent

MIN_AUTONOMY = 2

class BusAgent(TransportAgent):
    def __init__(self, agentjid, password, **kwargs):
        super().__init__(agentjid, password)

        #self.current_customer_orig = None                      # MOD-STRATEGY-02 - comments
        #self.set("assigned_customer", {})            # MOD-STRATEGY-01-A

        #self.fleetmanager_id = kwargs.get('fleet', None)        # vehicle.py

        # Bus line attributes
        self.stop_list = []
        self.line = None
        self.line_type = None
        #self.current_customers = {}
        self.stop_dic = None
        self.current_stop = None
        self.type_service = "stops"
        self.capacity = None
        self.current_capacity = None
        self.rounds = 0
        self.occupations = [0]
        # For movement
        self.set("origin_stop", None)
        self.set("destination_stop", None)

        # Transport in stop event
        self.set("arrived_to_stop", None)  # new
        self.transport_arrived_to_stop_event = asyncio.Event(loop=self.loop)

        #HARCODEADO ATRIBUTOS CHARGING
        self.current_autonomy_km = 0
        self.max_autonomy_km = 0

        def transport_arrived_to_stop_callback(old, new):
            if not self.transport_arrived_to_stop_event.is_set() and new is True:
                self.transport_arrived_to_stop_event.set()

        self.transport_arrived_to_stop_callback = transport_arrived_to_stop_callback

    # Bus line
    def set_line(self, line):
        logger.info("Setting line {} for transport {}".format(line, self.name))
        self.line = line

    def set_line_type(self, line_type):
        logger.info("Setting line type {} for transport {}".format(line_type, self.name))
        self.line_type = line_type

    def set_stop_list(self, stop_list):
        self.stop_list = stop_list

    def set_capacity(self, capacity):
        self.capacity = capacity
        self.current_capacity = capacity

    #def get_avg_occupation(self):
    #    return numpy.mean(self.occupations)

    # async def send(self, msg):
    #     if not msg.sender:
    #         msg.sender = str(self.jid)
    #     aioxmpp_msg = msg.prepare()
    #     await self.client.send(aioxmpp_msg)
    #     msg.sent = True
    #     self.traces.append(msg, category=str(self))

    #def is_customer_in_transport(self):
    #    return self.get("customer_in_transport") is not None

    #def is_free(self):
    #    return self.get("current_customer") is None

    def setup_current_stop(self):
        for jid in self.stop_dic.keys():
            stop_info = self.stop_dic.get(jid)
            if stop_info.get("position") == self.get("current_pos"):
                self.current_stop = stop_info

    async def arrived_to_stop(self):
        # Setup the stop the transport just arrived to as the current stop
        self.setup_current_stop()
        logger.info(
            "Transport {} arrived to stop {}".format(
                self.agent_id, self.current_stop.get("jid")
            )
        )
        self.set("arrived_to_stop", True)  # new
        # self.status = "TRANSPORT_IN_DEST"

    async def setup(self):
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = RegistrationBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning(
                    "Transport {} could not create RegisterBehaviour. Retrying...".format(
                        self.agent_id
                    )
                )
                self.add_behaviour(register_behaviour, template)
            self.ready = True
        except Exception as e:
            logger.error(
                "EXCEPTION creating RegisterBehaviour in Transport {}: {}".format(
                    self.agent_id, e
                )
            )

    def run_strategy(self):
        """
        Sets the strategy for the transport agent.

        Args: strategy_class (``TransportStrategyBehaviour``): The class to be used. Must inherit from
        ``TransportStrategyBehaviour``
        """
        if not self.running_strategy:
            template1 = Template()
            template1.set_metadata("protocol", REQUEST_PROTOCOL)
            # template2 = Template()
            # template2.set_metadata("protocol", QUERY_PROTOCOL)
            # self.add_behaviour(self.strategy(), template1 | template2)
            self.add_behaviour(self.strategy(), template1)
            self.running_strategy = True


    async def set_position(self, coords=None):
        """
        Sets the position of the transport. If no position is provided it is located in a random position.

        Args:
            coords (list): a list coordinates (longitude and latitude)
        """

        await super().set_position(coords)
        self.set("current_pos", coords)

        if self.is_in_destination():
            logger.info(
                "Transport {} has arrived to destination. Status: {}".format(
                    self.agent_id, self.status
                )
            )

            if self.status != TRANSPORT_MOVING_TO_STATION:
                #await self.arrived_to_station()
            #else:
                await self.arrived_to_stop()

    def setup_current_stop(self):
        for jid in self.stop_dic.keys():
            stop_info = self.stop_dic.get(jid)
            if stop_info.get("position") == self.get("current_pos"):
                self.current_stop = stop_info

    async def arrived_to_stop(self):
        # Setup the stop the transport just arrived to as the current stop
        self.setup_current_stop()
        logger.info(
            "Transport {} arrived to stop {}".format(
                self.agent_id, self.current_stop.get("jid")
            )
        )
        self.set("arrived_to_stop", True)  # new        #ANALIZAR
        # self.status = "TRANSPORT_IN_DEST"

    # Copia - Bus line
    # def to_json(self):
    #     """
    #     Serializes the main information of a transport agent to a JSON format.
    #     It includes the id of the agent, its current position, the destination coordinates of the agent,
    #     the current status, the speed of the transport (in km/h), the path it is following (if any), the customer that it
    #     has assigned (if any), the number of assignments if has done and the distance that the transport has traveled.
    #
    #     Returns:
    #         dict: a JSON doc with the main information of the transport.
    #
    #         Example::
    #
    #             {
    #                 "id": "cphillips",
    #                 "position": [ 39.461327, -0.361839 ],
    #                 "dest": [ 39.460599, -0.335041 ],
    #                 "status": 24,
    #                 "speed": 1000,
    #                 "path": [[0,0], [0,1], [1,0], [1,1], ...],
    #                 "customer": "ghiggins@127.0.0.1",
    #                 "assignments": 2,
    #                 "distance": 3481.34
    #             }
    #     """
    #     return {
    #         "id": self.agent_id,
    #         "position": [
    #             float("{0:.6f}".format(coord)) for coord in self.get("current_pos")
    #         ],
    #         "dest": [float("{0:.6f}".format(coord)) for coord in self.dest]
    #         if self.dest
    #         else None,
    #         "status": self.status,
    #         "speed": float("{0:.2f}".format(self.animation_speed))
    #         if self.animation_speed
    #         else None,
    #         "path": self.get("path"),
    #         "customer": self.get("current_customer").split("@")[0]
    #         if self.get("current_customer")
    #         else None,
    #         "assignments": self.num_assignments,
    #         "distance": "{0:.2f}".format(sum(self.distances)),
    #         #"autonomy": self.current_autonomy_km,
    #         #"max_autonomy": self.max_autonomy_km,
    #         "service": self.fleet_type,
    #         "fleet": self.fleetmanager_id.split("@")[0],
    #         "icon": self.icon,
    #     }


class RegistrationBehaviour(CyclicBehaviour):
    async def on_start(self):
        logger.debug("Strategy {} started in transport".format(type(self).__name__))

    async def send_registration(self):
        """
        Send a ``spade.message.Message`` with a proposal to manager to register.
        """
        logger.debug(
            "Transport {} sent proposal to register to manager {}".format(
                self.agent.name, self.agent.fleetmanager_id
            )
        )
        content = {
            "name": self.agent.name,
            "jid": str(self.agent.jid),
            "fleet_type": self.agent.fleet_type,
        }
        msg = Message()
        msg.to = str(self.agent.fleetmanager_id)
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
                    content = json.loads(msg.body)
                    self.agent.set_registration(True, content)
                    logger.info(
                        "[{}] Registration in the fleet manager accepted: {}.".format(
                            self.agent.name, self.agent.fleetmanager_id
                        )
                    )
                    self.kill(exit_code="Fleet Registration Accepted")
                elif performative == REFUSE_PERFORMATIVE:
                    logger.warning(
                        "Registration in the fleet manager was rejected (check fleet type)."
                    )
                    self.kill(exit_code="Fleet Registration Rejected")
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error(
                "EXCEPTION in RegisterBehaviour of Transport {}: {}".format(
                    self.agent.name, e
                )
            )

class BusStrategyBehaviour(StrategyBehaviour):
    """
    Class from which to inherit to create a transport strategy.
    You must overload the ```run`` coroutine

    Helper functions:
        * ``pick_up_customer``
        * ``send_proposal``
        * ``cancel_proposal``
    """

    async def on_start(self):
        logger.debug(
            "Strategy {} started in transport {}".format(
                type(self).__name__, self.agent.name
            )
        )
        # self.agent.total_waiting_time = 0.0

    # Bus line functions
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
            "Transport {} asked for stops to directory {} for type {}.".format(
                self.agent.name, self.agent.directory_id, self.agent.type_service
            )
        )

    def get_subsequent_stop(self):
        try:
            index_current = self.agent.stop_list.index(self.agent.get("current_pos"))
        except ValueError:
            index_current = None
        if index_current is None:
            logger.critical("Transport {} current pos ({}) is not in its stop_list {}".format(self.agent.name,
                                                                                              self.agent.get(
                                                                                                  "current_pos"),
                                                                                              self.agent.stop_list))
            sys.exit()
        next_destination = None
        if index_current + 1 < len(self.agent.stop_list):
            next_destination = self.agent.stop_list[index_current + 1]
        return next_destination

    async def move_to_next_stop(self, next_destination):
        logger.info("Transport {} in route to {}".format(self.agent.name, next_destination))
        dest = next_destination
        # set current destination as next destination
        self.agent.set("next_pos", dest)            #ANALIZAR
        # Invoke move_to
        try:
            await self.agent.move_to(dest)
        except AlreadyInDestination:
            self.agent.dest = dest
            await self.agent.arrived_to_stop()
        except PathRequestException as e:
            logger.error(
                "Raising PathRequestException in pick_up_customer for {}".format(
                    self.agent.name
                )
            )
            raise e

    async def drop_customers(self):
        # get current position ( = current destination)
        current_position = self.agent.get("current_pos")
        # Inform passengers (tuples with agent name, destination stop)
        inform_to = self.get_customers_from_stop(current_position)
        while len(inform_to) > 0:
            customer = inform_to[0]
            logger.info("Transport {} informing customer {} their destination stop has been reached".format(
                self.agent.name, customer))
            inform_to = inform_to[1:]
            msg = Message()
            msg.to = str(customer)
            msg.set_metadata("protocol", REQUEST_PROTOCOL)
            msg.set_metadata("performative", INFORM_PERFORMATIVE)
            msg.status = CUSTOMER_IN_DEST
            await self.send(msg)
            # Update capacity
            self.agent.current_capacity += 1
            # Delete customer from current customers
            #del self.agent.current_customers[customer]         #ADAPTAR CURRENT CUSTOMERS
            del self.agent.get("current_customer")[customer]

    def get_customers_from_stop(self, current_position):
        customer_list = []
        #for customer_id in self.agent.current_customers.keys():    #ADAPTAR CURRENT CUSTOMERS
        for customer_id in self.agent.get("current_customer").keys():
            #customer_dest = self.agent.current_customers.get(customer_id).get("dest")      #ADAPTAR CURRENT CUSTOMERS
            customer_dest = self.agent.get("current_customer").get(customer_id).get("dest")
            if customer_dest == current_position:
                customer_list.append(customer_id)
        return customer_list

    async def begin_boarding(self, content):
        logger.info("Transport {} informing stop {} that boarding may begin".format(self.agent.name,
                                                                                    self.agent.current_stop.get(
                                                                                        "jid")))
        if content is None:
            content = {}
        msg = Message()
        msg.to = str(self.agent.current_stop.get("jid"))
        msg.set_metadata("protocol", REQUEST_PROTOCOL)
        msg.set_metadata("performative", INFORM_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

    async def accept_customer(self, customer_id, content):
        """
        Send a ``spade.message.Message`` with accepting the boarding of a customer.
        If the content is empty the proposal is sent without content.

        Args:
            customer_id (str): the id of the customer
            content (dict, optional): the optional content of the message
        """
        customer_origin = content.get("origin")
        customer_dest = content.get("dest")
        logger.info(
            "Transport {} accepted customer {} with origin {} and dest {}".format(self.agent.name, customer_id,
                                                                                  customer_origin, customer_dest)
        )
        # Add customer to the current customers dict
        #self.agent.current_customers[str(customer_id)] = {"origin": customer_origin, "dest": customer_dest}
        self.agent.get("current_customer")[str(customer_id)] = {"origin": customer_origin, "dest": customer_dest}
        self.agent.num_assignments += 1

        # Send message accepting the boarding
        reply = Message()
        reply.to = str(customer_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def reject_customer(self, customer_id, content):
        """
        Send a ``spade.message.Message`` with accepting the boarding of a customer.
        If the content is empty the proposal is sent without content.

        Args:
            customer_id (str): the id of the customer
            content (dict, optional): the optional content of the message
        """
        logger.info("Transport {} rejected customer {}".format(self.agent.name, customer_id))

        # Send message rejecting the boarding
        reply = Message()
        reply.to = str(customer_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", REFUSE_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)
