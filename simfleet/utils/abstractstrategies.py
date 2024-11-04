from abc import ABCMeta
from loguru import logger
from spade.behaviour import CyclicBehaviour, FSMBehaviour


class StrategyBehaviour(CyclicBehaviour, metaclass=ABCMeta):
    """
    The base behaviour that all parent strategies must inherit from. It follows the Strategy Pattern
    and provides common event handling for the start and end of a strategy's lifecycle.
    """

    async def on_start(self) -> None:
        """
        Called when the behaviour is started. Emits an initial event for statistics.
        """
        self.agent.events_store.emit(
            event_type="initial_event",
            details={}
        )

    async def on_end(self) -> None:
        """
        Called when the behaviour ends. Emits a final event for statistics.
        """
        self.agent.events_store.emit(
            event_type="final_event",
            details={}
        )

    async def run(self) -> None:
        """
        The main behaviour logic that needs to be implemented by subclasses.
        """
        raise NotImplementedError


class FSMStrategyBehaviour(StrategyBehaviour, FSMBehaviour):
    """
    Combines the features of StrategyBehaviour and FSMBehaviour to allow FSM-based strategies
    to share common event handling for their lifecycle.
    """

    async def run(self) -> None:
        await super(FSMBehaviour, self).run()

    async def on_start(self) -> None:
        """
        Called when the FSM strategy is started. Ensures that the common start event is emitted.
        """
        #await super(StrategyBehaviour).on_start()

        # Alternative
        await super().on_start()

    async def on_end(self) -> None:
        """
        Called when the FSM strategy ends. Ensures that the common end event is emitted.
        """
        #await super(StrategyBehaviour).on_end()

        # Alternative
        await super().on_end()
