import json
import time

from loguru import logger
from collections import deque
from spade.message import Message
from spade.template import Template
from spade.behaviour import CyclicBehaviour, OneShotBehaviour

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
        self.waiting_lists = {}

        # ORIGINAL NEAR
        #self.near_list = {}
        self.simulatorjid = None

        #statics
        self.transports_in_queue_time = 0
        self.empty_queue_time = 0
        self.total_busy_time = 0  # total time with some transport waiting in queue
        self.queue_length = 0
        self.max_queue_length = 0

    def set_simulatorjid(self, jid):
        self.simulatorjid = jid

    def get_simulatorjid(self):
        return self.simulatorjid

    async def setup(self):
        logger.info("Queue agent {} running".format(self.name))

        template1 = Template()
        template1.set_metadata("protocol", REQUEST_PROTOCOL)
        template1.set_metadata("performative", REQUEST_PERFORMATIVE) #template slo permite una sola performativa y protocolo

        template2 = Template()
        template2.set_metadata("protocol", REQUEST_PROTOCOL)
        template2.set_metadata("performative", CANCEL_PERFORMATIVE)

        #template3 = Template()
        #template3.set_metadata("protocol", COORDINATION_PROTOCOL)
        #template3.set_metadata("performative", INFORM_PERFORMATIVE)

        #self.add_behaviour(self.queuebehaviour, template1 | template2 | template3)
        self.add_behaviour(self.queuebehaviour, template1 | template2)

    # Service Management
    def add_service(self, service_name, slots, one_shot_behaviour, **arguments):
        if service_name not in self.services_list:
            self.services_list[service_name] = {
                'slots': slots,
                'slots_in_use': 0,
                'one_shot_behaviour': one_shot_behaviour,
                'args': arguments,
            }
            #New queue- Queue for service
            #self.queuebehaviour.waiting_lists[service_name] = deque()
            self.waiting_lists[service_name] = deque()

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

    # Bus line
    def add_queue(self, line, **arguments):      #add_queue - POSIBLE CAMBIO DE NOMBRE
        if line not in self.services_list:
            self.services_list[line] = {
                'args': arguments,
            }
            #New queue- Queue for service
            #self.queuebehaviour.waiting_lists[service_name] = deque()
            self.waiting_lists[line] = deque()                      #COLA POR LINEA - Adaptar crando una nueva definicion add_queue - line_name, args

            logger.debug(
                "The line {} has been inserted in the agent {}. ".format(
                    line, self.name
                )
            )
        else:
            logger.warning(
                "The line {} exists in the agent {}.".format(
                    line, self.name
                )
            )

    def remove_service(self, service_name):
        if service_name in self.services_list:
            del self.services_list[service_name]

    def show_services(self):
        return tuple(self.services_list.keys())

    def show_service_arguments(self, service_name):
        return self.services_list[service_name]["args"]

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

    async def request_agent_position(self, agent_id, content):

        reply = Message()
        reply.to = str(agent_id)
        reply.set_metadata("protocol", COORDINATION_PROTOCOL)
        reply.set_metadata("performative", REQUEST_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)


    # Waiting list for agents
    class QueueBehaviour(CyclicBehaviour):

        def __init__(self):
            #self.agent.waiting_lists = {}
            super().__init__()

        def total_queue_size(self, service_name):
            return len(self.agent.waiting_lists[service_name])

        #Original
        #def queue_agent_to_waiting_list(self, service_name, id_agent):      # Meter un args dentro de la queue - diccionario ---- APUNTES
        #    self.agent.waiting_lists[service_name].append(id_agent)

        #def queue_agent_to_waiting_list(self, service_name, id_agent, *args):      # Meter un args dentro de la queue - diccionario ---- APUNTES
        def queue_agent_to_waiting_list(self, service_name, id_agent, **kwargs):  # Meter un args dentro de la queue - diccionario ---- APUNTES

            self.agent.waiting_lists[service_name].append((id_agent, kwargs))

        def dequeue_first_agent_to_waiting_list(self, service_name):  # Desencolar al primer agente
            if len(self.agent.waiting_lists[service_name]) == 0:
                return None
            return self.agent.waiting_lists[service_name].popleft()

        def dequeue_agent_to_waiting_list(self, service_name, id_agent):  # Desencolar un agente de la cola por id - vrs 1
            # self.agent.waiting_lists[service_name].remove(id_agent)    #FALLO
            if service_name in self.agent.waiting_lists:
                for agent in self.agent.waiting_lists[service_name]:
                    # DEPURACION
                    logger.warning(
                        "DEPURACION QUEUESTATIONAGENT - id_agent in queue: {},  sender: {}".format(
                            agent[0],
                            id_agent
                        )
                    )
                    if agent[0] == id_agent:
                        self.agent.waiting_lists[service_name].remove(agent)
                        break

        def find_queue_position(self, service_name, agent_id):
            try:
                position = self.agent.waiting_lists[service_name].index(agent_id)
                return position
            except ValueError:
                return None

        def get_queue(self, service_name):
            if service_name in self.agent.waiting_lists:
                return self.agent.waiting_lists[service_name]

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
                protocol = msg.get_metadata("protocol")
                agent_id = msg.sender
                content = json.loads(msg.body)

                #if content["service_name"]:
                #    service_name = content["service_name"]

                #if content["args"]:
                #    arguments = content["args"]

                #DEPURACION 4
                logger.warning(
                    "DEPURACION - Station {}, msg: {}".format(
                        self.agent.name,
                        msg,
                    )
                )

                logger.warning(
                    "AGENT ID {}.".format(
                        agent_id
                    )
                )

                #if content["agent_position"]:
                #    agent_position = content["agent_position"]

                #if content["user_agent_id"]:
                #    user_agent_id = content["user_agent_id"]


                if protocol == REQUEST_PROTOCOL and performative == CANCEL_PERFORMATIVE:

                    if "service_name" in content:
                        service_name = content["service_name"]

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
                        protocol == REQUEST_PROTOCOL and performative == REQUEST_PERFORMATIVE
                ):  # comes from send_confirmation_travel

                    if "service_name" in content:
                        service_name = content["service_name"]

                    # NEW - Change to new name - line and service_name - BUS
                    # Bus line
                    if "line" in content:
                        service_name = content["line"]

                    # NEW
                    if "object_type" in content:
                        object_type = content["object_type"]

                    if "args" in content:
                        arguments = content["args"]

                    # ORIGINAL NEAR
                    # if str(agent_id) not in self.agent.near_list:
                    #     self.agent.near_list[str(agent_id)] = {
                    #         'service_name': service_name,
                    #         'arguments': arguments
                    #     }
                    #
                    #     logger.warning(
                    #         "DICCIONARIO NEAR: {} exists in the near_list - agent_id: {}.".format(
                    #             self.agent.near_list,
                    #             agent_id
                    #         )
                    #     )
                    #
                    # else:
                    #     logger.warning(
                    #         "The agent {} exists in the near_list.".format(
                    #             agent_id
                    #         )
                    #     )

                    #Comprobamos la ubicación
                    #content = {"user_agent_id": agent_id}

                    #ORIGINAL NEAR
                    #Bus Line
                    #content = {"user_agent_id": agent_id, "object_type": object_type}
                    #await self.agent.request_agent_position("simulator_none@localhost", content)    #Cambiarlo - JID simulador - DEBATIR

                    # Request to SimulatorAgent for agent_position
                    #msg = await self.receive(timeout=5)         #Duda PREGUNTAR

                    #NEW NEAR
                    template3 = Template()
                    template3.set_metadata("protocol", COORDINATION_PROTOCOL)
                    template3.set_metadata("performative", INFORM_PERFORMATIVE)

                    instance = CheckNearBehaviour(self.agent.get_simulatorjid(), agent_id, service_name, object_type, arguments)
                    self.agent.add_behaviour(instance, template3)

                    await instance.join()       # Wait for the behaviour to complete

                    service_name = instance.service_name
                    agent_position = instance.agent_position
                    user_agent_id = instance.user_agent_id
                    arguments = instance.arguments

                # ORIGINAL - NEAR
                # elif (
                #         protocol == COORDINATION_PROTOCOL and performative == INFORM_PERFORMATIVE
                # ):  # comes from send_confirmation_travel
                #
                #     if "agent_position" in content:
                #         agent_position = content["agent_position"]
                #
                #     if "user_agent_id" in content:
                #         user_agent_id = content["user_agent_id"]
                #
                #     logger.warning(
                #         "NEAR depuracion - agent_position: {}, user_agent_id {}".format(
                #             agent_position,
                #             user_agent_id
                #         )
                #     )
                #
                #     logger.warning(
                #         "NEAR_LIST: {} ".format(
                #             self.agent.near_list[user_agent_id]
                #         )
                #     )
                #
                #     service_name = self.agent.near_list[user_agent_id]["service_name"]
                #     arguments = self.agent.near_list[user_agent_id]["arguments"]
                #     del self.agent.near_list[user_agent_id]
                #
                #     logger.debug(
                #         "Station {} has received msg from agent {} for near check".format(
                #             self.agent.name,
                #             agent_id
                #         )
                #     )


                    if service_name not in self.agent.waiting_lists or not self.agent.near_agent(
                            coords_1=self.agent.get_position(), coords_2=agent_position):    #New

                        await self.refuse_request_agent(user_agent_id)
                        logger.warning(
                            "Station {} has REFUSED request from agent {} for service {}".format(
                                self.agent.name,
                                user_agent_id,
                                service_name
                            )
                        )
                    else:

                        if self.total_queue_size(service_name) == 0:
                            self.agent.transports_in_queue_time = time.time()

                        # Encolamos
                        self.queue_agent_to_waiting_list(service_name, str(user_agent_id), **arguments)
                        #self.queue_agent_to_waiting_list(service_name, str(agent_id), *arguments)     #Duda ARGS

                        if self.total_queue_size(service_name) > self.agent.max_queue_length:
                            self.agent.max_queue_length = self.total_queue_size(service_name)

                        content = {"station_id": str(self.agent.jid)}
                        await self.accept_request_agent(user_agent_id, content)

                        logger.info(
                            "Station {} has put {} in the waiting_list".format(
                                self.agent.name,
                                user_agent_id,
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

            # COPIA

            # if msg:
            #     performative = msg.get_metadata("performative")
            #     agent_id = msg.sender
            #     service_name = json.loads(msg.body)["service_name"]      #chequear
            #     arguments = json.loads(msg.body)["args"]
            #     #agent_position = json.loads(msg.content)["agent_position"]  #Preguntar al SimulatorAGent
            #
            #     if performative == CANCEL_PERFORMATIVE:
            #
            #         logger.warning(
            #             "Agent {} received a REFUSE from agent {}.".format(
            #                 self.agent.name, agent_id
            #             )
            #         )
            #         self.dequeue_agent_to_waiting_list(service_name, str(agent_id))
            #         #self.cancel_request_agent(str(agent_id))
            #
            #         logger.debug(
            #             "Agent {} has been removed from the waiting_list.".format(
            #                 self.agent.name, agent_id
            #             )
            #         )
            #     elif (
            #             performative == REQUEST_PERFORMATIVE
            #     ):  # comes from send_confirmation_travel
            #
            #         content = {"user_agent_id": agent_id}
            #         # Send msg to SimulatorAgent for agent_position
            #         await self.agent.request_agent_position("simulator_none@localhost", content)    #Cambiarlo - JID simulador - DEBATIR
            #
            #         # Request to SimulatorAgent for agent_position
            #         msg = await self.receive(timeout=5)         #Duda PREGUNTAR
            #
            #         logger.warning(
            #             "MENSAJE DEL SIMULATOR: {} ".format(
            #                 msg
            #             )
            #         )
            #
            #         if msg:
            #             #CONTINUAR AQUI
            #             performative = msg.get_metadata("performative")
            #             agent_id_simulator = msg.sender
            #             content = json.loads(msg.body)
            #             agent_position = json.loads(msg.body)["agent_position"]
            #
            #             if agent_id_simulator == "simulator_none@localhost":
            #                 logger.debug(
            #                     "Transport {} received a message with ACCEPT_PERFORMATIVE from {}".format(
            #                         self.agent.name, content["station_id"]
            #                     )
            #                 )
            #
            #             if service_name not in self.agent.waiting_lists or not self.agent.near_agent(coords_1=self.agent.get_position(), coords_2=agent_position):    #New
            #                 self.refuse_request_agent(agent_id)
            #                 logger.warning(
            #                     "Station {} has REFUSED request from agent {} for service {}".format(
            #                         self.agent.name,
            #                         agent_id,
            #                         service_name
            #                     )
            #                 )
            #             else:
            #
            #                 if self.total_queue_size(service_name) == 0:
            #                     self.agent.transports_in_queue_time = time.time()
            #
            #                 self.queue_agent_to_waiting_list(service_name, str(agent_id), *arguments)     #Duda ARGS
            #
            #                 content = {"station_id": str(self.agent.jid)}
            #                 self.accept_request_agent(agent_id, content)
            #
            #                 logger.info(
            #                     "Station {} has put {} in the waiting_list".format(
            #                         self.agent.name,
            #                         agent_id,
            #                     )
            #                 )
            #         else:
            #             logger.warning(
            #                 "Station {} has not received agent position of {} from the Simulator".format(
            #                     self.agent.name,
            #                     agent_id,
            #                 )
            #             )
            #
            #     # time statistics update
            #     if self.total_queue_size(service_name):
            #         self.agent.empty_queue_time = time.time()
            #         self.agent.total_busy_time += (
            #             self.agent.empty_queue_time - self.agent.transports_in_queue_time
            #         )

class CheckNearBehaviour(OneShotBehaviour):
    def __init__(self, simulatorjid, user_agent_id, service_name, object_type, arguments):
        super().__init__()

        self.agent_simulator_id = simulatorjid
        self.user_agent_id = user_agent_id
        self.service_name = service_name
        self.object_type = object_type
        self.arguments = arguments
        self.agent_position = None

        #if 'transport_need' in kwargs:
        #    self.transport_need = kwargs['transport_need']

    async def request_agent_position_near(self, agent_id, content):
        reply = Message()
        reply.to = str(agent_id)
        reply.set_metadata("protocol", COORDINATION_PROTOCOL)
        reply.set_metadata("performative", REQUEST_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def run(self):

        content = {"user_agent_id": self.user_agent_id, "object_type": self.object_type}
        await self.request_agent_position_near(agent_id=self.agent_simulator_id, content=content)

        msg = await self.receive(timeout=30)

        if msg:
            performative = msg.get_metadata("performative")
            protocol = msg.get_metadata("protocol")
            agent_id = msg.sender
            content = json.loads(msg.body)

            if (
                    protocol == COORDINATION_PROTOCOL and performative == INFORM_PERFORMATIVE
            ):  # comes from send_confirmation_travel

                if "agent_position" in content:
                    agent_position = content["agent_position"]

                if "user_agent_id" in content:
                    user_agent_id = content["user_agent_id"]

                logger.warning(
                    "NEAR depuracion - agent_position: {}, user_agent_id {}".format(
                        agent_position,
                        user_agent_id
                    )
                )

                #logger.warning(
                #    "NEAR_LIST: {} ".format(
                #        self.agent.near_list[user_agent_id]
                #    )
                #)

                # Dentro del objeto
                #service_name = self.agent.near_list[user_agent_id]["service_name"]
                #arguments = self.agent.near_list[user_agent_id]["arguments"]
                #del self.agent.near_list[user_agent_id]

                logger.debug(
                    "Station {} has received msg from agent {} for near check".format(
                        self.agent.name,
                        agent_id
                    )
                )

                self.agent_position = agent_position
                #self.result = (self.user_agent_id, self.service_name, agent_position, self.arguments)
                #return (self.user_agent_id, self.service_name, agent_position, self.arguments)

                # Fuera del objeto
                # if service_name not in self.agent.waiting_lists or not self.agent.near_agent(
                #         coords_1=self.agent.get_position(), coords_2=agent_position):  # New
                #
                #     await self.refuse_request_agent(user_agent_id)
                #     logger.warning(
                #         "Station {} has REFUSED request from agent {} for service {}".format(
                #             self.agent.name,
                #             user_agent_id,
                #             service_name
                #         )
                #     )
                # else:
                #
                #     if self.total_queue_size(service_name) == 0:
                #         self.agent.transports_in_queue_time = time.time()
                #
                #     # Encolamos
                #     self.queue_agent_to_waiting_list(service_name, str(user_agent_id), **arguments)
                #     # self.queue_agent_to_waiting_list(service_name, str(agent_id), *arguments)     #Duda ARGS
                #
                #     if self.total_queue_size(service_name) > self.agent.max_queue_length:
                #         self.agent.max_queue_length = self.total_queue_size(service_name)
                #
                #     content = {"station_id": str(self.agent.jid)}
                #     await self.accept_request_agent(user_agent_id, content)
                #
                #     logger.info(
                #         "Station {} has put {} in the waiting_list".format(
                #             self.agent.name,
                #             user_agent_id,
                #         )
                #     )
            else:
                logger.warning(
                    "Station {} has not received agent position of {} from the Simulator".format(
                        self.agent.name,
                        agent_id,
                    )
                )

        #return
