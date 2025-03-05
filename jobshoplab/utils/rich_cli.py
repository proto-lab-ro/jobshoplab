import os
import pickle
import sys
import time
from functools import partial

import keyboard
from rich.columns import Columns
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from jobshoplab.types.state_types import (
    JobState,
    State,
    StateMachineResult,
)


def load_history_from_pickle(file_path: str) -> tuple[StateMachineResult, ...]:
    with open(file_path, "rb") as f:
        return pickle.load(f)


def render_action(state_result: StateMachineResult):
    text = Text(f"Actiontransitions done at time {state_result.state.time}\n")
    text.append("Transitons: \n", style="bold")
    for transition in state_result.action.transitions:
        text.append(str(transition) + "\n", style="bold")

    return text


# Function to render the table
def render_machine_table(state: State):
    table = Table(title=f"Production System Status (Time: {state.time})")
    table.add_column("Machine", justify="center", style="cyan")
    table.add_column("State", justify="center", style="magenta")
    table.add_column("Due", justify="center", style="magenta")
    table.add_column("Mb-id", justify="center", style="green")
    table.add_column("Mb.store", justify="center", style="green")
    table.add_column("in-id", justify="center", style="green")
    table.add_column("in.store", justify="center", style="green")
    table.add_column("out-id", justify="center", style="green")
    table.add_column("out.store", justify="center", style="green")

    for machine in state.machines:  # Fix: Use attribute access
        table.add_row(
            machine.id,
            machine.state.name,
            str(machine.occupied_till.time),
            machine.buffer.id,
            str(machine.buffer.store),
            machine.prebuffer.id,
            str(machine.prebuffer.store),
            machine.postbuffer.id,
            str(machine.postbuffer.store),
        )

    return table


# Function to render transport table
def render_transport_table(state: State):
    table = Table(title="Transport Status")
    table.add_column("Transport", justify="center", style="blue")
    table.add_column("State", justify="center", style="red")
    table.add_column("Due", justify="center", style="red")
    table.add_column("Location", justify="center", style="cyan")
    table.add_column("Buffer-id", justify="center", style="cyan")
    table.add_column("store", justify="center", style="cyan")

    for transport in state.transports:
        table.add_row(
            transport.id,
            transport.state.name,
            str(transport.occupied_till.time),
            str(transport.location.location),
            transport.buffer.id,
            str(transport.buffer.store),
        )

    return table


def render_job_table(job: JobState):
    table = Table(title=f"Job Status {job.id} at {job.location}")
    table.add_column("Op id", justify="center", style="cyan")
    table.add_column("Start", justify="center", style="cyan")
    table.add_column("Stop", justify="center", style="cyan")
    table.add_column("Machine", justify="center", style="cyan")
    table.add_column("State", justify="center", style="cyan")

    for op in job.operations:
        table.add_row(
            op.id,
            str(op.start_time.time),
            str(op.end_time.time),
            op.machine_id,
            op.operation_state_state.name,
        )

    return table


def render_possilbe_transitions(state_machine_result: StateMachineResult):
    table = Table(title="Possible Transitions")
    table.add_column("component_id", justify="center", style="cyan")
    table.add_column("new_state", justify="center", style="cyan")
    table.add_column("job_id", justify="center", style="cyan")

    for transition in state_machine_result.possible_transitions:
        table.add_row(
            transition.component_id,
            str(transition.new_state),
            transition.job_id,
        )

    return table


def render_machine_with_buffers(machine_state):
    """Render a machine with its pre-buffer and post-buffer in a single row."""

    # Pre Buffer Table
    pre_buf = Table(title=f"{machine_state.prebuffer.id}")
    pre_buf.add_column("Store", justify="center", style="cyan")
    pre_buf.add_row(str(machine_state.prebuffer.store))

    # Machine Table
    machine = Table(title=f"Machine {machine_state.id}")
    machine.add_column("State", justify="center", style="green")
    machine.add_column("Store", justify="center", style="yellow")
    machine.add_column("Occupied Till", justify="center", style="red")

    machine.add_row(
        machine_state.state.name,
        str(machine_state.buffer.store),
        str(machine_state.occupied_till.time),
    )

    # Post Buffer Table
    post_buf = Table(title=f"{machine_state.postbuffer.id}")
    post_buf.add_column("Store", justify="center", style="cyan")
    post_buf.add_row(str(machine_state.postbuffer.store))

    # Return a row of three tables
    return Columns([pre_buf, machine, post_buf], expand=False)


def render_standalone_buffers(state_machine_result: StateMachineResult):
    """Render Buffer Overview."""
    buffer_table = Table(title=f"Standalone Buffer Overview")
    buffer_table.add_column("Buffer", justify="center", style="cyan")
    buffer_table.add_column("Store", justify="center", style="cyan")
    for buffer in state_machine_result.state.buffers:
        buffer_table.add_row(buffer.id, str(buffer.store))
    return buffer_table


def render_shopfloor_overview(state_machine_result):
    """Render all machines compactly."""
    standalone_buffer = render_standalone_buffers(state_machine_result)
    machines = [render_machine_with_buffers(m) for m in state_machine_result.state.machines]

    shopfloor = Group(*[standalone_buffer, *machines])

    return Panel(shopfloor, title="Shopfloor Overview", expand=False)


# Function to render both tables
def render_table(state_result: StateMachineResult):
    action = render_action(state_result)
    machines_table = render_machine_table(state_result.state)
    transports_table = render_transport_table(state_result.state)

    jobs_column = Columns([], equal=True)
    for job in state_result.state.jobs:
        jobs_column.add_renderable(render_job_table(job))

    machine_transport_columns = Columns([machines_table, transports_table], equal=True)

    # Wrap both tables inside a single Panel to prevent flickering
    return Panel(
        Group(action, machine_transport_columns, jobs_column),
        title="Production System Overview",
        border_style="blue",
    )


def render_from_file(file_path: str):
    history: tuple[StateMachineResult, ...] = load_history_from_pickle(file_path)
    render(history, None)


def render(
    history: tuple[StateMachineResult, ...],
    *args,
    **kwargs,
):

    # Playback Controls
    index = 0  # Track current position
    paused = True  # Playback state
    """Render the history of the simulation."""
    if not history:
        print("No history data found.")
    else:
        with Live(render_table(history[index]), auto_refresh=False) as live:
            update = partial(live.update, refresh=True)
            while True:
                # time.sleep(0.1)  # Debounce
                if not paused:
                    time.sleep(1)
                    index = min(index + 1, len(history) - 1)  # Move forward automatically
                    update(render_table(history[index]))

                # Key controls
                if keyboard.is_pressed("space"):  # Pause/Resume
                    paused = not paused
                    time.sleep(1)  # Debounce

                if keyboard.is_pressed("right"):  # Forward
                    index = min(index + 1, len(history) - 1)
                    update(render_table(history[index]))
                    time.sleep(0.3)

                if keyboard.is_pressed("left"):  # Backward
                    index = max(index - 1, 0)
                    update(render_table(history[index]))
                    time.sleep(0.3)

                if keyboard.is_pressed("q"):  # Quit
                    print("Quitting...")
                    break

                # Key controls
                if keyboard.is_pressed("space"):  # Pause/Resume
                    paused = not paused
                    time.sleep(1)  # Debounce

                if keyboard.is_pressed("right"):  # Forward
                    index = min(index + 1, len(history) - 1)
                    live.update(render_table(history[index]))
                    time.sleep(0.3)

                if keyboard.is_pressed("left"):  # Backward
                    index = max(index - 1, 0)
                    live.update(render_table(history[index]))
                    time.sleep(0.3)

                if keyboard.is_pressed("q"):  # Quit
                    print("Quitting...")
                    break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Please provide the file path as an argument.")
        sys.exit(1)

    file_path = sys.argv[1]

    # Resolve to an absolute path
    file_path = os.path.abspath(file_path)

    # Validate file existence
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        sys.exit(1)

    if not os.path.isfile(file_path):
        print(f"Error: '{file_path}' is not a valid file.")
        sys.exit(1)

    try:
        render_from_file(file_path)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
