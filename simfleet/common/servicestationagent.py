import json
import datetime
import asyncio

from loguru import logger
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, TimeoutBehaviour
from spade.message import Message
from spade.template import Template

from simfleet.common.queuestationagent import QueueStationAgent

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    ACCEPT_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    COORDINATION_PROTOCOL,
)

class ServiceStationAgent(QueueStationAgent):
    def __init__(self, agentjid, password):
        QueueStationAgent.__init__(self, agentjid, password)


    async def setup(self):
        await super().setup()
        logger.info("Service station agent {} running".format(self.name))

        #template1 = Template()
        #template1.set_metadata("protocol", REQUEST_PROTOCOL)
        #template1.set_metadata("performative", ACCEPT_PERFORMATIVE)

        #template2 = Template()
        #template2.set_metadata("protocol", REQUEST_PROTOCOL)
        #template2.set_metadata("performative", CANCEL_PERFORMATIVE)

        #self.add_behaviour(self.ServiceRunBehaviour(), template1 | template2)

        self.add_behaviour(self.ServiceRunBehaviour())
        #Template for CANCEL y ACCEPT

    #Ajustar nombers de los def
    #def increase_service_slot(self, service_type):
    def increase_slots_used(self, service_type):
        if service_type in self.services_list:
            self.services_list[service_type]["slots_in_use"] += 1

    #def decrease_service_slot(self, service_type):
    def decrease_slots_used(self, service_type):
        if service_type in self.services_list:
            self.services_list[service_type]["slots_in_use"] -= 1

    #def get_service_slot_number(self, service_type):
    def get_slot_number(self, service_type):
        return self.services_list[service_type]["slots"]

    def get_slot_number_used(self, service_type):
        return self.services_list[service_type]["slots_in_use"]

    def service_available(self, service_name):
        if self.services_list[service_name]["slots_in_use"] >= self.services_list[service_name]["slots"]:
            return False
        return True


        # For ServiceRunBehaviour -- cordinate protocol

    class ServiceRunBehaviour(CyclicBehaviour):

        def __init__(self):
            super().__init__()
            #self.test = []

        #Posible eliminación
        #async def cancel_service(self, agent_id, content=None):
        async def refuse_service(self, agent_id, content=None):
            """
            Sends a ``spade.message.Message`` to a transport to accept a travel proposal for charge.
            It uses the REQUEST_PROTOCOL and the ACCEPT_PERFORMATIVE.

            Args:
                agent_id (str): The Agent JID of the agent
                content (dict): Content of the agent
            """
            reply = Message()
            reply.to = str(agent_id)
            reply.set_metadata("protocol", REQUEST_PROTOCOL)
            #reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
            #reply.set_metadata("performative", INFORM_PERFORMATIVE)
            reply.set_metadata("performative", REFUSE_PERFORMATIVE)
            #content = {"station_id": self.agent.name}
            reply.body = json.dumps(content)
            await self.send(reply)
            logger.debug(
                "Service {} request position of agent {}".format(
                    self.agent.name,
                    agent_id
                )
            )

        async def inform_service(self, agent_id, content=None):
            """
            Sends a ``spade.message.Message`` to a transport to accept a travel proposal for charge.
            It uses the REQUEST_PROTOCOL and the ACCEPT_PERFORMATIVE.

            Args:
                agent_id (str): The Agent JID of the agent
                content (dict): Content of the agent
            """
            if content is None:
                content = {}
            reply = Message()
            reply.to = str(agent_id)
            reply.set_metadata("protocol", REQUEST_PROTOCOL)
            #reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
            reply.set_metadata("performative", INFORM_PERFORMATIVE)
            #content = {"station_id": self.agent.name}
            reply.body = json.dumps(content)
            await self.send(reply)
            logger.debug(
                "Service {} request position of agent {}".format(
                    self.agent.name,
                    agent_id
                )
            )

        async def on_start(self):
            logger.debug("Strategy {} started in station".format(type(self).__name__))

        async def run(self):

            template1 = Template()
            template1.set_metadata("protocol", REQUEST_PROTOCOL)
            template1.set_metadata("performative", INFORM_PERFORMATIVE)

            # DEPURACION 2
            # logger.warning(
            #    "Service {} TIENE LA SIGUIENTE waitinglist {}".format(
            #        self.agent.name,
            #        self.agent.waiting_lists
            #    )
            # )

            # if self.agent.service_available(self):
            #    self.agent.queue_agent_to_waiting_list(service_name, str(agent_id))
            #    self.agent.total_queue_size()

            for service_name, queue in self.agent.waiting_lists.items():

                if len(queue) > 0:

                    # DEPURACION 6
                    # logger.info(
                    #    "SERVICESTATION - service_name {}".format(
                    #        service_name
                    #    )
                    # )

                    if self.agent.service_available(service_name):
                        # dequeue
                        # agent_info = self.agent.dequeue_first_agent_to_waiting_list(service_name)        #Adaptar los ARGS -- APUNTES
                        agent_info = self.agent.queuebehaviour.dequeue_first_agent_to_waiting_list(service_name)

                        if agent_info is not None:
                            agent, kwargs = agent_info

                            # DEPURACION 8
                            logger.warning(
                                "SERVICESTATION - Agent {}, slots usados: {}".format(
                                    self.agent.name,
                                    self.agent.get_slot_number_used(service_name)
                                )
                            )

                            self.agent.increase_slots_used(service_name)

                            content = {"station_id": self.agent.name, "serving": True}
                            await self.inform_service(str(agent), content)

                            # DEPURACION 7
                            logger.info(
                                "SERVICESTATION - agent: {}, args: {}, station slots: {}".format(
                                    agent,
                                    kwargs,
                                    self.agent.get_slot_number_used(service_name)
                                )
                            )

                            # Duda
                            one_shot_behaviour = self.agent.services_list[service_name]["one_shot_behaviour"]

                            # DEPURACION 8
                            logger.info(
                                "SERVICESTATION 1 - one_shot_behaviour: {}".format(
                                    one_shot_behaviour
                                )
                            )

                            one_shot_behaviour = one_shot_behaviour(str(agent), **kwargs)

                            # DEPURACION 8
                            logger.info(
                                "SERVICESTATION 2 - one_shot_behaviour: {}".format(
                                    one_shot_behaviour
                                )
                            )

                            # DEPURACION 8
                            # logger.info(
                            #    "SERVICESTATION 3 - one_shot_behaviour: {}".format(
                            #        one_shot_behaviour
                            #    )
                            # )

                            self.agent.add_behaviour(one_shot_behaviour, template1)  # PASAR ARGS (self.agent.power)

                            # TEST - NO FUNCIONA
                            # logger.info(
                            #    "Agent {} has finished receiving the service {}".format(
                            #        self.agent.name,
                            #        service_name
                            #    )
                            # )

                            # Run service -- Duda

                            # TEST - NO FUNCIONA
                            # self.agent.decrease_slots_used(service_name)

            # COPIA ORIGINAL
            # for service_name, queue in self.agent.waiting_lists.items():
            #
            #     if len(queue) > 0:
            #         if self.agent.service_available(self, service_name):
            #             # dequeue
            #             agent_info = self.agent.dequeue_first_agent_to_waiting_list(service_name)        #Adaptar los ARGS -- APUNTES
            #
            #             if agent_info is not None:
            #                 agent, args = agent_info
            #
            #                 self.agent.increase_slots_used(service_name)
            #
            #
            #                 #DEBATE - INFORMAR AGENTE DE QUE COMIENZA EL SERVICIO - SERVICIO_1a
            #
            #
            #
            #                 #Preguntar simulatorAgent para el near -
            #                 #await self.inform_agent(str(agent))
            #
            #                 # Send msg to SimulatorAgent for agent_position
            #                 self.agent.request_agent_position("simulator_none@localhost")
            #
            #                 # Request to SimulatorAgent for agent_position
            #
            #
            #                 msg = await self.receive(timeout=5)
            #                 content = json.loads(msg.body)
            #
            #                 if msg:
            #                     performative = msg.get_metadata("performative")
            #                     agent_id = msg.sender
            #                     #agent_position = json.loads(msg.body)["agent_position"]
            #                     agent_position = content["agent_position"]
            #
            #                     if not self.agent.near_agent(coords_1=self.agent.get_position(), coords_2=agent_position):
            #                         logger.warning(
            #                             "Station {} has Cancel request from agent {} for service {}".format(
            #                                 self.agent.name,
            #                                 agent_id,
            #                                 service_name
            #                             )
            #                         )
            #
            #                         # Msg Cancel
            #                         #self.cancel_service(str(agent))        #Original version
            #
            #                         #New version
            #                         content = {"station_id": self.agent.name}
            #                         self.refuse_service(str(agent), content)
            #                     else:
            #
            #                         content = {"station_id": self.agent.name, "serving":True}
            #                         self.inform_service(str(agent), content)
            #
            #                         # Duda
            #                         one_shot_behaviour = self.agent.waiting_lists[service_name]["one_shot_behaviour"]
            #                         self.agent.add_behaviour(one_shot_behaviour(agent_id=agent_id, *args), template1)        #PASAR ARGS (self.agent.power)
            #
            #
            #
            #                         logger.info(
            #                             "Agent {} has finished receiving the service {}".format(
            #                                 self.agent.name,
            #                                 service_name
            #                             )
            #                         )
            #
            #                         # Run service -- Duda
            #
            #                         self.agent.decrease_slots_used(service_name)
            #
