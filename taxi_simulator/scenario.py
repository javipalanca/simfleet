import json
import logging

import faker

from .coordinator import CoordinatorAgent
from .passenger import PassengerAgent
from .taxi import TaxiAgent

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
        self.taxis = []
        self.passengers = []
        self.scenario = None
        with open(filename, 'r') as f:
            logger.info("Reading scenario {}".format(filename))
            self.scenario = json.load(f)

    def load(self, coordinator: CoordinatorAgent):
        logger.info("Loading scenario...")
        for taxi in self.scenario["taxis"]:
            password = taxi["password"] if "password" in taxi else faker_factory.password()
            speed = taxi["speed"] if "speed" in taxi else None
            coordinator.create_agent(TaxiAgent, taxi["name"], password, taxi["position"], speed=speed)

        for passenger in self.scenario["passengers"]:
            password = passenger["password"] if "password" in passenger else faker_factory.password()
            coordinator.create_agent(PassengerAgent,
                                     passenger["name"], password,
                                     passenger["position"],
                                     target=passenger["dest"])
