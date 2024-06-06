import abc
import sys
from abc import ABC, abstractmethod

from loguru import logger

from simfleet.common.agents.directory import DirectoryAgent
from simfleet.common.agents.fleetmanager import FleetManagerAgent
from simfleet.common.agents.transport import TransportAgent
#from simfleet.common.agents.customer import CustomerAgent
from simfleet.common.agents.station import StationAgent
from simfleet.common.extensions.vehicles.models.vehicle import VehicleAgent

from simfleet.utils.reflection import load_class


class Factory(ABC):     #Factory
    @classmethod
    @abstractmethod
    def create_agent(cls,
                     domain,
                     name,
                     password,
                     class_,
                     default_strategy,
                     optional,
                     strategy,
                     jid_directory,
                     bbox,
                     fleetmanager,
                     fleet_type,
                     route_host,
                     autonomy,
                     current_autonomy,
                     position,
                     speed,
                     target,
                     service_name,
                     power,
                     slots,
                    ):
        raise NotImplementedError


class DirectoryFactory(Factory):    #DirectoryFactory
    @classmethod
    def create_agent(cls,
                     domain,
                     name,
                     password,
                     default_strategy,
                     class_=None,
                     optional=None,
                     strategy=None,
                     jid_directory=None,
                     bbox=None,
                     fleetmanager=None,
                     fleet_type=None,
                     route_host=None,
                     autonomy=None,
                     current_autonomy=None,
                     position=None,
                     speed=None,
                     target=None,
                     service_name=None,
                     power=None,
                     slots=None,
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
                     class_=None,
                     optional=None,
                     strategy=None,
                     jid_directory=None,
                     bbox=None,
                     fleetmanager=None,
                     fleet_type=None,
                     route_host=None,
                     autonomy=None,
                     current_autonomy=None,
                     position=None,
                     speed=None,
                     target=None,
                     service_name=None,
                     power=None,
                     slots=None,
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


class TransportFactory(Factory):    #TransportFactory
    @classmethod
    def create_agent(cls,
                     domain,
                     name,
                     password,
                     class_,
                     default_strategy,
                     optional=None,
                     strategy=None,
                     jid_directory=None,
                     bbox=None,
                     fleetmanager=None,
                     fleet_type=None,
                     route_host=None,
                     autonomy=None,
                     current_autonomy=None,
                     position=None,
                     speed=None,
                     target=None,
                     service_name=None,
                     power=None,
                     slots=None,
                    ):
        """
                                Create a transport agent.

                                Args:
                                    domain (str): name of domain xmpp
                                    name (str): name of the agent
                                    password (str): password of the agent
                                    default_strategy (class): default strategy class of the agent
                                    strategy (class, optional): strategy class of the agent
                                    jid_directory (JID): directory JID address
                                    fleetmanager (str): fleetmanager JID address
                                    fleet_type (str): type of fleet to be used
                                    route_host (str): route host address
                                    autonomy (str):
                                    current_autonomy (str):
                                    position (str):
                                    speed (str):
                                """
        jid = f"{name}@{domain}"
        logger.debug("Creating Transport agent: {}".format(jid))
        #agent = TransportAgent(jid, password)  # Crea el usuario y la conexión con el XMPP

        if type(class_) is str:   # Añadimos el objeto de la clase cargada a la variable agente_class
            agent_class = load_class(class_)
            if optional:
                agent = agent_class(jid, password, **optional)
            else:
                agent = agent_class(jid, password)
        else:
            raise Exception ("The agent needs a class in path format.")

        agent.set_id(name)  # Establece el identificador del agente
        agent.set_directory(jid_directory)

        if type(strategy) is str:   # Añadimos el objeto de la clase cargada a la variable strategy
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = default_strategy

        logger.debug("Assigning type {} to transport {}".format(fleet_type, agent.agent_id))
        agent.set_fleet_type(fleet_type)
        #agent.set_fleetmanager(fleetmanager)
        agent.set_route_host(route_host)
        agent.set_boundingbox(bbox)

        if autonomy:
            agent.set_autonomy(autonomy, current_autonomy)

        agent.set_initial_position(position)

        agent.set_service_type(service_name)
        if speed:
            agent.set_speed(speed)

        return agent


class CustomerFactory(Factory):
    @classmethod
    def create_agent(cls,
                     domain,
                     name,
                     password,
                     class_,
                     default_strategy,
                     optional=None,
                     strategy=None,
                     jid_directory=None,
                     bbox=None,
                     fleetmanager=None,
                     fleet_type=None,
                     route_host=None,
                     autonomy=None,
                     current_autonomy=None,
                     position=None,
                     speed=None,
                     target=None,
                     service_name=None,
                     power=None,
                     slots=None,
                    ):
        """
                                Create a customer agent.

                                Args:
                                    domain (str): name of domain xmpp
                                    name (str): name of the agent
                                    password (str): password of the agent
                                    default_strategy (class): default strategy class of the agent
                                    strategy (class, optional): strategy class of the agent
                                    jid_directory (JID): directory JID address
                                    fleet_type (str): type of he fleet to be or demand
                                    route_host (str): route host address
                                    position (list): initial coordinates of the agent
                                    target (list, optional): destination coordinates of the agent
                                """

        jid = f"{name}@{domain}"
        logger.debug("Creating Customer agent: {}".format(jid))
        #agent = CustomerAgent(jid, password)  # Crea el usuario y la conexión con el XMPP
        #agent = PedestrianAgent(jid, password)

        if type(class_) is str:   # Añadimos el objeto de la clase cargada a la variable agente_class
            agent_class = load_class(class_)
            agent = agent_class(jid, password)
        else:
            raise Exception ("The agent needs a class in path format.")

        agent.set_id(name)  # Establece el identificador del agente
        agent.set_directory(jid_directory)

        if type(strategy) is str:   # Añadimos el objeto de la clase cargada a la variable strategy
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = default_strategy

        logger.debug("Assigning fleet type {} to customer {}".format(fleet_type, name))
        agent.set_fleet_type(fleet_type)
        agent.set_route_host(route_host)
        agent.set_boundingbox(bbox)
        agent.set_position(position)
        agent.set_target_position(target)

        return agent


class StationFactory(Factory):
    @classmethod
    def create_agent(cls,
                    domain,
                    name,
                    password,
                    default_strategy,
                    class_=None,
                    optional=None,
                    strategy=None,
                    jid_directory=None,
                    bbox=None,
                    fleetmanager=None,
                    fleet_type=None,
                    route_host=None,
                    autonomy=None,
                    current_autonomy=None,
                    position=None,
                    speed=None,
                    target=None,
                    service_name = None,
                    power=None,
                    slots=None,
                    ):

        """
                Create a station agent.

                Args:
                    domain (str): name of domain xmpp
                    name (str): name of the agent
                    password (str): password of the agent
                    default_strategy (class): default strategy class of the agent
                    strategy (class, optional): strategy class of the agent
                    jid_directory (JID): directory JID address
                    position (list): initial coordinates of the agent
                    power (int): power of the station agent in kW
                    slots (int): destination coordinates of the agent
                """

        jid = f"{name}@{domain}"
        logger.debug("Creating Station agent: {}".format(jid))

        if type(class_) is str:   # Añadimos el objeto de la clase cargada a la variable agente_class
            agent_class = load_class(class_)
            agent = agent_class(jid, password)
        else:
            raise Exception ("The agent needs a class in path format.")

        #agent = StationAgent(jid, password)  # Crea el usuario y la conexión con el XMPP
        agent.set_id(name)  # Establece el identificador del agente
        agent.set_directory(jid_directory)

        #TEST 3
        if type(strategy) is str:   # Añadimos el objeto de la clase cargada a la variable strategy
            one_shot_behaviour = load_class(strategy)
        else:
            one_shot_behaviour = default_strategy

        #one_shot_behaviour = one_shot_behaviour(None, 0, power)

        agent.set_position(position)
        #agent.set_available_places(slots)
        agent.add_service(service_name, slots, one_shot_behaviour)
        agent.set_service_type(service_name)        #Testeo
        agent.set_power(power)                      #Testeo

        return agent

#New vehicle
class VehicleFactory(Factory):    #VehicleFactory
    @classmethod
    def create_agent(cls,
                    domain,
                    name,
                    password,
                    default_strategy,
                    class_=None,
                    optional=None,
                    strategy=None,
                    jid_directory=None,
                    bbox=None,
                    fleetmanager=None,
                    fleet_type=None,
                    route_host=None,
                    autonomy=None,
                    current_autonomy=None,
                    position=None,
                    speed=None,
                    target=None,
                    service_name = None,
                    power=None,
                    slots=None,
                    ):
        """
                                Create a vehicle agent.

                                Args:
                                    domain (str): name of domain xmpp
                                    name (str): name of the agent
                                    password (str): password of the agent
                                    default_strategy (class): default strategy class of the agent
                                    strategy (class, optional): strategy class of the agent
                                    jid_directory (JID): directory JID address
                                    fleetmanager (str): fleetmanager JID address
                                    fleet_type (str): type of fleet to be used
                                    route_host (str): route host address
                                    autonomy (str):
                                    current_autonomy (str):
                                    position (str):
                                    speed (str):
                                """
        jid = f"{name}@{domain}"
        logger.debug("Creating Vehicle agent: {}".format(jid))
        agent = VehicleAgent(jid, password)  # Crea el usuario y la conexión con el XMPP
        agent.set_id(name)  # Establece el identificador del agente
        agent.set_directory(jid_directory)

        if type(strategy) is str:   # Añadimos el objeto de la clase cargada a la variable strategy
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = default_strategy

        logger.debug("Assigning type {} to vehicle {}".format(fleet_type, agent.agent_id))
        agent.set_fleet_type(fleet_type)
        #agent.set_fleetmanager(fleetmanager)
        agent.set_route_host(route_host)
        agent.set_boundingbox(bbox)
        agent.set_target_position(target)

        #if autonomy:
        #    agent.set_autonomy(autonomy, current_autonomy)

        agent.set_initial_position(position)

        if speed:
            agent.set_speed(speed)

        return agent
