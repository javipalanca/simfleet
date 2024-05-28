import json
import time

from loguru import logger
from collections import deque
from spade.message import Message
from spade.template import Template
from spade.behaviour import CyclicBehaviour

from simfleet.common.geolocatedagent import GeoLocatedAgent

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    QUERY_PROTOCOL,
    COORDINATION_PROTOCOL,
)

class QueueStationAgent(GeoLocatedAgent):
    def __init__(self, agentjid, password):
        GeoLocatedAgent.__init__(self, agentjid, password)

        self.queuebehaviour = self.QueueBehaviour()


        self.services_list = {}

        #statics
        self.transports_in_queue_time = None
        self.empty_queue_time = None
        self.total_busy_time = None  # total time with some transport waiting in queue

    # Service Management
    def add_service(self, service_name, slots, one_shot_behaviour):
        if service_name not in self.services_list:
            self.services_list[service_name] = {
                'slots': slots,
                'slots_in_use': 0,
                'one_shot_behaviour': one_shot_behaviour
            }
            #New queue- Queue for service
            self.queuebehaviour.waiting_lists[service_name] = deque()

            logger.debug(
                "The service {} has been inserted in the agent {}. ".format(
                    service_name, self.name
                )
            )
        else:
            logger.warning(
                "The service {} exists in the agent {}.".format(
                    service_name, self.name
                )
            )

    def remove_service(self, service_name):
        if service_name in self.services_list:
            del self.services_list[service_name]

    def show_services(self):
        return tuple(self.services_list.keys())


    async def send_inform_service(self, agent_id, content):
        """
        Send a message to the transport agent that the vehicle load has been completed
        """
        reply = Message()
        reply.to = str(self.agent_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        content = {"services": self.show_services()}
        reply.body = json.dumps(content)
        await self.send(reply)

    async def request_agent_position(self, agent_id):

        reply = Message()
        reply.to = str(agent_id)
        reply.set_metadata("protocol", COORDINATION_PROTOCOL)
        reply.set_metadata("performative", REQUEST_PERFORMATIVE)
        # reply.body = json.dumps(content)
        await self.send(reply)


    # Waiting list for agents
    class QueueBehaviour(CyclicBehaviour):

        def __init__(self):
            self.waiting_lists = {}
            super().__init__()

        def total_queue_size(self, service_name):
            return len(self.waiting_lists[service_name])

        #Original
        #def queue_agent_to_waiting_list(self, service_name, id_agent):      # Meter un args dentro de la queue - diccionario ---- APUNTES
        #    self.waiting_lists[service_name].append(id_agent)

        def queue_agent_to_waiting_list(self, service_name, id_agent, *args):      # Meter un args dentro de la queue - diccionario ---- APUNTES

            self.waiting_lists[service_name].append((id_agent, args))

        def dequeue_first_agent_to_waiting_list(self, service_name):  # Desencolar al primer agente
            if len(self.waiting_lists[service_name]) == 0:
                return None
            return self.waiting_lists[service_name].popleft()

        def dequeue_agent_to_waiting_list(self, service_name, id):  # Desencolar un agente de la cola por id - vrs 1
            self.waiting_lists[service_name].remove(id)

        def find_queue_position(self, service_name, agent_id):
            try:
                position = self.waiting_lists[service_name].index(agent_id)
                return position
            except ValueError:
                return None

        # MSG

        async def accept_request_agent(self, agent_id, content=None):
            """
            Sends a ``spade.message.Message`` to a transport to accept a travel proposal for charge.
            It uses the REQUEST_PROTOCOL and the ACCEPT_PERFORMATIVE.

            Args:
                transport_id (str): The Agent JID of the transport
            """
            if content is None:
                content = {}
            reply = Message()
            reply.to = str(agent_id)
            reply.set_metadata("protocol", REQUEST_PROTOCOL)
            reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
            #content = {"station_id": str(self.agent.jid), "dest": self.agent.current_pos}
            reply.body = json.dumps(content)
            await self.send(reply)
            logger.debug(
                "Agent {} accepted entry proposal".format(
                    self.agent.name
                )
            )

        async def refuse_request_agent(self, agent_id):
            """
            Sends an ``spade.message.Message`` to a transport to refuse a travel proposal for charge.
            It uses the REQUEST_PROTOCOL and the REFUSE_PERFORMATIVE.

            Args:
                transport_id (str): The Agent JID of the transport
            """
            reply = Message()
            reply.to = str(agent_id)
            reply.set_metadata("protocol", REQUEST_PROTOCOL)
            reply.set_metadata("performative", REFUSE_PERFORMATIVE)
            content = {}
            reply.body = json.dumps(content)

            await self.send(reply)
            logger.debug(
                "Agent {} refused queuebehaviour proposal from agent {}".format(
                    self.agent.name, agent_id
                )
            )


        async def on_start(self):
            logger.debug("Strategy {} started in station".format(type(self).__name__))

        async def run(self):
            msg = await self.receive(timeout=5)

            if msg:
                performative = msg.get_metadata("performative")
                agent_id = msg.sender
                service_name = json.loads(msg.body)["service_name"]      #chequear
                args = json.loads(msg.body)["args"]
                #agent_position = json.loads(msg.content)["agent_position"]  #Preguntar al SimulatorAGent

                if performative == CANCEL_PERFORMATIVE:

                    logger.warning(
                        "Agent {} received a REFUSE from agent {}.".format(
                            self.agent.name, agent_id
                        )
                    )
                    self.dequeue_agent_to_waiting_list(service_name, str(agent_id))
                    #self.cancel_request_agent(str(agent_id))

                    logger.debug(
                        "Agent {} has been removed from the waiting_list.".format(
                            self.agent.name, agent_id
                        )
                    )
                elif (
                        performative == REQUEST_PERFORMATIVE
                ):  # comes from send_confirmation_travel

                    # Send msg to SimulatorAgent for agent_position
                    self.agent.request_agent_position("simulator@localhost")    #Cambiarlo - JID simulador - DEBATIR

                    # Request to SimulatorAgent for agent_position
                    msg = await self.receive(timeout=5)         #Duda PREGUNTAR

                    if msg:
                        performative = msg.get_metadata("performative")
                        agent_id_simulator = msg.sender
                        agent_position = json.loads(msg.body)["agent_position"]

                        if service_name not in self.waiting_lists or not self.agent.near_agent(coords_1=self.agent.get_position(), coords_2=agent_position):    #New
                            await self.refuse_request_agent(agent_id)
                            logger.warning(
                                "Station {} has REFUSED request from agent {} for service {}".format(
                                    self.agent.name,
                                    agent_id,
                                    service_name
                                )
                            )
                        else:

                            if self.total_queue_size(service_name) == 0:
                                self.agent.transports_in_queue_time = time.time()

                            self.queue_agent_to_waiting_list(service_name, str(agent_id), args)     #Duda ARGS

                            content = {"station_id": str(self.agent.jid)}
                            await self.accept_request_agent(agent_id, content)

                            logger.info(
                                "Station {} has put {} in the waiting_list".format(
                                    self.agent.name,
                                    agent_id,
                                )
                            )
                    else:
                        logger.warning(
                            "Station {} has not received agent position of {} from the Simulator".format(
                                self.agent.name,
                                agent_id,
                            )
                        )

                # time statistics update
                if self.total_queue_size(service_name):
                    self.agent.empty_queue_time = time.time()
                    self.agent.total_busy_time += (
                        self.agent.empty_queue_time - self.agent.transports_in_queue_time
                    )



    async def setup(self):
        logger.info("Queue agent {} running".format(self.name))

        template1 = Template()
        template1.set_metadata("protocol", REQUEST_PROTOCOL)
        template1.set_metadata("performative", REQUEST_PERFORMATIVE) #template slo permite una sola performativa y protocolo

        template2 = Template()
        template2.set_metadata("protocol", REQUEST_PROTOCOL)
        template2.set_metadata("performative", CANCEL_PERFORMATIVE)

        self.add_behaviour(self.queuebehaviour, template1 | template2)
