import json
import logging

import faker

from .customer import CustomerAgent
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
        self.customers = []
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

        for customer in self.scenario["customers"]:
            password = customer["password"] if "password" in customer else faker_factory.password()
            agent.create_agent(CustomerAgent,
                                     customer["name"], password,
                                     customer["position"],
                                     target=customer["dest"])
