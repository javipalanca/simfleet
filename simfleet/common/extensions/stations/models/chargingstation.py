import json
import datetime
import asyncio

from loguru import logger
from asyncio import CancelledError
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template

from simfleet.common.servicestationagent import ServiceStationAgent

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    COORDINATION_PROTOCOL,
    REGISTER_PROTOCOL,
)

class ChargingStationAgent(ServiceStationAgent):
    def __init__(self, agentjid, password):
        ServiceStationAgent.__init__(self, agentjid, password)

        self.power = None  # Test charging variable --- Analice     #POSIBLE BORRADO DEL ATRIBUTO
        self.service_type = None
        #self.arguments = kwargs.get('args', None)       #ARRAY

    # New function - Know if the agent is stopped
    def is_stopped(self):
        return self.stopped

    def is_ready(self):
        return self.ready

    def set_type(self, service_type):
        self.service_type = service_type

    def set_power(self, power):
        self.power = power

    async def setup(self):
        await super().setup()
        self.total_busy_time = 0.0
        logger.info("Station agent {} running".format(self.name))
        #self.set_type("station")       #AÑADIR A FACTORY
        #self.set_status()
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = RegistrationBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning(
                    "Station {} could not create RegisterBehaviour. Retrying...".format(
                        self.agent_id
                    )
                )
                self.add_behaviour(register_behaviour, template)
        except Exception as e:
            logger.error(
                "EXCEPTION creating RegisterBehaviour in Station {}: {}".format(
                    self.agent_id, e
                )
            )

        self.ready = True


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
            "Station {} sent proposal to register to directory {}".format(
                self.agent.name, self.agent.directory_id
            )
        )

        content = {
            "jid": str(self.agent.jid),
            "type": self.agent.service_type, #CAMBIARLO POR SERVICE_TYPE
            #"status": self.agent.status,
            "position": self.agent.get_position(),
            "charge": self.agent.power,
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


#Strategie? - New ubication -> extension > stations > strategies > chargingstation
class ChargingService(OneShotBehaviour):
    def __init__(self, agent_id, *args):        #ADAPTAR PARA QUE RECIBA LOS ARGS -- APUNTES
        self.agent_id = agent_id
        #self.power = power
        self.power = args[0]
        self.transport_need = args[1]
        #self.additional_args = args
        super().__init__()

    async def charging_transport(self):
        #total_time = need / self.power
        total_time = self.transport_need / self.power
        total_time = round(total_time)
        logger.info(
            "Station {} started charging transport {} for {} seconds.".format(
                self.agent.name, self.agent_id, total_time
            )
        )
        await asyncio.sleep(total_time)       #Check seconds - Testing


    async def inform_charging_complete(self):

        reply = Message()
        reply.to = str(self.agent_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        content = {"charged": True}
        reply.body = json.dumps(content)
        await self.send(reply)

    # Codigo para testear - deassigning_place
    # CODIGO PARA TESTEAR
    #async def deassigning_place(self):
    #    """
    #    Leave a space of the charging station, when the station has free spaces, the status will change to FREE_STATION
    #    """
    #    if self.waiting_list:
    #        transport_id = self.waiting_list.pop(0)
            # time statistics update
    #        if len(self.waiting_list) == 0:
    #            self.empty_queue_time = time.time()
    #            self.total_busy_time += (
    #                self.empty_queue_time - self.transports_in_queue_time
    #            )

    #        logger.debug(
    #            "Station {} has a place to charge transport {}".format(
    #                self.agent_id, transport_id
    #            )
    #        )
            # confirm EXPLICITLY to transport it can start charging
    #        reply = Message()
    #        reply.to = str(transport_id)
    #        reply.set_metadata("protocol", REQUEST_PROTOCOL)
    #        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
    #        content = {"station_id": self.agent_id}
    #        reply.body = json.dumps(content)
    #        await self.send(reply)
            # await send_confirmation_to_transport(transport_id)

    #    else:
    #        p = self.get_available_places()
    #        if p + 1:
    #            self.set_status(FREE_STATION)
    #        self.set_available_places(p + 1)

    async def run(self):
        logger.debug("Station {} finished charging.".format(self.agent.name))

        #msg = await self.receive(timeout=60)
        #if not msg:
        #    logger.warning(
        #        "Station {} did not receive a message".format(
        #            self.agent.name
        #        )
        #    )
        #    return

        #content = json.loads(msg.body)
        #transport_id = msg.sender
        #performative = msg.get_metadata("performative")

        #if performative == INFORM_PERFORMATIVE:
            #await asyncio.sleep(1)     #Testing
        #    await self.charging_transport(content["need"], transport_id)
        #    await self.inform_charging_complete()
            #await self.deassigning_place()
        await self.charging_transport()
        await self.inform_charging_complete()
        return
