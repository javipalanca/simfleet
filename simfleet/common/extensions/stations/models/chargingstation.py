import json
import datetime
import asyncio

from loguru import logger
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, TimeoutBehaviour
from spade.message import Message
from spade.template import Template
from asyncio import CancelledError

from simfleet.common.servicestationagent import ServiceStationAgent

from simfleet.communications.protocol import (
    REGISTER_PROTOCOL,
    REQUEST_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    CANCEL_PERFORMATIVE,
    INFORM_PERFORMATIVE,
    COORDINATION_PROTOCOL,
)


class ChargingStationAgent(ServiceStationAgent):
    def __init__(self, agentjid, password):
        ServiceStationAgent.__init__(self, agentjid, password)

        self.power = None  # Test charging variable --- Analice     #POSIBLE BORRADO DEL ATRIBUTO
        self.service_type = None
        #self.arguments = kwargs.get('args', None)       #ARRAY
        self.arguments = []

        self.charged_transports = 0

    # New function - Know if the agent is stopped
    def is_stopped(self):
        return self.stopped

    def is_ready(self):
        return self.ready

    def set_service_type(self, service_type):
        self.service_type = service_type

    def get_service_type(self):
        return self.service_type

    def set_power(self, power):
        self.power = power

    def run_strategy(self):
        """
        Sets the strategy for the transport agent.
        """
        if not self.running_strategy:
            #template = Template()
            #template.set_metadata("protocol", REQUEST_PROTOCOL)
            #self.add_behaviour(self.strategy(), template)
            self.running_strategy = True

    def to_json(self):
        """
        Serializes the main information of a station agent to a JSON format.
        It includes the id of the agent, its current position, the destination coordinates of the agent,
        the current status, the transport that it has assigned (if any) and its waiting time.

        Returns:
            dict: a JSON doc with the main information of the station.

            Example::

                {
                    "id": "cphillips",
                    "position": [ 39.461327, -0.361839 ],
                    "status": True,
                    "places": 10,
                    "power": 10
                }
        """
        return {
            "id": self.agent_id,
            "position": self.get("current_pos"),
            "status": self.status,
            #"places": self.get_slot_number_used(self.get_service_type()),      #CHECK FRONTEND
            "power": self.power,
            "icon": self.icon,
        }


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

    #def set_registration(self, decision):
    #    self.agent.registration = decision

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
            #"type": self.agent.service_type, #CAMBIARLO POR SERVICE_TYPE
            "type": self.agent.show_services(),
            #"status": self.agent.status,
            "position": self.agent.get_position(),
            #"charge": self.agent.power,
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
                    self.agent.set_registration(True)
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
    #def __init__(self, agent_id, *args):        #ADAPTAR PARA QUE RECIBA LOS ARGS -- APUNTES
    def __init__(self, agent_id, **kwargs):
        super().__init__()
        self.agent_id = agent_id
        #self.power = power
        #TEST
        #self.transport_need = args[0]
        #self.power = args[1]

        if 'transport_need' in kwargs:
            self.transport_need = kwargs['transport_need']

        if 'service_name' in kwargs:
            self.service_type = kwargs['service_name']

        if 'power' in kwargs:
            self.power = kwargs['power']

        #self.additional_args = args
        #super().__init__()

    async def charging_transport(self):
        #total_time = need / self.power
        total_time = self.transport_need / self.power
        #total_time = self.transport_need / self.agent.power
        recarge_time = datetime.timedelta(seconds=total_time)
        logger.info(
            "Station {} started charging transport {} for {} seconds.".format(
                self.agent.name, self.agent_id, recarge_time.total_seconds()
            )
        )

        self.agent.charged_transports += 1

        logger.info(
            "DEPURACION CHARGINGSTATION - Station {} started charging transport {} for {} seconds.".format(
                self.agent.name, self.agent_id, recarge_time.total_seconds()
            )
        )

        await asyncio.sleep(recarge_time.total_seconds())       #Check seconds - Testing


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
        logger.debug("Station {} start charging.".format(self.agent.name))

        #DEPURACION
        logger.warning("START CHARGING - Station {} start charging.".format(self.agent.name))

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

        #service_name = "electricity"
        logger.info(
            "Agent {} has finished receiving the service {}".format(
                self.agent_id,
                self.service_type
            )
        )

        await self.inform_charging_complete()

        logger.info(
            "CHARGINGSTATION DEPURACION - Agent {}, slots usados: {}".format(
                self.agent.name,
                self.agent.get_slot_number_used(self.service_type)
            )
        )

        self.agent.decrease_slots_used(self.service_type)
        #return

        logger.info(
            "CHARGINGSTATION DEPURACION - Agent {}, slots usados: {}".format(
                self.agent.name,
                self.agent.get_slot_number_used(self.service_type)
            )
        )

class GasolineService(OneShotBehaviour):
    #def __init__(self, agent_id, *args):        #ADAPTAR PARA QUE RECIBA LOS ARGS -- APUNTES
    def __init__(self, agent_id, **kwargs):
        super().__init__()
        self.agent_id = agent_id
        #self.power = power
        #TEST
        #self.transport_need = args[0]
        #self.power = args[1]

        if 'transport_need' in kwargs:
            self.transport_need = kwargs['transport_need']

        if 'service_name' in kwargs:
            self.service_type = kwargs['service_name']

        if 'refueling_rate' in kwargs:
            self.refueling_rate = kwargs['refueling_rate']

        #self.additional_args = args
        #super().__init__()

    async def charging_transport(self):
        #total_time = need / self.power
        total_time = self.transport_need / self.refueling_rate
        #total_time = self.transport_need / self.agent.power
        recarge_time = datetime.timedelta(seconds=total_time)
        logger.info(
            "Station {} started charging transport {} for {} seconds.".format(
                self.agent.name, self.agent_id, recarge_time.total_seconds()
            )
        )

        self.agent.charged_transports += 1

        logger.info(
            "DEPURACION CHARGINGSTATION - Station {} started charging transport {} for {} seconds.".format(
                self.agent.name, self.agent_id, recarge_time.total_seconds()
            )
        )

        await asyncio.sleep(recarge_time.total_seconds())       #Check seconds - Testing


    async def inform_charging_complete(self):

        reply = Message()
        reply.to = str(self.agent_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        content = {"charged": True}
        reply.body = json.dumps(content)
        await self.send(reply)

    async def run(self):
        logger.debug("Station {} start charging.".format(self.agent.name))

        #DEPURACION
        logger.warning("START CHARGING - Station {} start charging.".format(self.agent.name))

        await self.charging_transport()

        #service_name = "electricity"
        logger.info(
            "Agent {} has finished receiving the service {}".format(
                self.agent_id,
                self.service_type
            )
        )

        await self.inform_charging_complete()

        logger.info(
            "CHARGINGSTATION DEPURACION - Agent {}, slots usados: {}".format(
                self.agent.name,
                self.agent.get_slot_number_used(self.service_type)
            )
        )

        self.agent.decrease_slots_used(self.service_type)
        #return

        logger.info(
            "CHARGINGSTATION DEPURACION - Agent {}, slots usados: {}".format(
                self.agent.name,
                self.agent.get_slot_number_used(self.service_type)
            )
        )


class DieselService(OneShotBehaviour):
    #def __init__(self, agent_id, *args):        #ADAPTAR PARA QUE RECIBA LOS ARGS -- APUNTES
    def __init__(self, agent_id, **kwargs):
        super().__init__()
        self.agent_id = agent_id
        #self.power = power
        #TEST
        #self.transport_need = args[0]
        #self.power = args[1]

        if 'transport_need' in kwargs:
            self.transport_need = kwargs['transport_need']

        if 'service_name' in kwargs:
            self.service_type = kwargs['service_name']

        if 'refueling_rate' in kwargs:
            self.refueling_rate = kwargs['refueling_rate']

        #self.additional_args = args
        #super().__init__()

    async def charging_transport(self):
        #total_time = need / self.power
        total_time = self.transport_need / self.refueling_rate
        #total_time = self.transport_need / self.agent.power
        recarge_time = datetime.timedelta(seconds=total_time)
        logger.info(
            "Station {} started charging transport {} for {} seconds.".format(
                self.agent.name, self.agent_id, recarge_time.total_seconds()
            )
        )

        self.agent.charged_transports += 1

        logger.info(
            "DEPURACION CHARGINGSTATION - Station {} started charging transport {} for {} seconds.".format(
                self.agent.name, self.agent_id, recarge_time.total_seconds()
            )
        )

        await asyncio.sleep(recarge_time.total_seconds())       #Check seconds - Testing


    async def inform_charging_complete(self):

        reply = Message()
        reply.to = str(self.agent_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        content = {"charged": True}
        reply.body = json.dumps(content)
        await self.send(reply)


    async def run(self):
        logger.debug("Station {} start charging.".format(self.agent.name))

        #DEPURACION
        logger.warning("START CHARGING - Station {} start charging.".format(self.agent.name))

        await self.charging_transport()

        #service_name = "electricity"
        logger.info(
            "Agent {} has finished receiving the service {}".format(
                self.agent_id,
                self.service_type
            )
        )

        await self.inform_charging_complete()

        logger.info(
            "CHARGINGSTATION DEPURACION - Agent {}, slots usados: {}".format(
                self.agent.name,
                self.agent.get_slot_number_used(self.service_type)
            )
        )

        self.agent.decrease_slots_used(self.service_type)
        #return

        logger.info(
            "CHARGINGSTATION DEPURACION - Agent {}, slots usados: {}".format(
                self.agent.name,
                self.agent.get_slot_number_used(self.service_type)
            )
        )
