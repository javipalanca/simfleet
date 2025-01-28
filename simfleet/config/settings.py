import json
from loguru import logger

from simfleet.utils.reflection import load_class
from simfleet.utils.helpers import get_bbox_from_location

def hide_passwords(item, key=None):
    if isinstance(item, dict):
        d = dict()
        for newk, newv in item.items():
            d[newk] = hide_passwords(newv, newk)
    elif isinstance(item, list):
        d = list()
        for i in item:
            d.append(hide_passwords(i))
    else:
        d = "*" * len(item) if isinstance(key, str) and "password" in key else item
    return d


class SimfleetConfig(object):
    """
    A scenario object reads a file with a JSON representation of a scenario and is used to create the participant agents.
    """

    def __init__(self, filename=None, name=None, max_time=None, verbose=None):
        """
        The SimfleetConfig constructor reads the JSON file and sets.
        Args:
            filename (str): the name of the scenario file
        """

        self.__config = dict()

        self.__config["fleets"] = []
        self.__config["transports"] = []
        self.__config["customers"] = []
        self.__config["stations"] = []
        self.__config["vehicles"] = []  # New vehicle
        # Bus line
        self.__config["stops"] = []
        self.__config["lines"] = []

        if filename:
            self.load_config(filename)

        self.__config["simulation_name"] = self.__config.get("simulation_name", name)
        self.__config["max_time"] = self.__config.get("max_time", max_time)
        self.__config["verbose"] = self.__config.get("verbose", verbose)
        self.__config["simulation_password"] = self.__config.get("simulation_password", "secret")

        #New coords
        if self.__config.get("coords"):
            if self.__config.get("zoom"):
                input_location = get_bbox_from_location(self.__config["coords"], self.__config["zoom"])
                logger.debug(
                    "BoundingBox for {} is {}".format(self.__config["coords"], input_location[1])
                )
                self.__config["coords"] = input_location
            else:
                logger.debug("Default value 12 for Zoom variable")
                input_location = get_bbox_from_location(self.__config["coords"], 12)
                self.__config["zoom"] = 12
                self.__config["coords"] = input_location
        else:
            #raise Exception("Could not find coordinates for the entered location")
            logger.debug(
                "Could not find coordinates for the entered location. Default coordinates: Valencia, ES"
            )
            default_location = get_bbox_from_location("Valencia, ES", 11.75)
            self.__config["zoom"] = self.__config.get("zoom", 11.75)
            self.__config["coords"] = default_location

        #self.__config["coords"] = self.__config.get("coords", [39.47, -0.37])
        #self.__config["zoom"] = self.__config.get("zoom", 12)

        self.__config["transport_strategy"] = self.__config.get(
            "transport_strategy", "simfleet.common.lib.transports.strategies.taxi.FSMTaxiBehaviour"
        )
        self.__config["customer_strategy"] = self.__config.get(
            "customer_strategy", "simfleet.common.lib.customers.strategies.taxicustomer.AcceptFirstRequestBehaviour"
        )
        self.__config["fleetmanager_strategy"] = self.__config.get(
            "fleetmanager_strategy", "simfleet.common.lib.fleet.strategies.fleetmanager.DelegateRequestBehaviour"
        )
        self.__config["directory_strategy"] = self.__config.get(
            "directory_strategy", "simfleet.common.agents.directory.DirectoryStrategyBehaviour"
        )
        self.__config["station_strategy"] = self.__config.get(
            "station_strategy", "simfleet.common.lib.stations.models.chargingstation.ChargingService"
        )
        #New vehicle
        self.__config["vehicle_strategy"] = self.__config.get(
            "vehicle_strategy", "simfleet.common.lib.vehicles.strategies.vehicle.FSMOneShotVehicleBehaviour"
        )
        # New statistics
        self.__config["mobility_metrics"] = self.__config.get(          #Metric - Renombrar
            "mobility_metrics", "simfleet.metrics.lib.mobilitystatistics.MobilityStatisticsClass"
        )

        # Bus line
        #self.__config["bus_stop_strategy"] = self.__config.get(
        #    "bus_stop_strategy", "simfleet.common.lib.stations.models.busstop.BusStopStrategyBehaviour")

        self.__config["fleetmanager_name"] = self.__config.get(
            "fleetmanager_name", "fleetmanager"
        )
        self.__config["fleetmanager_password"] = self.__config.get(
            "fleetmanager_passwd", "fleetmanager_passwd"
        )
        self.__config["route_host"] = self.__config.get(
            #"route_host", "http://router.project-osrm.org/"
            "route_host", "http://osrm.gti-ia.upv.es/"
        )
        self.__config["route_name"] = self.__config.get("route_name", "route")
        self.__config["route_password"] = self.__config.get(
            "route_passwd", "route_passwd"
        )
        self.__config["directory_name"] = self.__config.get(
            "directory_name", "directory"
        )
        self.__config["directory_password"] = self.__config.get(
            "directory_passwd", "directory_passwd"
        )

        self.__config["host"] = self.__config.get("host", "127.0.0.1")
        self.__config["xmpp_port"] = self.__config.get("xmpp_port", 5222)
        self.__config["http_port"] = self.__config.get("http_port", 9000)
        self.__config["http_ip"] = self.__config.get("http_ip", "127.0.0.1")

        logger.debug("Config loaded: {}".format(self))

    def load_config(self, filename):
        with open(filename, "r") as f:
            logger.info("Reading config {}".format(filename))
            self.__config.update(json.load(f))

    @property
    def num_managers(self):
        try:
            return len(self.__config["fleets"])
        except KeyError:
            return 0

    @property
    def num_transport(self):
        try:
            return len(self.__config["transports"])
        except KeyError:
            return 0

    @property
    def num_customers(self):
        try:
            return len(self.__config["customers"])
        except KeyError:
            return 0

    @property
    def num_stations(self):
        try:
            return len(self.__config["stations"])
        except KeyError:
            return 0

    #New vehicle
    @property
    def num_vehicles(self):
        try:
            return len(self.__config["vehicles"])
        except KeyError:
            return 0

    # Bus line
    @property
    def num_stops(self):
        try:
            return len(self.__config["stops"])
        except KeyError:
            return 0

    @property
    def num_lines(self):
        try:
            return len(self.__config["lines"])
        except KeyError:
            return 0

    def __getitem__(self, item):
        return self.__config[item]

    def __getattr__(self, item):
        if item != "__config" and item in self.__config:
            return self.__config[item]
        else:
            return super().__getattribute__(item)

    def __setattr__(self, key, value):
        if "__config" in self.__dict__ and key in self.__config:
            self.__config[key] = value
        else:
            super().__setattr__(key, value)

    def __str__(self):
        d = hide_passwords(self.__config)
        return json.dumps(d, indent=4)


def set_default_metrics(mobility_metrics):      #Renombrar
    class_dict = {}

    class_dict['mobility_metrics'] = load_class(mobility_metrics)     #Crear lista de metricas

    return class_dict

def set_default_strategies(
        directory_strategy,
        fleetmanager_strategy,
        transport_strategy,
        customer_strategy,
        station_strategy,
        vehicle_strategy,   #New vehicle
        #bus_stop_strategy,  #Bus line
):
    """
    Gets the strategy strings and loads their classes. This strategies are prepared to be injected into any
    new transport or customer agent.
    Args:
        directory_strategy (str): the path to the directory strategy
        fleetmanager_strategy (str): the path to the fleetmanager strategy
        transport_strategy (str): the path to the transport strategy
        customer_strategy (str): the path to the customer strategy
        station_strategy (str): the path to the station strategy
    """

    class_dict = {}

    class_dict['directory'] = load_class(directory_strategy)
    class_dict['fleetmanager'] = load_class(fleetmanager_strategy)
    class_dict['transport'] = load_class(transport_strategy)
    class_dict['customer'] = load_class(customer_strategy)
    class_dict['station'] = load_class(station_strategy)
    class_dict['vehicle'] = load_class(vehicle_strategy)  #New vehicle
    #class_dict['stop'] = load_class(bus_stop_strategy)  # Bus line

    logger.debug(
        "Loaded default strategy classes: {}, {}, {}, {} and {}".format(
            class_dict['directory'],
            class_dict['fleetmanager'],
            class_dict['transport'],
            class_dict['customer'],
            class_dict['station'],
            class_dict['vehicle'],  #New vehicle
            #class_dict['stop'],  # Bus line
        )
    )

    return class_dict
