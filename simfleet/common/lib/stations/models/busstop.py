import json

from loguru import logger
from asyncio import CancelledError
from spade.message import Message
from spade.template import Template
from spade.behaviour import CyclicBehaviour


from simfleet.communications.protocol import (
        ACCEPT_PERFORMATIVE,
        INFORM_PERFORMATIVE,
        REGISTER_PROTOCOL,
        REQUEST_PERFORMATIVE,
        REQUEST_PROTOCOL
)

from simfleet.common.agents.station.queuestationagent import QueueStationAgent
from simfleet.utils.status import TRANSPORT_IN_CUSTOMER_PLACE


class BusStopAgent(QueueStationAgent):
    """
        Represents a bus stop agent that manages customer registrations,
        informs customers about bus arrivals, and handles the bus stop status.

        Methods:
            setup(): Initializes the bus stop agent and sets up its behavior templates.
            set_name(name): Sets the name of the bus stop.
            set_status(state): Sets the status of the bus stop.
            set_type(station_type): Sets the type of the bus stop.
            set_lines(lines): Sets the bus lines that serve the stop.
            to_json(): Returns the bus stop information in JSON format.
            run_strategy(): Sets the strategy behavior for the stop.
    """
    def __init__(self, agentjid, password, **kwargs):
        super().__init__(agentjid, password)

        # Bus stop attributes
        self.stop_name = None
        self.lines = None

        # Atribut afegit perque funcione
        self.type = None

    async def setup(self):
        """
            Sets up the bus stop agent by defining its type and behaviors.
        """
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

    #Cambiar en mas lugares
    def set_name(self, name):
        """
            Sets the name of the bus stop.
        """
        self.stop_name = name

    def set_status(self, state=None):
        """
        Sets the status of the bus stop.
        """
        self.status = state

    def set_type(self, station_type):
        """
        Sets the type of the bus stop.
        """
        self.type = station_type

    def set_lines(self, lines):
        """
            Sets the bus lines that the stop serves.
        """
        self.lines = lines

    def to_json(self):
        return {
            "id": self.agent_id,
            "name": self.stop_name,
            "position": self.get("current_pos"),
            "lines": self.lines,
            "icon": self.icon,
        }

    def run_strategy(self):
        """
        Sets the strategy for the stop agent.
        """
        if not self.running_strategy:
            self.running_strategy = True


class RegistrationBehaviour(CyclicBehaviour):
    """
        Handles the registration behavior of the bus stop, allowing it to register with the directory agent.

        Methods:
            on_start(): Initializes the behavior and sets up the logger.
            send_registration(): Sends a registration message to the directory.
            run(): Manages the registration logic and response handling.
    """
    async def on_start(self):
        logger.debug("Strategy {} started in directory".format(type(self).__name__))

    def set_registration(self, decision):
        """
            Sets the registration status of the agent.

            Args:
                decision (bool): Registration decision.
        """
        self.agent.registration = decision

    async def send_registration(self):
        """
        Sends a registration message to the directory agent with the bus stop's information.
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
    Strategy behavior for managing the bus stop operations, including handling customer notifications.

    Methods:
        on_start(): Initializes the behavior and sets up the logger.
        dequeue_customers(): Manages the dequeueing of customers based on their destinations.
        inform_customers(): Informs customers that their transport has arrived.
        run(): Main loop handling incoming messages and customer notifications.
    """

    async def on_start(self):
        logger.debug(
            "Strategy {} started in transport {}".format(
                type(self).__name__, self.agent.name
            )
        )

    async def dequeue_customers(self, sender, line, list_of_stops=None):        #ADAPTAR A QUEUESTATIONAGENT
        """
        Sends a message to all customers whose destination is in the list of stops.

        Args:
            sender (str): ID of the sender (bus).
            line (str): The bus line.
            list_of_stops (list, optional): Coordinates for each stop in the transport's route.
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
            self.agent.queuebehaviour.dequeue_agent_to_waiting_list(line, sender)


    async def inform_customers(self, inform_to, sender):
        """
            Informs the specified customers that their transport has arrived.

            Args:
                inform_to (list): List of customers to be informed.
                sender (str): The ID of the bus notifying the customers.
        """
        for customer in inform_to:
            data = {"status": TRANSPORT_IN_CUSTOMER_PLACE, "transport": sender}
            msg = Message()
            msg.to = customer
            msg.set_metadata("protocol", REQUEST_PROTOCOL)
            msg.set_metadata("performative", INFORM_PERFORMATIVE)
            msg.body = json.dumps(data)
            await self.send(msg)


    async def run(self):
        """
            Main loop that handles incoming messages and manages customer notifications.
        """
        msg = await self.receive(timeout=30)
        logger.debug("Bus stop {} received message: {}".format(self.agent.jid, msg))
        if msg:
            sender = msg.sender
            performative = msg.get_metadata("performative")
            content = json.loads(msg.body)

            if performative == INFORM_PERFORMATIVE:
                line = content["line"]

                if "list_of_stops" in content:
                    list_of_stops = content["list_of_stops"]
                else:
                    list_of_stops = None

                logger.debug("Stop {} received message from transport {}, informing customers...".format(
                    self.agent.name, sender))

                await self.dequeue_customers(sender, line, list_of_stops)
