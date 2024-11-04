from loguru import logger

from simfleet.common.agents.fleetmanager import FleetManagerStrategyBehaviour


################################################################
#                                                              #
#                     FleetManager Strategy                    #
#                                                              #
################################################################

class DelegateRequestBehaviour(FleetManagerStrategyBehaviour):
    """
    The default strategy for the FleetManager agent. By default it delegates all requests to all transports.
    """

    async def run(self):
        if not self.agent.registration:
            await self.send_registration()

        msg = await self.receive(timeout=5)
        logger.debug("Manager received message: {}".format(msg))
        if msg:
            for transport in self.get_transport_agents().values():
                msg.to = str(transport["jid"])
                logger.debug(
                    "Manager sent request to transport {}".format(transport["name"])
                )
                await self.send(msg)
