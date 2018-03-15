import logging


class State:
    def __init__(self, name):
        self.name = name
        self.fsm = None
        self.behav = None
        self.helpers = None
        self.logger = None

    def setup(self, fsm, behav):
        self.fsm = fsm
        self.behav = behav
        self.helpers = self.behav
        self.logger = logging.getLogger("{} {} ({})".format(self.behav.myAgent.__class__.__name__,
                                                            self.name,
                                                            self.behav.myAgent.agent_id))

    def transition_to(self, name):
        return self.fsm.get_state(name)

    def receive(self, timeout=10):
        return self.behav.receive(timeout=timeout)

    def send(self, message):
        self.behav.send(message)

    def run(self):
        raise NotImplementedError

    def is_final(self):
        return False

    def __str__(self):
        return self.name


class FinalState(State):
    def run(self):
        raise NotImplementedError

    def is_final(self):
        return True


class StateMachine:
    def __init__(self, behav):
        self.behav = behav
        self.current_state = None
        self.__states = {}
        self.logger = logging.getLogger("{} ({})".format(self.behav.myAgent.__class__.__name__,
                                                         self.behav.myAgent.agent_id))

        self.setup()

    def register_state(self, state):
        self.__states[state.name] = state
        self.__states[state.name].setup(self, self.behav)
        self.logger.debug("State {} registered".format(state))

    def get_state(self, name):
        return self.__states[name]

    def set_initial_state(self, initial_state_name):
        self.current_state = self.get_state(initial_state_name)
        self.behav.myAgent.status = self.current_state.name
        self.logger.debug("Initial State {}".format(initial_state_name))

    def setup(self):
        pass

    def step(self):
        self.logger.debug("Running state {}".format(self.current_state))
        try:
            next_state = self.current_state.run()
            if next_state:
                self.current_state = next_state
                self.behav.myAgent.status = self.current_state.name
        except Exception as e:
            self.logger.error("Exception running state {}: {}".format(self.current_state, e))
        else:
            self.logger.debug("Transitioning to state {}".format(self.current_state))

    def is_finished(self):
        return self.current_state.is_final()
