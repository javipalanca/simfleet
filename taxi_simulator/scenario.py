import json
import logging

import faker

from .passenger import PassengerAgent
from .transport import TransportAgent

logger = logging.getLogger()

faker_factory = faker.Factory.create()


class Scenario(object):
    """
    A scenario object reads a file with a JSON representation of a scenario and is used to create the participant agents.
    """

    def __init__(self, filename):
        """
        The Scenario constructor reads the JSON file and creates the defined agents found in that file.
        Args:
            filename (str): the name of the scenario file
        """
        self.transports = []
        self.passengers = []
        self.scenario = None
        with open(filename, 'r') as f:
            logger.info("Reading scenario {}".format(filename))
            self.scenario = json.load(f)

    def load(self, agent):
        logger.info("Loading scenario...")
        for transport in self.scenario["transports"]:
            password = transport["password"] if "password" in transport else faker_factory.password()
            speed = transport["speed"] if "speed" in transport else None
            agent.create_agent(TransportAgent, transport["name"], password, transport["position"], speed=speed)

        for passenger in self.scenario["passengers"]:
            password = passenger["password"] if "password" in passenger else faker_factory.password()
            agent.create_agent(PassengerAgent,
                                     passenger["name"], password,
                                     passenger["position"],
                                     target=passenger["dest"])
