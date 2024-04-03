from loguru import logger

#from simfleet.common.agents.customer import CustomerStrategyBehaviour
from simfleet.common.agents.fleetmanager import FleetManagerStrategyBehaviour


#from simfleet.common.agents.transport import TransportStrategyBehaviour        #transport.py


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




################################################################
#                                                              #
#                     Vehicle Strategy                         #
#                                                              #
################################################################
#class RequestAndTravelBehavior(VehicleStrategyBehaviour):
#    """
#    The default strategy for the Vehicle agent. By default it register and move agent to the destination.
#    """

#    async def run(self):

#        if self.agent.status != None and self.agent.status == VEHICLE_WAITING:
#            try:
#                logger.debug(
#                    "Transport {} continue the trip".format(
#                        self.agent.name
#                    )
#                )

#                await self.planned_trip()
#                return
#            except PathRequestException:
#                logger.error(
#                    "Transport {} could not get a path to customer. Cancelling...".format(
#                        self.agent.name
#                    )
#                )
#                return


