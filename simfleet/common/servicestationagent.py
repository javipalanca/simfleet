import json

from loguru import logger
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template

from simfleet.common.queuestationagent import QueueStationAgent

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    REFUSE_PERFORMATIVE,
    INFORM_PERFORMATIVE,
)

class ServiceStationAgent(QueueStationAgent):
    """
        ServiceStationAgent is responsible for managing service stations (e.g., charging or refueling stations).
        It extends the QueueStationAgent class, which allows agents to queue for available services.

        Methods:
            setup(): Initializes the service station agent and starts its behavior.
            increase_slots_used(service_type): Increases the number of slots currently in use for a specific service type.
            decrease_slots_used(service_type): Decreases the number of slots currently in use for a specific service type.
            get_slot_number(service_type): Returns the total number of slots available for a specific service type.
            get_slot_number_used(service_type): Returns the number of slots currently in use for a specific service type.
            service_available(service_name): Checks if there are free slots available for a specific service.
    """

    def __init__(self, agentjid, password):
        QueueStationAgent.__init__(self, agentjid, password)


    async def setup(self):
        """
            Initializes the service station and adds its main behavior.
        """
        await super().setup()
        logger.info("Service station agent {} running".format(self.name))
        self.add_behaviour(self.ServiceRunBehaviour())

    def increase_slots_used(self, service_type):
        """
            Increments the number of slots currently in use for a given service type.
        """
        if service_type in self.services_list:
            self.services_list[service_type]["slots_in_use"] += 1

    def decrease_slots_used(self, service_type):
        """
            Decrements the number of slots currently in use for a given service type.
        """
        if service_type in self.services_list:
            self.services_list[service_type]["slots_in_use"] -= 1

    def get_slot_number(self, service_type):
        """
            Returns the total number of slots for the given service type.
        """
        return self.services_list[service_type]["slots"]

    def get_slot_number_used(self, service_type):
        """
            Returns the number of slots currently in use for the given service type.
        """
        return self.services_list[service_type]["slots_in_use"]

    def service_available(self, service_name):
        """
            Checks if there are available slots for the given service name.
            Returns:
                bool: True if the service has available slots, False otherwise.
        """
        if self.services_list[service_name]["slots_in_use"] >= self.services_list[service_name]["slots"]:
            return False
        return True

    def to_json(self):
        data = super().to_json()
        return data


    class ServiceRunBehaviour(CyclicBehaviour):

        def __init__(self):
            super().__init__()

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
            reply.set_metadata("performative", REFUSE_PERFORMATIVE)
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
            reply.set_metadata("performative", INFORM_PERFORMATIVE)
            reply.body = json.dumps(content)
            await self.send(reply)
            logger.debug(
                "Service {} request position of agent {}".format(
                    self.agent.name,
                    agent_id
                )
            )

        async def on_start(self):
            """
                Called when the behavior starts, logging the event.
            """
            logger.debug("Strategy {} started in station".format(type(self).__name__))

        async def run(self):
            """
                Main execution loop that processes the waiting lists and assigns services to agents
                if slots are available. It dequeues agents from the queue and starts the respective service.
            """
            template1 = Template()
            template1.set_metadata("protocol", REQUEST_PROTOCOL)
            template1.set_metadata("performative", INFORM_PERFORMATIVE)

            # Iterate through the available service types and their corresponding queues
            for service_name, queue in self.agent.waiting_lists.items():

                if len(queue) > 0:

                    if self.agent.service_available(service_name):

                        # Dequeue the first agent from the queue for the given service
                        agent_info = self.agent.queuebehaviour.dequeue_first_agent_to_waiting_list(service_name)

                        if agent_info is not None:
                            agent, kwargs = agent_info

                            # Increase the number of slots in use for this service
                            self.agent.increase_slots_used(service_name)

                            # Inform the agent that they are being served
                            content = {"station_id": self.agent.name, "serving": True}
                            await self.inform_service(str(agent), content)

                            logger.info(
                                "Agent: {} with args: {}, station slots used: {}".format(
                                    agent,
                                    kwargs,
                                    self.agent.get_slot_number_used(service_name)
                                )
                            )

                            # Get service-specific arguments
                            arguments_station = self.agent.show_service_arguments(service_name)
                            arguments_station["service_name"] = service_name
                            kwargs.update(arguments_station)

                            # Retrieve and instantiate the appropriate service behavior
                            one_shot_behaviour = self.agent.services_list[service_name]["one_shot_behaviour"]
                            one_shot_behaviour = one_shot_behaviour(str(agent), **kwargs)

                            # Add the behavior to the agent
                            self.agent.add_behaviour(one_shot_behaviour, template1)
