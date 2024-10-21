import json
from asyncio import CancelledError

from loguru import logger
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template

from simfleet.common.simfleetagent import SimfleetAgent

from simfleet.communications.protocol import (
    REQUEST_PROTOCOL,
    REGISTER_PROTOCOL,
    ACCEPT_PERFORMATIVE,
    REQUEST_PERFORMATIVE,
    REFUSE_PERFORMATIVE,
)
from simfleet.utils.utils_old import StrategyBehaviour


class FleetManagerAgent(SimfleetAgent):
    """
    The FleetManagerAgent is responsible for managing the fleet of transport agents. It registers transport agents
    into its fleet and coordinates the requests between transports and customers.

    Attributes:
        transports_in_fleet (int): The number of transports currently registered in the fleet.
        fleet_icon (str): The icon representing the fleet in visual representations.
    """

    def __init__(self, agentjid, password):
        """
            Initializes the FleetManager agent with the given JID (Jabber ID) and password. It also initializes
            its internal structures to track the transport agents within the fleet.
        """

        super().__init__(agentjid, password)

        self.transports_in_fleet = 0
        self.fleet_icon = None
        self.clear_agents()


    def clear_agents(self):
        """
        Clears the stored set of transport agents and resets the simulation clock. This method is useful for
        resetting the fleet manager state between simulations or sessions.
        """
        self.set("transport_agents", {})

    async def setup(self):
        """
            Sets up the FleetManager agent by registering a behavior that handles the registration of transport agents.
            This method is called automatically when the agent is started.
        """
        logger.info("FleetManager agent {} running".format(self.name))
        try:
            template = Template()
            template.set_metadata("protocol", REGISTER_PROTOCOL)
            register_behaviour = TransportRegistrationForFleetBehaviour()
            self.add_behaviour(register_behaviour, template)
            while not self.has_behaviour(register_behaviour):
                logger.warning(
                    "Manager {} could not create RegisterBehaviour. Retrying...".format(
                        self.agent_id
                    )
                )
                self.add_behaviour(register_behaviour, template)
            self.ready = True
        except Exception as e:
            logger.error(
                "EXCEPTION creating RegisterBehaviour in Manager {}: {}".format(
                    self.agent_id, e
                )
            )

    def set_id(self, agent_id):
        """
        Sets the ID for the agent.

        Args:
            agent_id (str): The new ID for the agent.
        """
        self.agent_id = agent_id

    def set_icon(self, icon):
        """
            Sets the fleet icon for visual representation.

            Args:
                icon (str): The icon identifier for the fleet.
        """
        self.fleet_icon = icon

    def run_strategy(self):
        """
        Runs the fleet management strategy, registering a behavior for handling transport and customer requests.
        """
        if not self.running_strategy:
            template = Template()
            template.set_metadata("protocol", REQUEST_PROTOCOL)
            self.add_behaviour(self.strategy(), template)
            self.running_strategy = True


class TransportRegistrationForFleetBehaviour(CyclicBehaviour):
    """
        This behavior manages the registration of new transport agents in the fleet. It receives requests from
        transport agents and registers them if their fleet type matches the FleetManager's type.
    """
    async def on_start(self):
        logger.debug("Strategy {} started in manager".format(type(self).__name__))

    def add_transport(self, agent):
        """
        Adds a new transport agent to the fleet's internal store.

        Args:
            agent (dict): The details of the transport agent to be added.
        """
        self.agent.transports_in_fleet += 1
        self.get("transport_agents")[agent["name"]] = agent

    def remove_transport(self, key):
        """
        Removes a transport agent from the fleet's internal store by its key.

        Args:
            key (str): The unique key representing the transport agent.
        """
        if key in self.get("transport_agents"):
            del self.get("transport_agents")[key]
            logger.debug("Deregistration of the TransporterAgent {}".format(key))
            self.agent.transports_in_fleet -= 1
        else:
            logger.debug("Cancelation of the registration in the Fleet")

    async def accept_registration(self, agent_id):
        """
        Sends an acceptance message to a transport agent, confirming its registration in the fleet.

        Args:
            agent_id (str): The ID of the transport agent to be accepted.
        """
        reply = Message()
        content = {"icon": self.agent.fleet_icon, "fleet_type": self.agent.fleet_type}
        reply.to = str(agent_id)
        reply.set_metadata("protocol", REGISTER_PROTOCOL)
        reply.set_metadata("performative", ACCEPT_PERFORMATIVE)
        reply.body = json.dumps(content)
        await self.send(reply)

    async def reject_registration(self, agent_id):
        """
        Sends a rejection message to a transport agent, declining its registration request.

        Args:
            agent_id (str): The ID of the transport agent to be rejected.
        """
        reply = Message()
        reply.to = str(agent_id)
        reply.set_metadata("protocol", REGISTER_PROTOCOL)
        reply.set_metadata("performative", REFUSE_PERFORMATIVE)
        reply.body = ""
        await self.send(reply)

    async def run(self):
        """
            Listens for registration requests from transport agents and processes them by accepting or rejecting
            them based on the fleet type.
        """
        try:
            msg = await self.receive(timeout=5)
            if msg:
                performative = msg.get_metadata("performative")
                if performative == REQUEST_PERFORMATIVE:
                    content = json.loads(msg.body)
                    if content["fleet_type"] == self.agent.fleet_type:
                        self.add_transport(content)
                        await self.accept_registration(msg.sender)
                        logger.debug(
                            "Registration in the {} fleet to {}".format(self.agent.name,content.get("name"))
                        )
                    else:
                        await self.reject_registration(msg.sender)

                if performative == ACCEPT_PERFORMATIVE:
                    self.agent.set_registration(True)
                    logger.info("Registration in the dictionary of services")
        except CancelledError:
            logger.debug("Cancelling async tasks...")
        except Exception as e:
            logger.error(
                "EXCEPTION in RegisterBehaviour of Manager {}: {}".format(
                    self.agent.name, e
                )
            )


class FleetManagerStrategyBehaviour(StrategyBehaviour):
    """
    The FleetManagerStrategyBehaviour class defines the main strategy for coordinating customer and transport
    agents in the fleet. This behavior needs to implement a `_process` method for custom strategies.
    """

    async def on_start(self):
        """
            Logs that the strategy has started in the Fleet Manager.
        """
        logger.debug("Strategy {} started in manager".format(type(self).__name__))

    def get_transport_agents(self):
        """
        Returns the list of transport agents currently registered with the FleetManager.

        Returns:
            list: A list of transport agents.
        """
        return self.get("transport_agents")

    async def send_registration(self):
        """
        Sends a registration request to the directory service to register the FleetManager.
        """
        logger.info(
            "Manager {} sent proposal to register to directory {}".format(
                self.agent.name, self.agent.directory_id
            )
        )
        content = {"jid": str(self.agent.jid), "type": self.agent.fleet_type}
        msg = Message()
        msg.to = str(self.agent.directory_id)
        msg.set_metadata("protocol", REGISTER_PROTOCOL)
        msg.set_metadata("performative", REQUEST_PERFORMATIVE)
        msg.body = json.dumps(content)
        await self.send(msg)

    async def run(self):
        """
            A placeholder method that needs to be implemented by any subclass defining specific fleet management strategies.
        """
        raise NotImplementedError
