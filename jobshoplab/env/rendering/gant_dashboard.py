import argparse
import pickle
import socket
import time
import uuid
from itertools import groupby
from pathlib import Path
from typing import Any, Dict, List, Tuple

import dash_daq as daq
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html
import dash_ag_grid as dag
from plotly import colors as plotly_colors

from jobshoplab.types.instance_config_types import InstanceConfig
from jobshoplab.types.state_types import (
    NoTime,
    OperationStateState,
    StateMachineResult,
    TransportStateState,
)
from jobshoplab.utils.exceptions import FileNotFound
from jobshoplab.utils.logger import get_logger


# -------------------------------------------------------------------
# Utility Classes
# -------------------------------------------------------------------


class DashboardUtils:
    @staticmethod
    def map_time(int_time: int, current_time: int) -> str:
        current_time += 1
        real_time = time.time()
        time_fct = real_time / current_time
        computed_time = int_time * time_fct
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(computed_time)))

    @staticmethod
    def is_port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) == 0

    @staticmethod
    def check_port(port: int) -> int:
        while DashboardUtils.is_port_in_use(port):
            port += 1
        return port

    @staticmethod
    def has_transports(data: Dict[str, Any]) -> bool:
        try:
            return any(
                item.get("duration", 0) > 0 for item in data.get("travel_times", {}).values()
            )
        except Exception:
            return False


class DashboardDataMapper:
    @staticmethod
    def map_key_to_sort(key: str) -> int:
        if key.startswith("j"):
            return int(key[2:])
        if key.startswith("m"):
            return int(key[2:])
        if key.startswith("t"):
            return int(key[2:]) + 1000
        if key.startswith("b"):
            return int(key[2:]) + 2000
        return 0

    @staticmethod
    def get_color_mapping(keys: set) -> Dict[str, str]:
        colors = {}
        job_colors = plotly_colors.qualitative.Plotly
        machine_colors = plotly_colors.qualitative.Plotly
        buffer_colors = plotly_colors.colorbrewer.Greens
        transport_colors = plotly_colors.colorbrewer.Greys[3:]
        for key in keys:
            if key.startswith("j"):
                colors[key] = job_colors[int(key[2:]) % len(job_colors)]
            elif key.startswith("m"):
                colors[key] = machine_colors[int(key[2:]) % len(machine_colors)]
            elif key.startswith("t"):
                colors[key] = transport_colors[int(key[2:]) % len(transport_colors)]
            elif key.startswith("b"):
                colors[key] = buffer_colors[int(key[2:]) % len(buffer_colors)]
        return colors

    @staticmethod
    def make_hover_text(d: Dict[str, Any]) -> str:
        if d["type"] == "Schedule":
            return (
                f"Typ: {d['type']}<br>Job: {d['job']}<br>"
                f"Start: {d['start']}<br>End: {d['end']}<br>ID: {d['id']}"
            )
        elif d["type"] == "Transport":
            return (
                f"Typ: {d['type']}<br>Job: {d['job']}<br>"
                f"Start: {d['start']}<br>End: {d['end']}<br>Route: {d['meta_info']}"
            )
        return ""

    @staticmethod
    def build_figure(data: List[Dict[str, Any]], current_time: Any, axis: bool) -> go.Figure:
        fig = go.Figure()
        y_axis_key = "id" if axis else "job"
        legend_key = "job" if axis else "id"
        color_mapping = DashboardDataMapper.get_color_mapping({d[legend_key] for d in data})
        seen_legend = set()

        # Sort data first by start time then by the chosen y-axis key.
        data_sorted = sorted(data, key=lambda x: (x["start"], x[y_axis_key]))
        for item in data_sorted:
            showlegend = item[legend_key] not in seen_legend
            seen_legend.add(item[legend_key])
            fig.add_trace(
                go.Bar(
                    x=[item["end"] - item["start"]],
                    y=[item[y_axis_key]],
                    offsetgroup=item["type"],
                    base=[item["start"]],
                    name=item[legend_key],
                    orientation="h",
                    hovertext=DashboardDataMapper.make_hover_text(item),
                    hoverinfo="text",
                    showlegend=showlegend,
                    legendgroup=item[legend_key],
                    marker=dict(color=color_mapping.get(item[legend_key], "#000000")),
                )
            )

        # Add a vertical line indicating the current time.
        fig.add_shape(
            type="line",
            x0=current_time,
            y0=0,
            x1=current_time,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(color="red", width=2),
            name="Current Time",
            showlegend=True,
        )

        fig.update_xaxes(title_text="Time", overwrite=True)
        fig.update_yaxes(title_text="Job" if not axis else "Component")
        sorted_components = sorted(
            {d[y_axis_key] for d in data_sorted},
            key=lambda x: DashboardDataMapper.map_key_to_sort(x),
        )
        fig.update_layout(
            yaxis=dict(categoryorder="array", categoryarray=sorted_components),
            barmode="group" if not axis else "overlay",
            bargroupgap=0,
            bargap=0.3,
            legend=dict(traceorder="normal"),
            height=800,
            font=dict(family="Open Sans, sans-serif", size=14, color="black"),
        )

        # --- Sort the legend by reordering the traces.
        fig.data = sorted(
            fig.data, key=lambda trace: DashboardDataMapper.map_key_to_sort(trace.name)
        )
        return fig

    @staticmethod
    def map_states_to_schedule_data(last_state: Any, latest_time: Any) -> Tuple[dict, ...]:
        data = []
        for job in last_state.jobs:
            active_op = next(
                filter(
                    lambda x: x.operation_state_state == OperationStateState.PROCESSING,
                    job.operations,
                ),
                None,
            )
            for op in filter(
                lambda x: x.operation_state_state == OperationStateState.DONE, job.operations
            ):
                data.append(
                    {
                        "job": job.id,
                        "start": op.start_time.time,
                        "end": op.end_time.time,
                        "id": op.machine_id,
                        "type": "Schedule",
                        "meta_info": None,
                    }
                )
            if active_op is not None:
                data.append(
                    {
                        "job": job.id,
                        "start": active_op.start_time.time,
                        "end": active_op.end_time.time,
                        "id": active_op.machine_id,
                        "type": "Schedule",
                        "meta_info": None,
                    }
                )
        return tuple(data)

    @staticmethod
    def map_transports_to_data(transport: Any, current_time: Any) -> dict:
        return {
            "type": "Transport",
            "id": transport.id,
            "job": transport.transport_job,
            "start": current_time,
            "end": transport.occupied_till.time,
            "meta_info": f"route: {transport.location.location}",
        }

    @staticmethod
    def make_transport_data(transports: List[Any]) -> Tuple[dict, ...]:
        for _, group in groupby(transports, lambda x: x[0].id):
            group_list = list(group)
            for _, sub_group in groupby(group_list, lambda x: x[0].location.location):
                sub_group_list = list(sub_group)
                yield DashboardDataMapper.map_transports_to_data(
                    sub_group_list[-1][0], sub_group_list[0][1]
                )

    @staticmethod
    def map_states_to_transport_data(
        history: Tuple[Any, ...], latest_time: Any
    ) -> Tuple[dict, ...]:
        transport_states = ((tran, h.time.time) for h in history for tran in h.transports)
        transports = filter(lambda x: x[0].state != TransportStateState.IDLE, transport_states)
        transports = sorted(tuple(transports), key=lambda x: (int(x[0].id[2:]), x[1]))
        transport_list = list(DashboardDataMapper.make_transport_data(transports))
        return tuple(transport_list)

    @staticmethod
    def map_states_to_buffer_data(history: Tuple[Any, ...], latest_time: Any) -> Tuple[dict, ...]:
        # Buffer data mapping not implemented.
        return tuple()

    @staticmethod
    def get_latest_time(last_state: Any) -> Any:
        return max(
            op.end_time.time
            for job in last_state.jobs
            for op in job.operations
            if op.end_time != NoTime()
        )

    @staticmethod
    def add_sub_states_to_history(history: Tuple[Any, ...]) -> Tuple[Any, ...]:
        all_states = []
        for h in history:
            all_states.extend(list(h.sub_states))
            all_states.append(h.state)
        return tuple(all_states)

    @staticmethod
    def map_states_to_gant_data(history: Tuple[Any, ...]) -> Dict[str, Tuple[dict, ...]]:
        all_history = DashboardDataMapper.add_sub_states_to_history(history)
        latest_time = DashboardDataMapper.get_latest_time(all_history[-1])
        schedules = DashboardDataMapper.map_states_to_schedule_data(all_history[-1], latest_time)
        transports = DashboardDataMapper.map_states_to_transport_data(all_history, latest_time)
        buffer_data = DashboardDataMapper.map_states_to_buffer_data(all_history, latest_time)
        return {"schedules": schedules, "transports": transports, "buffer": buffer_data}


# -------------------------------------------------------------------
# Main Dashboard Class with Unique Callback IDs
# -------------------------------------------------------------------


class JobShopDashboard:
    def __init__(
        self,
        data: Dict[str, Any],
        num_machines: Tuple[int],
        num_jobs: int,
        current_time: Any,
        has_transports: bool,
        debug: bool,
        port: int,
    ) -> None:
        self.data = data
        self.num_machines = num_machines
        self.num_jobs = num_jobs
        self.current_time = current_time
        self.has_transports = has_transports
        self.debug = debug
        self.port = port
        self.logger = get_logger("JobShopDashboard", "INFO")

        # Generate unique IDs for every interactive component.
        self.store_data_id = f"store-data-{uuid.uuid4().hex}"
        self.store_current_time_id = f"store-current_time-{uuid.uuid4().hex}"
        self.store_num_machines_id = f"store-num_machines-{uuid.uuid4().hex}"
        self.store_num_jobs_id = f"store-num_jobs-{uuid.uuid4().hex}"
        self.graph_id = f"gantt-{uuid.uuid4().hex}"
        self.show_transport_id = f"show_transport-{uuid.uuid4().hex}"
        self.show_schedules_id = f"show_schedules-{uuid.uuid4().hex}"
        self.show_buffer_id = f"show_buffer-{uuid.uuid4().hex}"
        self.axis_toggle_id = f"axis_toggle-{uuid.uuid4().hex}"
        self.schedule_table_id = f"schedule_table-{uuid.uuid4().hex}"
        self.download_btn_id = f"download_btn-{uuid.uuid4().hex}"
        self.download_db_id = f"download_db-{uuid.uuid4().hex}"
        self.download_csv_btn_id = f"download_csv_btn-{uuid.uuid4().hex}"
        self.download_csv_id = f"download_csv-{uuid.uuid4().hex}"

        self.app = Dash(__name__)
        self._setup_layout()
        self._register_callbacks()

    def _setup_layout(self) -> None:
        table_data = [
            dict(item)
            for item in self.data["schedules"] + self.data["transports"] + self.data["buffer"]
        ]

        self.app.layout = html.Div(
            [
                dcc.Store(id=self.store_data_id, data=self.data),
                dcc.Store(id=self.store_current_time_id, data=self.current_time),
                dcc.Store(id=self.store_num_machines_id, data=self.num_machines),
                dcc.Store(id=self.store_num_jobs_id, data=self.num_jobs),
                html.H1(
                    f"JobShopLab Dashboard for {self.num_machines[0]} machines and {self.num_jobs} jobs",
                    style={
                        "text-align": "center",
                        "font-size": "24px",
                        "font-family": "Roboto",
                        "margin-bottom": "6px",
                    },
                ),
                dcc.Graph(
                    id=self.graph_id,
                    style={
                        "font-size": "14px",
                        "font-family": "Roboto",
                        "margin-bottom": "12px",
                    },
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                daq.BooleanSwitch(
                                    id=self.show_transport_id,
                                    on=self.has_transports,
                                    label="Show Transport",
                                    labelPosition="top",
                                    style={"font-size": "16px", "font-family": "Roboto"},
                                    disabled=not self.has_transports,
                                ),
                            ],
                            style={"margin-right": "20px"},
                        ),
                        html.Div(
                            [
                                daq.BooleanSwitch(
                                    id=self.show_schedules_id,
                                    on=True,
                                    label="Show Machine-Schedules",
                                    labelPosition="top",
                                    style={"font-size": "16px", "font-family": "Roboto"},
                                ),
                            ],
                            style={"margin-right": "20px"},
                        ),
                        html.Div(
                            [
                                daq.BooleanSwitch(
                                    id=self.show_buffer_id,
                                    on=False,
                                    label="Show Buffer occupancy",
                                    labelPosition="top",
                                    style={"font-size": "16px", "font-family": "Roboto"},
                                    disabled=True,
                                ),
                            ],
                            style={"margin-right": "20px"},
                        ),
                        daq.ToggleSwitch(
                            id=self.axis_toggle_id,
                            value=False,
                            label="Job or Component bound Axis",
                            style={"font-size": "16px", "font-family": "Roboto"},
                        ),
                    ],
                    style={"display": "flex", "justify-content": "center", "margin-bottom": "46px"},
                ),
                html.Div(
                    [
                        dag.AgGrid(
                            id="schedule-table",
                            columnDefs=[
                                {
                                    "field": "id",
                                    "headerName": "ID",
                                },
                                {"field": "job", "headerName": "Job"},
                                {"field": "start", "headerName": "Start"},
                                {"field": "end", "headerName": "End"},
                                {
                                    "field": "meta_info",
                                    "headerName": "Meta Info",
                                },
                            ],
                            rowData=table_data,
                            # rowSelection="multiple",  # Enable multi-row selection
                            defaultColDef={
                                "sortable": True,
                                "filter": True,
                                "resizable": True,
                                "cellStyle": {
                                    "textAlign": "center",
                                    "fontSize": "14px",
                                    "fontFamily": "Roboto",
                                },
                                # "checkboxSelection": {
                                #     "function": "params.column == params.columnApi.getAllDisplayedColumns()[0]"
                                # },
                                # "headerCheckboxSelection": {
                                #     "function": "params.column == params.columnApi.getAllDisplayedColumns()[0]"
                                # },
                            },
                            dashGridOptions={
                                "pagination": True,
                                "paginationPageSize": 12,
                                "rowSelection": "multiple",
                                "suppressRowClickSelection": True,
                                "animateRows": False,
                            },
                            className="ag-theme-balham",
                            style={
                                "padding": "auto",
                                "height": "400px",
                                "width": "1012px",
                                "justify-content": "center",
                                "font-size": "14px",
                                "font-family": "Roboto",
                            },
                        )
                    ],
                    style={
                        "display": "flex",
                        "justify-content": "center",  # Centers the table horizontally
                        "alignItems": "center",
                        "margin-bottom": "12px",
                        "font-size": "14px",
                        "font-family": "Roboto",
                        "width": "100%",
                    },
                ),
                html.Div(
                    [
                        html.Button(
                            "Download",
                            id=self.download_btn_id,
                            style={
                                "font-size": "16px",
                                "font-family": "Roboto",
                                "width": "180px",
                                "display": "inline-block",
                                "margin-bottom": "12px",
                                "margin-right": "20px",  # Added margin-right for spacing
                                "height": "36px",
                                "verticalAlign": "middle",
                                "padding": "8px 16px",
                                "background-color": "#4CAF50",  # A nice green color
                                "color": "white",
                                "border": "none",
                                "border-radius": "4px",
                                "cursor": "pointer",
                                "transition": "all 0.3s ease",
                                "box-shadow": "0 2px 5px rgba(0,0,0,0.2)",
                                "text-transform": "uppercase",
                                "font-weight": "bold",
                                "letter-spacing": "0.5px",
                            },
                        ),
                        dcc.Download(id=self.download_db_id),
                        html.Button(
                            "Download CSV",
                            id=self.download_csv_btn_id,
                            style={
                                "font-size": "16px",
                                "font-family": "Roboto",
                                "width": "180px",
                                "display": "inline-block",
                                "margin-bottom": "12px",
                                "height": "36px",
                                "verticalAlign": "middle",
                                "padding": "8px 16px",
                                "background-color": "#4CAF50",  # A nice green color
                                "color": "white",
                                "border": "none",
                                "border-radius": "4px",
                                "cursor": "pointer",
                                "transition": "all 0.3s ease",
                                "box-shadow": "0 2px 5px rgba(0,0,0,0.2)",
                                "text-transform": "uppercase",
                                "font-weight": "bold",
                                "letter-spacing": "0.5px",
                            },
                        ),
                        dcc.Download(id=self.download_csv_id),
                    ],
                    style={"display": "flex", "justify-content": "center", "margin-bottom": "46px"},
                ),
            ],
            style={
                "display": "flex",
                "flex-direction": "column",
                "justify-content": "center",
                "backgroundColor": "white",
                "text-align": "center",
                "font-size": "20px",
                "font-family": "Roboto",
                "padding": "20px",
            },
        )
        self.app.title = "JobShopLab Dashboard"

    def _register_callbacks(self) -> None:
        @self.app.callback(
            Output(self.graph_id, "figure"),
            Input(self.store_data_id, "data"),
            Input(self.store_current_time_id, "data"),
            Input(self.show_transport_id, "on"),
            Input(self.show_schedules_id, "on"),
            Input(self.show_buffer_id, "on"),
            Input(self.axis_toggle_id, "value"),
        )
        def update_fig(data, current_time, show_transport, show_schedules, show_buffer, axis):
            return self.update_fig(
                data, current_time, show_transport, show_schedules, show_buffer, axis
            )

        @self.app.callback(
            Output(self.download_db_id, "data"),
            Input(self.store_data_id, "data"),
            Input(self.store_current_time_id, "data"),
            Input(self.store_num_jobs_id, "data"),
            Input(self.store_num_machines_id, "data"),
            Input(self.download_btn_id, "n_clicks"),
            prevent_initial_call=True,
        )
        def download_db(data, current_time, num_jobs, num_machines, n_clicks):
            return self.download_db(data, current_time, num_jobs, num_machines, n_clicks)

        @self.app.callback(
            Output(self.download_csv_id, "data"),
            Input(self.store_data_id, "data"),
            Input(self.download_csv_btn_id, "n_clicks"),
            prevent_initial_call=True,
        )
        def download_csv(data, n_clicks):
            return self.download_csv(data, n_clicks)

    def update_fig(
        self, data, current_time, show_transport, show_schedules, show_buffer, axis
    ) -> go.Figure:
        try:
            filtered_data = []
            if show_transport:
                filtered_data += data["transports"]
            if show_schedules:
                filtered_data += data["schedules"]
            if show_buffer:
                filtered_data += data["buffer"]
            if not filtered_data:
                return go.Figure()
            return DashboardDataMapper.build_figure(filtered_data, current_time, axis)
        except Exception as e:
            self.logger.error(f"Error updating figure: {e}")
            return go.Figure()

    def download_db(self, data, current_time, num_jobs, num_machines, n_clicks):
        try:
            file_bytes = pickle.dumps((data, num_jobs, num_machines, current_time))
            return dcc.send_bytes(file_bytes, "dashboard_db.lab")
        except Exception as e:
            self.logger.error(f"Error preparing file download: {e}")
            return None

    def download_csv(self, data, n_clicks):
        try:
            df = pd.DataFrame(data["schedules"] + data["transports"] + data["buffer"])
            return dcc.send_data_frame(df.to_csv, "dashboard_data.csv")
        except Exception as e:
            self.logger.error(f"Error preparing CSV download: {e}")
            return None

    def run(self) -> None:
        try:
            port = DashboardUtils.check_port(self.port)
            self.app.run(
                debug=self.debug,
                use_reloader=False,
                port=port,
                jupyter_height=1500,
                jupyter_mode="inline",
            )
        except Exception as e:
            self.logger.error(f"Failed to launch dashboard: {e}")
            raise


def start_dashboard_from_file(file_path: str, debug: bool, port: int) -> None:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFound(path)
    logger = get_logger("FileLoad", "INFO")
    try:
        with open(path, "rb") as f:
            data, num_jobs, num_machines, current_time = pickle.load(f)
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        raise

    has_transports = DashboardUtils.has_transports(data)
    dashboard = JobShopDashboard(
        data, num_machines, num_jobs, current_time, has_transports, debug, port
    )
    dashboard.run()


def render_in_dashboard(
    loglevel: int | str,
    history: Tuple[StateMachineResult, ...],
    instance: InstanceConfig,
    debug: bool = False,
    port: int = 8050,
    *args,
    **kwargs,
) -> None:
    logger = get_logger("GanttPlotter", loglevel)
    logger.info("Plotting Gantt Chart")
    if len(history) < 2:
        logger.error("No data available to plot Gantt Chart")
        return

    data = DashboardDataMapper.map_states_to_gant_data(history)
    num_machines = (len(history[-1].state.machines),)
    num_jobs = len(history[-1].state.jobs)
    current_time = history[-1].state.time.time
    has_transports = any(tt.duration > 0 for tt in instance.logistics.travel_times.values())
    dashboard = JobShopDashboard(
        data, num_machines, num_jobs, current_time, has_transports, debug, port
    )
    dashboard.run()


def parse_cli_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Job Shop Lab Dashboard")
    parser.add_argument("file_path", type=str, help="Path of the file to load")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=8050, help="Port to run the dashboard on")
    return parser.parse_args()


def main() -> None:
    args = parse_cli_arguments()
    try:
        start_dashboard_from_file(args.file_path, args.debug, args.port)
    except Exception as e:
        logger = get_logger("Main", "ERROR")
        logger.error(f"Dashboard failed to start: {e}")


if __name__ == "__main__":
    main()
