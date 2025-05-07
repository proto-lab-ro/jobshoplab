import argparse
import pickle
import socket
import time
import uuid
from itertools import groupby
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Union

import dash_ag_grid as dag
import dash_daq as daq
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html
from plotly import colors as plotly_colors

from jobshoplab.types.instance_config_types import InstanceConfig
from jobshoplab.types.state_types import (NoTime, OperationStateState,
                                          StateMachineResult,
                                          TransportStateState)
from jobshoplab.utils.exceptions import FileNotFound
from jobshoplab.utils.logger import get_logger

# -------------------------------------------------------------------
# Utility Classes
# -------------------------------------------------------------------


class DashboardUtils:
    """Utility class for dashboard operations."""

    @staticmethod
    def map_time(int_time: int, current_time: int) -> str:
        """
        Map integer time to real-time representation.

        Args:
            int_time: Integer time to be mapped.
            current_time: Current time reference.

        Returns:
            Formatted time string in the format 'YYYY-MM-DD HH:MM:SS'.
        """
        current_time += 1
        real_time = time.time()
        time_fct = real_time / current_time
        computed_time = int_time * time_fct
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(computed_time)))

    @staticmethod
    def is_port_in_use(port: int) -> bool:
        """
        Check if a port is in use.

        Args:
            port: Port number to check.

        Returns:
            True if port is in use, False otherwise.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) == 0

    @staticmethod
    def check_port(port: int) -> int:
        """
        Find an available port starting from the given port.

        Args:
            port: Starting port number to check.

        Returns:
            An available port number.
        """
        while DashboardUtils.is_port_in_use(port):
            port += 1
        return port

    @staticmethod
    def has_transports(data: Dict[str, Any]) -> bool:
        """
        Check if the data contains transport information.

        Args:
            data: Dictionary containing state data.

        Returns:
            True if transport data is present and valid, False otherwise.
        """
        try:
            return any(item.get("time", 0) > 0 for item in data.get("travel_times", {}).values())
        except Exception:
            return False


class DashboardDataMapper:
    """Class responsible for mapping data for dashboard visualization."""

    @staticmethod
    def map_key_to_sort(key: str) -> int:
        """
        Map component keys to sort values for consistent ordering.

        Args:
            key: Component identifier key (e.g., 'j1', 'm2', 't3', 'b4').

        Returns:
            Integer value for sorting purposes.
        """
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
    def get_color_mapping(keys: Set[str]) -> Dict[str, str]:
        """
        Create a color mapping for different component types.

        Args:
            keys: Set of component identifier keys.

        Returns:
            Dictionary mapping component keys to color values.
        """
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
        """
        Generate hover text for Gantt chart elements.

        Args:
            d: Dictionary containing element data.

        Returns:
            Formatted HTML string for hover tooltip.
        """
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
        """
        Build Plotly Gantt chart figure from data.

        Args:
            data: List of dictionaries containing schedule, transport, and buffer data.
            current_time: Current time to display as vertical line.
            axis: If True, use components as y-axis; if False, use jobs as y-axis.

        Returns:
            Plotly Figure object.
        """
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
    def map_states_to_schedule_data(
        last_state: Any, latest_time: Any
    ) -> Tuple[Dict[str, Any], ...]:
        """
        Extract schedule data from state machine state.

        Args:
            last_state: The final state machine state containing job and operation info.
            latest_time: The latest time in the state machine history.

        Returns:
            Tuple of dictionaries containing schedule data.
        """
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
    def map_transports_to_data(transport: Any, current_time: Any) -> Dict[str, Any]:
        """
        Map transport data to visualization format.

        Args:
            transport: Transport object with state information.
            current_time: Current time reference.

        Returns:
            Dictionary containing formatted transport data.
        """
        return {
            "type": "Transport",
            "id": transport.id,
            "job": transport.transport_job,
            "start": current_time,
            "end": transport.occupied_till.time,
            "meta_info": f"route: {transport.location.location}",
        }

    @staticmethod
    def make_transport_data(transports: List[Any]) -> Iterator[Dict[str, Any]]:
        """
        Generate transport data in visualization-ready format.

        Args:
            transports: List of transport objects with state information.

        Yields:
            Dictionaries containing formatted transport data.
        """
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
    ) -> Tuple[Dict[str, Any], ...]:
        """
        Extract transport data from state machine history.

        Args:
            history: Tuple of state machine results.
            latest_time: The latest time in the state machine history.

        Returns:
            Tuple of dictionaries containing transport data.
        """
        transport_states = ((tran, h.time.time) for h in history for tran in h.transports)
        transports = filter(lambda x: x[0].state != TransportStateState.IDLE, transport_states)
        transports = sorted(tuple(transports), key=lambda x: (int(x[0].id[2:]), x[1]))
        transport_list = list(DashboardDataMapper.make_transport_data(transports))
        return tuple(transport_list)

    @staticmethod
    def map_states_to_buffer_data(
        history: Tuple[Any, ...], latest_time: Any
    ) -> Tuple[Dict[str, Any], ...]:
        """
        Extract buffer data from state machine history.

        Args:
            history: Tuple of state machine results.
            latest_time: The latest time in the state machine history.

        Returns:
            Tuple of dictionaries containing buffer data (currently not implemented).
        """
        # Buffer data mapping not implemented.
        return tuple()

    @staticmethod
    def get_latest_time(last_state: Any) -> int:
        """
        Get the latest time from the state machine state.

        Args:
            last_state: The final state machine state.

        Returns:
            The latest time value from operations.
        """
        return max(
            op.end_time.time
            for job in last_state.jobs
            for op in job.operations
            if op.end_time != NoTime()
        )

    @staticmethod
    def add_sub_states_to_history(history: Tuple[Any, ...]) -> Tuple[Any, ...]:
        """
        Extract and combine sub-states from history.

        Args:
            history: Tuple of state machine results.

        Returns:
            Tuple of states including sub-states.
        """
        all_states = []
        for h in history:
            all_states.extend(list(h.sub_states))
            all_states.append(h.state)
        return tuple(all_states)

    @staticmethod
    def map_states_to_gant_data(history: Tuple[Any, ...]) -> Dict[str, Tuple[Dict[str, Any], ...]]:
        """
        Map state machine history to Gantt chart data.

        Args:
            history: Tuple of state machine results.

        Returns:
            Dictionary containing schedules, transports, and buffer data.
        """
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
    """
    Main dashboard class for visualizing job shop scheduling data.

    Attributes:
        data: Dictionary containing schedule, transport, and buffer data.
        num_machines: Tuple containing the number of machines.
        num_jobs: Number of jobs in the instance.
        current_time: Current time reference.
        has_transports: Boolean indicating if transport data is present.
        debug: Boolean flag for debug mode.
        port: Port number for the dashboard server.
        logger: Logger instance.
        app: Dash application instance.
    """

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
        """
        Initialize the JobShopDashboard.

        Args:
            data: Dictionary containing schedule, transport, and buffer data.
            num_machines: Tuple containing the number of machines.
            num_jobs: Number of jobs in the instance.
            current_time: Current time reference.
            has_transports: Boolean indicating if transport data is present.
            debug: Boolean flag for debug mode.
            port: Port number for the dashboard server.
        """
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
        """Set up the layout for the Dash application."""
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
                        "font-family": "Roboto, arial",
                        "margin-bottom": "6px",
                    },
                ),
                dcc.Graph(
                    id=self.graph_id,
                    style={
                        "font-size": "14px",
                        "font-family": "Roboto, arial",
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
                                    style={"font-size": "16px", "font-family": "Roboto, arial"},
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
                                    style={"font-size": "16px", "font-family": "Roboto, arial"},
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
                                    style={"font-size": "16px", "font-family": "Roboto, arial"},
                                    disabled=True,
                                ),
                            ],
                            style={"margin-right": "20px"},
                        ),
                        daq.ToggleSwitch(
                            id=self.axis_toggle_id,
                            value=False,
                            label="Job or Component bound Axis",
                            style={"font-size": "16px", "font-family": "Roboto, arial"},
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
                                    "fontFamily": "Roboto, arial",
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
                                "font-family": "Roboto, arial",
                            },
                        )
                    ],
                    style={
                        "display": "flex",
                        "justify-content": "center",  # Centers the table horizontally
                        "alignItems": "center",
                        "margin-bottom": "12px",
                        "font-size": "14px",
                        "font-family": "Roboto, arial",
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
                                "font-family": "Roboto, arial",
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
                                "font-family": "Roboto, arial",
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
                "font-family": "Roboto, arial",
                "padding": "20px",
            },
        )
        self.app.title = "JobShopLab Dashboard"

    def _register_callbacks(self) -> None:
        """Register callback functions for Dash application interactivity."""

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
        self,
        data: Dict[str, List[Dict[str, Any]]],
        current_time: int,
        show_transport: bool,
        show_schedules: bool,
        show_buffer: bool,
        axis: bool,
    ) -> go.Figure:
        """
        Update the Gantt chart figure based on user selections.

        Args:
            data: Dictionary containing schedule, transport, and buffer data.
            current_time: Current time reference.
            show_transport: Whether to display transport data.
            show_schedules: Whether to display schedule data.
            show_buffer: Whether to display buffer data.
            axis: If True, use components as y-axis; if False, use jobs as y-axis.

        Returns:
            Updated Plotly Figure object.
        """
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

    def download_db(
        self,
        data: Dict[str, Any],
        current_time: int,
        num_jobs: int,
        num_machines: Tuple[int],
        n_clicks: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Prepare dashboard data for download in binary format.

        Args:
            data: Dictionary containing schedule, transport, and buffer data.
            current_time: Current time reference.
            num_jobs: Number of jobs in the instance.
            num_machines: Tuple containing the number of machines.
            n_clicks: Number of times the download button has been clicked.

        Returns:
            Dictionary containing download data or None if an error occurs.
        """
        try:
            file_bytes = pickle.dumps((data, num_jobs, num_machines, current_time))
            return dcc.send_bytes(file_bytes, "dashboard_db.lab")
        except Exception as e:
            self.logger.error(f"Error preparing file download: {e}")
            return None

    def download_csv(
        self, data: Dict[str, List[Dict[str, Any]]], n_clicks: int
    ) -> Optional[Dict[str, Any]]:
        """
        Prepare dashboard data for download in CSV format.

        Args:
            data: Dictionary containing schedule, transport, and buffer data.
            n_clicks: Number of times the download button has been clicked.

        Returns:
            Dictionary containing download data or None if an error occurs.
        """
        try:
            df = pd.DataFrame(data["schedules"] + data["transports"] + data["buffer"])
            return dcc.send_data_frame(df.to_csv, "dashboard_data.csv")
        except Exception as e:
            self.logger.error(f"Error preparing CSV download: {e}")
            return None

    def run(self) -> None:
        """
        Run the dashboard application.

        Raises:
            Exception: If dashboard fails to launch.
        """
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
    """
    Start the dashboard from a data file.

    Args:
        file_path: Path to the data file.
        debug: Flag to enable debug mode.
        port: Port number for the dashboard server.

    Raises:
        FileNotFound: If the file does not exist.
        Exception: If the file cannot be loaded.
    """
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
    loglevel: Union[int, str],
    history: Tuple[StateMachineResult, ...],
    instance: InstanceConfig,
    debug: bool = False,
    port: int = 8050,
    *args,
    **kwargs,
) -> None:
    """
    Render state machine results in a dashboard.

    Args:
        loglevel: Log level for the dashboard.
        history: Tuple of state machine results.
        instance: Instance configuration.
        debug: Flag to enable debug mode.
        port: Port number for the dashboard server.
        *args: Additional positional arguments.
        **kwargs: Additional keyword arguments.
    """
    logger = get_logger("GanttPlotter", loglevel)
    logger.info("Plotting Gantt Chart")
    if len(history) < 2:
        logger.error("No data available to plot Gantt Chart")
        return

    data = DashboardDataMapper.map_states_to_gant_data(history)
    num_machines = (len(history[-1].state.machines),)
    num_jobs = len(history[-1].state.jobs)
    current_time = history[-1].state.time.time
    has_transports = any(tt.time > 0 for tt in instance.logistics.travel_times.values())
    dashboard = JobShopDashboard(
        data, num_machines, num_jobs, current_time, has_transports, debug, port
    )
    dashboard.run()


def parse_cli_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="Job Shop Lab Dashboard")
    parser.add_argument("file_path", type=str, help="Path of the file to load")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=8050, help="Port to run the dashboard on")
    return parser.parse_args()


def main() -> None:
    """
    Main entry point for the dashboard application.
    """
    args = parse_cli_arguments()
    try:
        start_dashboard_from_file(args.file_path, args.debug, args.port)
    except Exception as e:
        logger = get_logger("Main", "ERROR")
        logger.error(f"Dashboard failed to start: {e}")


if __name__ == "__main__":
    main()
