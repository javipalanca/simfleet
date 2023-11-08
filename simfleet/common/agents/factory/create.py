import abc
import sys
from abc import ABC, abstractmethod

from loguru import logger

from simfleet.common.agents.directory import DirectoryAgent
from simfleet.common.agents.fleetmanager import FleetManagerAgent

from simfleet.utils.reflection import load_class


class Factory(ABC):     #Factory
    @classmethod
    @abstractmethod
    def create_agent(cls,
                    domain,
                    name,
                    password,
                    default_strategy,
                    strategy,
                    jid_directory,
                    fleetmanager,
                    fleet_type,
                    route_host,
                    autonomy,
                    current_autonomy,
                    position,
                    speed,
                    target,
                    power,
                    places,
                    ):
        raise NotImplementedError


class DirectoryFactory(Factory):    #DirectoryFactory
    @classmethod
    def create_agent(cls,
                    domain,
                    name,
                    password,
                    default_strategy,
                    strategy=None,
                    jid_directory=None,
                    fleetmanager=None,
                    fleet_type=None,
                    route_host=None,
                    autonomy=None,
                    current_autonomy=None,
                    position=None,
                    speed=None,
                    target=None,
                    power=None,
                    places=None,
                    ):
        """
                        Create a directory agent.

                        Args:
                            domain(str): domain of the agent
                            name (str): name of the agent
                            password (str): password of the agent
                            default_strategy (class, optional): strategy class of the agent
                        """
        jid = f"{name}@{domain}"
        logger.debug("Creating Directory agent: {}".format(jid))
        agent = DirectoryAgent(jid, password)  # Crea el usuario y la conexión con el XMPP
        agent.set_id(name)  #Establece el identificador del agente
        agent.strategy = default_strategy   #Añadimos el objeto de la clase cargada a la variable strategy
        return agent


class FleetManagerFactory(Factory):      #ManagerFactory
    @classmethod
    def create_agent(cls,
                    domain,
                    name,
                    password,
                    default_strategy,
                    strategy=None,
                    jid_directory=None,
                    fleetmanager=None,
                    fleet_type=None,
                    route_host=None,
                    autonomy=None,
                    current_autonomy=None,
                    position=None,
                    speed=None,
                    target=None,
                    power=None,
                    places=None,
                    ):
        """
                        Create a fleetmanager agent.

                        Args:
                            domain (str): name of domain xmpp
                            name (str): name of the agent
                            password (str): password of the agent
                            default_strategy (class): default strategy class of the agent
                            strategy (class, optional): strategy class of the agent
                            jid_directory (JID): directory JID address
                            fleet_type (str): type of fleet to be used

                        """
        jid = f"{name}@{domain}"
        logger.debug("Creating FleetManager agent: {}".format(jid))
        agent = FleetManagerAgent(jid, password)  # Crea el usuario y la conexión con el XMPP
        agent.set_id(name)  # Establece el identificador del agente
        agent.set_directory(jid_directory)

        if type(strategy) is str:
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = default_strategy

        logger.debug("Assigning type {} to fleetmanager {}".format(fleet_type, agent.agent_id))
        agent.set_fleet_type(fleet_type)
        return agent
