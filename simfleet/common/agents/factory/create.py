import abc
import sys
from abc import ABC, abstractmethod

from loguru import logger

from simfleet.common.agents.directory import DirectoryAgent

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
                            strategy (class, optional): strategy class of the agent
                        """
        jid = f"{name}@{domain}"
        logger.debug("Creating Directory agent: {}".format(jid))
        agent = DirectoryAgent(jid, password)  # Crea el usuario y la conexión con el XMPP
        agent.set_id(name)  #Establece el identificador del agente
        agent.strategy = default_strategy   #Añadimos el objeto de la clase cargada a la variable strategy
        return agent
