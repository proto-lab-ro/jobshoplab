import os
import pickle
import sys

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import DataTable, Footer, Header, Static

from jobshoplab.types.state_types import StateMachineResult


def load_history_from_pickle(file_path: str) -> tuple[StateMachineResult, ...]:
    with open(file_path, "rb") as f:
        return pickle.load(f)


class ProductionApp(App):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.history = load_history_from_pickle(file_path)
        self.index = 0
        self.len = 0
        self.paused = True
        self.input_mode = False
        self.input_buffer = ""  # Store user input

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Production System Overview", id="title"),
            Static(id="status"),
            Static("", id="input_display"),  # <-- New input display
            DataTable(id="machine_table"),
            DataTable(id="transport_table"),
            DataTable(id="job_table"),
        )
        yield Footer()

    def on_mount(self) -> None:
        if not self.history:
            self.exit("No history data found.")

        self.len = len(self.history) - 1
        self.update_tables()
        self.set_interval(1, self.auto_update)

    def update_tables(self):
        state = self.history[self.index].state

        # Update status
        status_widget = self.query_one("#status", Static)
        if self.index >= self.len:
            next_op = "End of Simulation"
        else:
            next_op = self.history[self.index + 1].action
        status_widget.update(
            f"Index: {self.index} from {self.len}, Env Time: {state.time.time}\nNext Operation: {next_op}"
        )

        # Update input display
        input_widget = self.query_one("#input_display", Static)
        input_widget.update(f":{self.input_buffer}" if self.input_mode else "")  # <-- Show input

        machine_table = self.query_one("#machine_table", DataTable)
        machine_table.clear(columns=True)
        machine_table.add_columns("Machine", "State", "Due", "Mb-id", "Mb.store")
        for machine in state.machines:
            machine_table.add_row(
                machine.id,
                machine.state.name,
                str(machine.occupied_till.time),
                machine.buffer.id,
                str(machine.buffer.store),
            )

        transport_table = self.query_one("#transport_table", DataTable)
        transport_table.clear(columns=True)
        transport_table.add_columns("Transport", "State", "Due", "Location")
        for transport in state.transports:
            transport_table.add_row(
                transport.id,
                transport.state.name,
                str(transport.occupied_till.time),
                str(transport.location.location),
            )

        job_table = self.query_one("#job_table", DataTable)
        job_table.clear(columns=True)
        job_table.add_columns("Job ID", "Op ID", "Start", "Stop", "Machine")
        for job in state.jobs:
            for op in job.operations:
                job_table.add_row(
                    job.id, op.id, str(op.start_time.time), str(op.end_time.time), op.machine_id
                )

    def auto_update(self):
        if not self.paused:
            self.index = min(self.index + 1, len(self.history) - 1)
            self.update_tables()

    def on_key(self, event) -> None:
        if self.input_mode:
            if event.key.isdigit():
                self.input_buffer += event.key
                self.update_tables()  # <-- Update display while typing
            elif event.key == "backspace":
                self.input_buffer = self.input_buffer[:-1]
                self.update_tables()
            elif event.key == "enter":
                if self.input_buffer.isdigit():
                    self.jump_to_index(int(self.input_buffer))
                self.input_mode = False
                self.input_buffer = ""
                self.update_tables()
            elif event.key == "escape":
                self.input_mode = False
                self.input_buffer = ""
                self.update_tables()
        else:
            if event.key == "space":
                self.paused = not self.paused
            elif event.key == "right":
                self.index = min(self.index + 1, len(self.history) - 1)
                self.update_tables()
            elif event.key == "left":
                self.index = max(self.index - 1, 0)
                self.update_tables()
            elif event.key == "q":
                self.exit("Quitting...")
            elif event.key == "i":
                self.input_mode = True
                self.input_buffer = ""
                self.update_tables()  # <-- Show input mode immediately

    def jump_to_index(self, index: int) -> None:
        if 0 <= index < len(self.history):
            self.index = index
            self.update_tables()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Please provide the file path as an argument.")
        sys.exit(1)

    file_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        print(f"Error: The file '{file_path}' does not exist or is not valid.")
        sys.exit(1)

    ProductionApp(file_path).run()
