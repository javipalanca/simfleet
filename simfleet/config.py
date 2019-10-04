import json
from loguru import logger


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

        if filename:
            self.load_config(filename)

        self.__config["simulation_name"] = self.__config.get("simulation_name", name)
        self.__config["max_time"] = self.__config.get("max_time", max_time)
        self.__config["verbose"] = self.__config.get("verbose", verbose)

        self.__config["coords"] = self.__config.get("coords", [39.47, -0.37])
        self.__config["zoom"] = self.__config.get("zoom", 12)

        self.__config["transport_strategy"] = self.__config.get("transport_strategy",
                                                                "simfleet.strategies.AcceptAlwaysStrategyBehaviour")
        self.__config["customer_strategy"] = self.__config.get("customer_strategy",
                                                               "simfleet.strategies.AcceptFirstRequestBehaviour")
        self.__config["fleetmanager_strategy"] = self.__config.get("fleetmanager_strategy",
                                                                   "simfleet.strategies.DelegateRequestBehaviour")
        self.__config["directory_strategy"] = self.__config.get("directory_strategy",
                                                                "simfleet.directory.DirectoryStrategyBehaviour")
        self.__config["station_strategy"] = self.__config.get("station_strategy",
                                                              "simfleet.station.StationStrategyBehaviour")

        self.__config["fleetmanager_name"] = self.__config.get("fleetmanager_name", "fleetmanager")
        self.__config["fleetmanager_password"] = self.__config.get("fleetmanager_passwd", "fleetmanager_passwd")
        self.__config["route_name"] = self.__config.get("route_name", "route")
        self.__config["route_password"] = self.__config.get("route_passwd", "route_passwd")
        self.__config["directory_name"] = self.__config.get("directory_name", "directory")
        self.__config["directory_password"] = self.__config.get("directory_passwd", "directory_passwd")

        self.__config["host"] = self.__config.get("host", "127.0.0.1")
        self.__config["xmpp_port"] = self.__config.get("xmpp_port", 5222)
        self.__config["http_port"] = self.__config.get("http_port", 9000)
        self.__config["http_ip"] = self.__config.get("http_ip", "127.0.0.1")

        logger.debug("Config loaded: {}".format(self))

    def load_config(self, filename):
        with open(filename, 'r') as f:
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

    def __getitem__(self, item):
        return self.__config[item]

    def __getattr__(self, item):
        if item != "__config" and item in self.__config.keys():
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
