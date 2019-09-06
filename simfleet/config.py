import json
import logging

logger = logging.getLogger()


class SimfleetConfig(object):
    """
    A scenario object reads a file with a JSON representation of a scenario and is used to create the participant agents.
    """

    def __init__(self, filename=None):
        """
        The SimfleetConfig constructor reads the JSON file and sets.
        Args:
            filename (str): the name of the scenario file
        """

        self.__config = dict()
        if filename:
            self.load_config(filename)

        self.simulation_name = self.__config.get("simulation_name", None)
        self.max_time = self.__config.get("max_time", None)
        self.verbose = self.__config.get("verbose", None)

        self.transport_strategy = self.__config.get("transport_strategy",
                                                    "simfleet.strategies.AcceptAlwaysStrategyBehaviour")
        self.customer_strategy = self.__config.get("customer_strategy",
                                                   "simfleet.strategies.AcceptFirstRequestTaxiBehaviour")
        self.fleetmanager_strategy = self.__config.get("fleetmanager_strategy",
                                                       "simfleet.strategies.DelegateRequestTaxiBehaviour")
        self.directory_strategy = self.__config.get("directory_strategy",
                                                    "simfleet.strategies.AlwaysAnswerStrategyBehaviour")
        self.station_strategy = self.__config.get("station_strategy", "simfleet.strategies.ManageChargeSpacesBehaviour")

        self.fleetmanager_name = self.__config.get("fleetmanager_name", "fleetmanager")
        self.fleetmanager_passwd = self.__config.get("fleetmanager_passwd", "fleetmanager_passwd")
        self.route_name = self.__config.get("route_name", "route")
        self.route_passwd = self.__config.get("route_passwd", "route_passwd")
        self.directory_name = self.__config.get("directory_name", "directory")
        self.directory_passwd = self.__config.get("directory_passwd", "directory_passwd")

        self.host = self.__config.get("host", "127.0.0.1")
        self.xmpp_port = self.__config.get("xmpp_port", 5222)
        self.http_port = self.__config.get("http_port", 9000)
        self.http_ip = self.__config.get("http_ip", "127.0.0.1")

    def load_config(self, filename):
        with open(filename, 'r') as f:
            logger.info("Reading config {}".format(filename))
            self.__config = json.load(f)

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

    def __getattribute__(self, item):
        if item in self.__config.keys():
            return self.__config[item]
        else:
            super().__getattribute__(item)
