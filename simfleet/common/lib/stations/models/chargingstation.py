import json
import datetime
import asyncio

from loguru import logger
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template
from asyncio import CancelledError

from simfleet.common.agents.station.servicestationagent import ServiceStationAgent

from simfleet.communications.protocol import (
    REGISTER_PROTOCOL,
    REQUEST_PROTOCOL,
    REQUEST_PERFORMATIVE,
    ACCEPT_PERFORMATIVE,
    INFORM_PERFORMATIVE,
)


class ChargingStationAgent(ServiceStationAgent):
    """
        Represents a charging station agent that provides services such as electric charging,
        gasoline refueling, or diesel refueling.

        Methods:
            setup(): Initializes the charging station and its behaviors.
            run_strategy(): Configures the behavior strategy for the station.
            to_json(): Serializes the station's main information to JSON format.
    """

    def __init__(self, agentjid, password):
        ServiceStationAgent.__init__(self, agentjid, password)

        self.arguments = []

    def run_strategy(self):
        """
        Placeholder for setting the strategy behavior for the station.
        """
        if not self.running_strategy:
            self.running_strategy = True

    def to_json(self):
        data = super().to_json()
        return data


    async def setup(self):
        """
            Sets up the agent with its behavior templates for registration.
        """
        await super().setup()
        logger.info("Agent[{}]: Charging station running".format(self.name))
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = RegistrationBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning(
                    "Agent[{}]: The agent could not create RegisterBehaviour. Retrying...".format(
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
    """
        Manages the registration behavior of the charging station, allowing it to register
        with the directory agent.

        Methods:
            on_start(): Initializes the behavior and sets up the logger.
            send_registration(): Sends a registration message to the directory.
            run(): Manages the registration logic and response handling.
    """
    async def on_start(self):
        logger.debug("Agent[{}]: Strategy ({}) started".format(self.agent.name, type(self).__name__))

    async def send_registration(self):
        """
        Sends a registration message to the directory agent with the station's information.
        """
        logger.info(
            "Agent[{}]: The agent sent proposal to register to directory ({})".format(
                self.agent.name, self.agent.directory_id
            )
        )

        content = {
            "jid": str(self.agent.jid),
            "type": self.agent.show_services(),
            "position": self.agent.get_position(),
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
                    logger.debug("Agent[{}]: Registration in the directory".format(self.agent.name))
        except CancelledError:
            logger.debug("Agent[{}]: Cancelling async tasks...".format(self.agent.name))
        except Exception as e:
            logger.error(
                "Agent[{}]: EXCEPTION in RegisterBehaviour: {}".format(
                    self.agent.name, e
                )
            )


class ChargingService(OneShotBehaviour):
    """
        Represents a behavior for charging electric vehicles in the station.
        It manages the charging process and notifies the vehicle when charging is complete.

        Methods:
            charging_transport(): Performs the charging operation and logs the duration.
            inform_charging_complete(): Notifies the vehicle when charging is complete.
            run(): Executes the charging sequence.
        """
    def __init__(self, agent_id, **kwargs):
        super().__init__()
        self.agent_id = agent_id

        if 'transport_need' in kwargs:
            self.transport_need = kwargs['transport_need']

        if 'service_name' in kwargs:
            self.service_type = kwargs['service_name']

        if 'power' in kwargs:
            self.power = kwargs['power']

    async def charging_transport(self):
        """
            Simulates the charging process based on the power and transport need, and logs the operation.
        """
        total_time = self.transport_need / self.power
        recarge_time = datetime.timedelta(seconds=total_time)
        logger.info(
            "Agent[{}]: The agent started charging transport [{}] for ({}) seconds.".format(
                self.agent.name, self.agent_id, recarge_time.total_seconds()
            )
        )

        await asyncio.sleep(recarge_time.total_seconds())


    async def inform_charging_complete(self):
        """
            Sends a message to the transport indicating that the charging is complete.
        """

        reply = Message()
        reply.to = str(self.agent_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        content = {"charged": True}
        reply.body = json.dumps(content)
        await self.send(reply)

    async def run(self):
        """
            Main execution of the charging behavior, performing the charging operation and notifying the transport.
        """
        logger.debug("Agent[{}]: The station start charging.".format(self.agent.name))

        await self.charging_transport()

        logger.info(
            "Agent[{}]: The agent has finished receiving the service ({})".format(
                self.agent_id,
                self.service_type
            )
        )

        await self.inform_charging_complete()

        self.agent.servicebehaviour.decrease_slots_used(self.service_type)

class GasolineService(OneShotBehaviour):
    """
        Represents a behavior for refueling gasoline vehicles at the station.
        Follows a similar structure to the ChargingService class.
    """
    def __init__(self, agent_id, **kwargs):
        super().__init__()
        self.agent_id = agent_id

        if 'transport_need' in kwargs:
            self.transport_need = kwargs['transport_need']

        if 'service_name' in kwargs:
            self.service_type = kwargs['service_name']

        if 'refueling_rate' in kwargs:
            self.refueling_rate = kwargs['refueling_rate']


    async def charging_transport(self):
        """
            Simulates the refueling process based on the refueling rate and logs the operation.
        """
        total_time = self.transport_need / self.refueling_rate
        recarge_time = datetime.timedelta(seconds=total_time)
        logger.info(
            "Station {} started charging transport {} for {} seconds.".format(
                self.agent.name, self.agent_id, recarge_time.total_seconds()
            )
        )

        await asyncio.sleep(recarge_time.total_seconds())


    async def inform_charging_complete(self):
        """
            Sends a message to the transport indicating that the refueling is complete.
        """

        reply = Message()
        reply.to = str(self.agent_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        content = {"charged": True}
        reply.body = json.dumps(content)
        await self.send(reply)

    async def run(self):
        logger.debug("Station {} start charging.".format(self.agent.name))

        await self.charging_transport()

        logger.info(
            "Agent {} has finished receiving the service {}".format(
                self.agent_id,
                self.service_type
            )
        )

        await self.inform_charging_complete()

        self.agent.servicebehaviour.decrease_slots_used(self.service_type)


class DieselService(OneShotBehaviour):
    """
        Represents a behavior for refueling diesel vehicles at the station.
        Follows a similar structure to the GasolineService class.
        """
    def __init__(self, agent_id, **kwargs):
        super().__init__()
        self.agent_id = agent_id

        if 'transport_need' in kwargs:
            self.transport_need = kwargs['transport_need']

        if 'service_name' in kwargs:
            self.service_type = kwargs['service_name']

        if 'refueling_rate' in kwargs:
            self.refueling_rate = kwargs['refueling_rate']

    async def charging_transport(self):
        """
            Simulates the refueling process for diesel based on the refueling rate and logs the operation.
        """
        total_time = self.transport_need / self.refueling_rate
        recarge_time = datetime.timedelta(seconds=total_time)
        logger.info(
            "Station {} started charging transport {} for {} seconds.".format(
                self.agent.name, self.agent_id, recarge_time.total_seconds()
            )
        )

        await asyncio.sleep(recarge_time.total_seconds())


    async def inform_charging_complete(self):
        """
            Sends a message to the transport indicating that the refueling is complete.
        """
        reply = Message()
        reply.to = str(self.agent_id)
        reply.set_metadata("protocol", REQUEST_PROTOCOL)
        reply.set_metadata("performative", INFORM_PERFORMATIVE)
        content = {"charged": True}
        reply.body = json.dumps(content)
        await self.send(reply)


    async def run(self):
        """
            Main execution of the diesel refueling behavior.
        """
        logger.debug("Station {} start charging.".format(self.agent.name))

        await self.charging_transport()

        logger.info(
            "Agent {} has finished receiving the service {}".format(
                self.agent_id,
                self.service_type
            )
        )

        await self.inform_charging_complete()

        self.agent.servicebehaviour.decrease_slots_used(self.service_type)

