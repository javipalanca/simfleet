from loguru import logger
from abc import ABC, abstractmethod

from simfleet.common.agents.directory import DirectoryAgent
from simfleet.common.agents.fleetmanager import FleetManagerAgent
from simfleet.common.lib.vehicles.models.vehicle import VehicleAgent

from simfleet.utils.reflection import load_class


class Factory(ABC):
    """
        Abstract factory class for creating agents. All agent factories must inherit from this class
        and implement the create_agent method.

    """
    @classmethod
    @abstractmethod
    def create_agent(cls,
                     domain,
                     name,
                     password,
                     class_,
                     default_strategy,
                     simulatorjid,
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
                     services,
                     capacity,
                     line,
                     lines
                     ):
        """
                Abstract method that must be implemented by all subclasses to create a specific agent.
        """

        raise NotImplementedError


class DirectoryFactory(Factory):
    """
        Factory class for creating DirectoryAgent instances.

    """
    @classmethod
    def create_agent(cls,
                     domain,
                     name,
                     password,
                     default_strategy,
                     simulatorjid=None,
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
                     services=None,
                     capacity=None,
                     line=None,
                     lines=None
                     ):
        """
                        Create a directory agent.

                        Args:
                            domain(str): domain of the agent
                            name (str): name of the agent
                            password (str): password of the agent
                            default_strategy (class, optional): strategy class of the agent

                        Returns:
                        DirectoryAgent: An instance of DirectoryAgent
                        """
        jid = f"{name}@{domain}"
        logger.debug("Creating Directory agent: {}".format(jid))
        agent = DirectoryAgent(jid, password)
        agent.set_id(name)
        agent.strategy = default_strategy
        return agent


class FleetManagerFactory(Factory):
    """
        Factory class for creating FleetManagerAgent instances.

        """
    @classmethod
    def create_agent(cls,
                     domain,
                     name,
                     password,
                     default_strategy,
                     simulatorjid=None,
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
                     services=None,
                     capacity=None,
                     line=None,
                     lines=None
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

                        Returns:
                        FleetManagerAgent: An instance of FleetManagerAgent.
                        """
        jid = f"{name}@{domain}"
        logger.debug("Creating FleetManager agent: {}".format(jid))
        agent = FleetManagerAgent(jid, password)
        agent.set_id(name)
        agent.set_directory(jid_directory)

        # Load strategy if provided
        if type(strategy) is str:
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = default_strategy

        logger.debug("Assigning type {} to fleetmanager {}".format(fleet_type, agent.agent_id))
        agent.set_fleet_type(fleet_type)
        return agent


class TransportFactory(Factory):
    """
        Factory class for creating transport-related agent instances.

        """
    @classmethod
    def create_agent(cls,
                     domain,
                     name,
                     password,
                     class_,
                     default_strategy,
                     simulatorjid=None,
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
                     services=None,
                     capacity=None,
                     line=None,
                     lines=None
                    ):
        """
        Create a Transport agent.

        Args:
            domain (str): XMPP domain name.
            name (str): Agent name.
            password (str): Password for the agent.
            class_ (str): Class name for the agent in path format.
            default_strategy (class): Default strategy class for the agent.
            strategy (class, optional): Optional specific strategy class.
            jid_directory (JID): Directory JID address.
            fleetmanager (str): Fleet manager JID address.
            fleet_type (str): Type of fleet used by the agent.
            route_host (str): Route host address.
            autonomy (str): Autonomy level of the agent.
            current_autonomy (str): Current autonomy level.
            position (list): Initial coordinates of the agent.
            speed (str): Speed of the agent.
            services (list): List of services the agent provides.
            capacity (int): Capacity of the agent.
            line (str, optional): Bus line assigned to the agent.
            lines (dict, optional): Dictionary containing line details.

        Returns:
            TransportAgent: An instance of the specified transport agent class.
                                """

        jid = f"{name}@{domain}"
        logger.debug("Creating Transport agent: {}".format(jid))

        # Load and instantiate agent class
        if type(class_) is str:
            agent_class = load_class(class_)
            if optional:
                agent = agent_class(jid, password, **optional)
            else:
                agent = agent_class(jid, password)
        else:
            raise Exception ("The agent needs a class in path format.")

        agent.set_id(name)
        agent.set_directory(jid_directory)

        # Load strategy if provided
        if type(strategy) is str:
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = default_strategy

        # Set fleet type, route host, and additional attributes
        agent.set_fleet_type(fleet_type)
        agent.set_route_host(route_host)
        agent.set_boundingbox(bbox)

        if autonomy:
            agent.set_autonomy(autonomy, current_autonomy)

        if services:
            agent.set_service_type(services)

        # Bus line management
        if line:
            agent.set_line(line)
            stop_list = lines.get(line).get("stop_list")
            line_type = lines.get(line).get("line_type")
            agent.set_stop_list(stop_list)
            agent.set_line_type(line_type)
            agent.set_initial_position(stop_list[0])

        # Additional attributes
        agent.set_initial_position(position)

        if capacity:
            agent.set_capacity(capacity)

        if speed:
            agent.set_speed(speed)

        return agent


class CustomerFactory(Factory):
    """
        Factory class for creating CustomerAgent instances.
    """
    @classmethod
    def create_agent(cls,
                     domain,
                     name,
                     password,
                     class_,
                     default_strategy,
                     simulatorjid=None,
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
                     services=None,
                     capacity=None,
                     line=None,
                     lines=None
                    ):
        """
        Create a Customer agent.

        Args:
            domain (str): XMPP domain name.
            name (str): Agent name.
            password (str): Password for the agent.
            class_ (str): Class name for the agent in path format.
            default_strategy (class): Default strategy class for the agent.
            strategy (class, optional): Optional specific strategy class.
            jid_directory (JID): Directory JID address.
            fleet_type (str): Type of fleet used by the agent.
            route_host (str): Route host address.
            position (list): Initial coordinates of the agent.
            target (list, optional): Destination coordinates of the agent.

        Returns:
            CustomerAgent: An instance of the specified customer agent class.
        """

        jid = f"{name}@{domain}"
        logger.debug("Creating Customer agent: {}".format(jid))

        # Load and instantiate agent class
        if type(class_) is str:
            agent_class = load_class(class_)
            agent = agent_class(jid, password)
        else:
            raise Exception ("The agent needs a class in path format.")

        agent.set_id(name)
        agent.set_directory(jid_directory)

        # Load strategy if provided
        if type(strategy) is str:
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = default_strategy

        if line:
            agent.set_line(line)

        # Set fleet type, route host, and additional attributes
        agent.set_fleet_type(fleet_type)
        agent.set_route_host(route_host)
        agent.set_boundingbox(bbox)

        agent.set_initial_position(position)

        agent.set_target_position(target)

        if speed:
            agent.set_speed(speed)

        return agent


class StationFactory(Factory):
    """
        Factory class for creating StationAgent instances.

        """
    @classmethod
    def create_agent(cls,
                    domain,
                    name,
                    password,
                    default_strategy,
                    simulatorjid=None,
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
                    services=None,
                    capacity=None,
                    line=None,
                    lines=None
                    ):

        """
        Create a Station agent.

        Args:
            domain (str): XMPP domain name.
            name (str): Agent name.
            password (str): Password for the agent.
            class_ (str): Class name for the agent in path format.
            default_strategy (class): Default strategy class for the agent.
            strategy (class, optional): Optional specific strategy class.
            jid_directory (JID): Directory JID address.
            position (list): Initial coordinates of the agent.
            services (list): List of services provided by the station.
            capacity (int): Capacity of the station (e.g., slots available for vehicles).

        Returns:
            StationAgent: An instance of StationAgent.
        """

        jid = f"{name}@{domain}"
        logger.debug("Creating Station agent: {}".format(jid))

        # Load and instantiate agent class
        if type(class_) is str:
            agent_class = load_class(class_)
            agent = agent_class(jid, password)
        else:
            raise Exception ("The agent needs a class in path format.")

        agent.set_id(name)
        agent.set_directory(jid_directory)

        # Set route host, and additional attributes
        agent.set_route_host(route_host)
        agent.set_boundingbox(bbox)
        agent.set_position(position)

        if simulatorjid:
            agent.set_simulatorjid(simulatorjid)

        # Station service management
        for service in services:
            type_ = service["type"]
            behaviour = service["behaviour"]
            slots = service["slots"]
            args = service["args"]

            if type(behaviour) is str:
                one_shot_behaviour = load_class(behaviour)
            else:
                one_shot_behaviour = default_strategy
            agent.add_service(type_, slots, one_shot_behaviour, **args)

        return agent

class TransportStopFactory(Factory):
    """
        Factory class for creating TransportStopAgent instances.

        """
    @classmethod
    def create_agent(cls,
                    domain,
                    name,
                    password,
                    default_strategy=None,
                    simulatorjid=None,
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
                    services=None,
                    capacity=None,
                    line=None,
                    lines=None
                    ):

        """
        Create a Transport Stop agent.

        Args:
            domain (str): XMPP domain name.
            name (str): List containing agent ID and stop name.
            password (str): Password for the agent.
            default_strategy (class): Default strategy class for the agent.
            strategy (class, optional): Optional specific strategy class.
            jid_directory (JID): Directory JID address.
            position (list): Initial coordinates of the transport stop.
            lines (list): List of lines served by the transport stop.

        Returns:
            TransportStopAgent: An instance of TransportStopAgent.
        """

        jid = f"{name[0]}@{domain}"
        logger.debug("Creating Station agent: {}".format(jid))

        # Load and instantiate agent class
        if type(class_) is str:
            agent_class = load_class(class_)
            agent = agent_class(jid, password)
        else:
            raise Exception ("The agent needs a class in path format.")

        agent.set_id(name[0])
        agent.set_name(name[1])
        agent.set_directory(jid_directory)

        # Load strategy if provided
        if type(strategy) is str:
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = default_strategy

        # Set route host, and additional attributes
        agent.set_route_host(route_host)
        agent.set_boundingbox(bbox)
        agent.set_position(position)

        if simulatorjid:
            agent.set_simulatorjid(simulatorjid)

        for line in lines:
            agent.add_queue(line)

        return agent

class VehicleFactory(Factory):
    """
        Factory class for creating VehicleAgent instances.

        """
    @classmethod
    def create_agent(cls,
                    domain,
                    name,
                    password,
                    default_strategy,
                    simulatorjid=None,
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
                    services = None,
                    capacity=None,
                    line=None,
                    lines=None
                    ):
        """
        Create a Vehicle agent.

        Args:
            domain (str): XMPP domain name.
            name (str): Agent name.
            password (str): Password for the agent.
            default_strategy (class): Default strategy class for the agent.
            strategy (class, optional): Optional specific strategy class.
            jid_directory (JID): Directory JID address.
            fleet_type (str): Type of fleet used by the vehicle.
            route_host (str): Route host address.
            position (list): Initial coordinates of the vehicle.
            speed (str): Speed of the vehicle.
            target (list, optional): Target coordinates for the vehicle.

        Returns:
            VehicleAgent: An instance of VehicleAgent.
        """
        jid = f"{name}@{domain}"
        logger.debug("Creating Vehicle agent: {}".format(jid))
        agent = VehicleAgent(jid, password)
        agent.set_id(name)
        agent.set_directory(jid_directory)

        # Load strategy if provided
        if type(strategy) is str:
            agent.strategy = load_class(strategy)
        else:
            agent.strategy = default_strategy

        # Set route host, and additional attributes
        agent.set_fleet_type(fleet_type)
        agent.set_route_host(route_host)
        agent.set_boundingbox(bbox)
        agent.set_target_position(target)

        agent.set_initial_position(position)

        if speed:
            agent.set_speed(speed)

        return agent
