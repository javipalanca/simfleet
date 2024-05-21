import json
import asyncio

from spade.behaviour import CyclicBehaviour, OneShotBehaviour, TimeoutBehaviour
from spade.message import Message
from spade.template import Template
from loguru import logger

from simfleet.common.queuestationagent import QueueStationAgent

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    ACCEPT_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    COORDINATION_PROTOCOL,
)

class ServiceStationAgent(QueueStationAgent):
    #def __init__(self, agentjid, password):
    #    QueueStationAgent.__init__(self, agentjid, password)


    async def setup(self):
        logger.info("Service station agent {} running".format(self.name))

        #template1 = Template()
        #template1.set_metadata("protocol", REQUEST_PROTOCOL)
        #template1.set_metadata("performative", ACCEPT_PERFORMATIVE)

        #template2 = Template()
        #template2.set_metadata("protocol", REQUEST_PROTOCOL)
        #template2.set_metadata("performative", CANCEL_PERFORMATIVE)

        #self.add_behaviour(self.ServiceRunBehaviour(), template1 | template2)
        service_run_behaviour = self.ServiceRunBehaviour()
        self.add_behaviour(service_run_behaviour)
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


        async def cancel_service(self, agent_id, content=None):
            """
            Sends a ``spade.message.Message`` to a transport to accept a travel proposal for charge.
            It uses the REQUEST_PROTOCOL and the ACCEPT_PERFORMATIVE.

            Args:
                transport_id (str): The Agent JID of the transport
            """
            reply = Message()
            reply.to = str(agent_id)
            reply.set_metadata("protocol", REQUEST_PROTOCOL)
            #reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
            reply.set_metadata("performative", INFORM_PERFORMATIVE)
            content = {"station_id": self.agent.name}
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

            #if self.agent.service_available(self):
            #    self.agent.queue_agent_to_waiting_list(service_name, str(agent_id))
            #    self.agent.total_queue_size()

            for service_name, queue in self.agent.waiting_lists.items():

                if len(queue) > 0:
                    if self.agent.service_available(self, service_name):
                        # dequeue
                        agent = self.agent.dequeue_first_agent_to_waiting_list(service_name)
                        self.agent.increase_slots_used(service_name)
                        #Preguntar simulatorAgent para el near -
                        #await self.inform_agent(str(agent))

                        # Send msg to SimulatorAgent for agent_position
                        self.agent.request_agent_position("simulator@localhost")

                        # Request to SimulatorAgent for agent_position


                        msg = await self.receive(timeout=5)     #Duda PREGUNTAR - While hasta tener agent_position?

                        if msg:
                            performative = msg.get_metadata("performative")
                            agent_id = msg.sender
                            agent_position = json.loads(msg.content)["agent_position"]

                            if not self.agent.near_agent(coords_1=self.agent.get_position(), coords_2=agent_position):
                                logger.warning(
                                    "Station {} has Cancel request from agent {} for service {}".format(
                                        self.agent.name,
                                        agent_id,
                                        service_name
                                    )
                                )

                                # Msg Cancel
                                await self.cancel_service(str(agent))

                            else:

                                # Duda
                                one_shot_behaviour = self.agent.waiting_lists[service_name]["one_shot_behaviour"]
                                self.agent.add_behaviour(one_shot_behaviour(agent))


                                logger.info(
                                    "Agent {} has been put in the waiting_list".format(
                                        self.agent.name
                                    )
                                )

                                # Run service -- Duda

                                self.agent.decrease_slots_used(service_name)



class ChargingService(OneShotBehaviour):
    def __init__(self, agent_id):
        self.agent_id = agent_id
        super().__init__()

    async def inform_charging_complete(self):

        reply = Message()
        reply.to = str(self.agent_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        #reply.body = json.dumps(content)
        await self.send(reply)

    async def calculate_charging_time(self, need, power):
        total_time = need / power
        #now = datetime.datetime.now()
        #start_at = now + datetime.timedelta(seconds=total_time)
        #logger.info(
        #    "Station {} started charging transport {} for {} seconds. From {} to {}.".format(
        #        self.name,
        #        transport_id,
        #        total_time,
        #        now,
        #        start_at
        #    )
        #)

    async def run(self):
        logger.debug("Station {} finished charging.".format(self.agent.name))
        await asyncio.sleep(1)
        await self.inform_charging_complete()
