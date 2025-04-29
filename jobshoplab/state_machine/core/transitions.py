from jobshoplab.utils.exceptions import NotImplementedError


class StateEnum:
    IDLE = "Idle"
    RUNNING = "running"
    OUTAGE = "outage"
    FULL = "full"
    EMPTY = "empty"
    SETUP = "setup"


class Transition:
    def __init__(self, state, transitions):
        self.states = state
        self.transitions = transitions

    def _match_state(self, state):
        match state.value.lower():
            case "idle":
                return StateEnum.IDLE
            case "setup":
                return StateEnum.SETUP
            case "running" | "working" | "pickup" | "transit" | "waitingpickup":
                return StateEnum.RUNNING
            case "outage" | "maintenance":
                return StateEnum.OUTAGE
            case _:
                raise NotImplementedError()

    def is_valid_transition(self, state, new_state):
        if state == new_state:
            return False
        _state = self._match_state(state)
        _new_state = self._match_state(new_state)
        return _new_state in self.transitions[_state]


class BufferTransition(Transition):
    def __init__(self):
        states = [StateEnum.IDLE, StateEnum.EMPTY, StateEnum.FULL, StateEnum.OUTAGE]
        transitions = {
            StateEnum.IDLE: (StateEnum.EMPTY, StateEnum.FULL, StateEnum.OUTAGE),
            StateEnum.EMPTY: (StateEnum.IDLE, StateEnum.FULL, StateEnum.OUTAGE),
            StateEnum.FULL: (StateEnum.IDLE, StateEnum.EMPTY, StateEnum.OUTAGE),
            StateEnum.OUTAGE: (StateEnum.IDLE, StateEnum.EMPTY, StateEnum.FULL),
        }
        super().__init__(states, transitions)


class MachineTransition(Transition):
    def __init__(self):
        states = [StateEnum.IDLE, StateEnum.RUNNING, StateEnum.OUTAGE, StateEnum.SETUP]
        transitions = {
            StateEnum.IDLE: (StateEnum.SETUP,),
            StateEnum.SETUP: (StateEnum.RUNNING),
            StateEnum.RUNNING: (
                # StateEnum.IDLE,
                # No transitions from IDEL to OUTAGE, SETUP and RUNNING
                StateEnum.OUTAGE,
                # StateEnum.SETUP,
                StateEnum.RUNNING,
            ),
            StateEnum.OUTAGE: (StateEnum.IDLE),
        }

        super().__init__(states, transitions)


class TransportTransition(Transition):
    def __init__(self) -> None:
        states = [StateEnum.IDLE, StateEnum.RUNNING, StateEnum.OUTAGE]
        transitions = {
            StateEnum.IDLE: (StateEnum.RUNNING,),
            StateEnum.RUNNING: (StateEnum.OUTAGE, StateEnum.RUNNING),
            StateEnum.OUTAGE: (StateEnum.IDLE,),
        }

        super().__init__(states, transitions)
