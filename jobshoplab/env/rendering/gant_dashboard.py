import argparse
import pickle
import socket
import time
from itertools import groupby
from pathlib import Path

import dash_daq as daq
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, callback, dash_table, dcc, html
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


def _map_time(int_time, current_time):
    current_time += 1
    _real_time = time.time()
    time_fct = _real_time / current_time
    _time = int_time * time_fct
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(_time)))


def start_dashboard_from_file(dir, debug, port):
    if isinstance(dir, str):
        dir = Path(dir)
    if not dir.exists():
        raise FileNotFound(dir)
    with open(dir, "rb") as dir:
        data, num_jobs, num_machines, current_time = pickle.load(dir)
    _launch_dashboard(debug, port, data, num_machines, num_jobs, current_time)


def render_in_dashboard(
    loglevel: int | str,
    history: tuple[StateMachineResult, ...],
    instance: InstanceConfig,
    debug=False,
    port=8050,
    *args,
    **kwargs,
):
    """
    Plot a Gantt chart based on the given instance, configuration, and state.

    Parameters:
    - instance (InstanceConfig): The instance configuration.

    - loglevel (int | str): The log level for logging.
    - backend (Callable): The backend function used to render/save the chart.
    - last_state (State): The last state of the job shop.
    - *args: Additional positional arguments.
    - **kwargs: Additional keyword arguments.

    Returns:
    - None

    Raises:
    - None
    """

    logger = get_logger("GanttPlotter", loglevel)
    logger.info("Plotting Gantt Chart")
    if len(history) < 2:
        logger.error("No data available to plot Gantt Chart")
        return

    data = _map_states_to_gant_data(history)
    num_machines = (len(history[-1].state.machines),)
    num_jobs = len(history[-1].state.jobs)
    current_time = history[-1].state.time.time
    has_transports = any(_tt.duration > 0 for _tt in instance.logistics.travel_times.values())
    # call backend to render/save fig
    _launch_dashboard(debug, port, data, num_machines, num_jobs, current_time, has_transports)


def _launch_dashboard(debug, port, data, num_machines, num_jobs, current_time, has_transports):
    app = _create_dashboard_app(data, num_machines, num_jobs, current_time, has_transports)
    port = _check_port(port)

    app.run(
        debug=debug, use_reloader=False, port=port, jupyter_height=1500, jupyter_mode="external"
    )


def _is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def _check_port(port):
    while _is_port_in_use(port):
        port += 1
    return port


def _create_dashboard_app(data, num_machines, num_jobs, current_time, has_transports):
    app = Dash(__name__)
    app.layout = html.Div(
        [
            dcc.Store(id="data", data=data),
            dcc.Store(id="current_time", data=current_time),
            dcc.Store(id="num_machines", data=num_machines),
            dcc.Store(
                id="num_jobs",
                data=num_jobs,
            ),
            html.H1(
                "JobShopLab Dashboard for {} machines and {} jobs".format(
                    num_machines[0], num_jobs
                ),
                style={
                    "text-align": "center",
                    "font-size": "24px",
                    "font-family": "Open Sans",
                    "margin-bottom": "6px",
                },
            ),
            dcc.Graph(
                id="gantt",
                style={"font-size": "14px", "font-family": "Open Sans", "margin-bottom": "12px"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            daq.BooleanSwitch(
                                id="show_transport",
                                on=has_transports,
                                label="Show Transport",
                                labelPosition="top",
                                style={"font-size": "16px", "font-family": "Open Sans"},
                                disabled=not has_transports,
                            ),
                        ],
                        style={"margin-right": "20px"},
                    ),
                    html.Div(
                        [
                            daq.BooleanSwitch(
                                id="show_schedules",
                                on=True,
                                label="Show Machine-Schedules",
                                labelPosition="top",
                                style={"font-size": "16px", "font-family": "Open Sans"},
                            ),
                        ],
                        style={"margin-right": "20px"},
                    ),
                    html.Div(
                        [
                            daq.BooleanSwitch(
                                id="show_buffer",
                                on=False,
                                label="Show Buffer occupancy",
                                labelPosition="top",
                                style={
                                    "font-size": "16px",
                                    "font-family": "Open Sans",
                                    # "margin-right": "20px",
                                },
                                disabled=True,
                            ),
                        ],
                        style={"margin-right": "20px"},
                    ),
                    daq.ToggleSwitch(
                        id="axis_toggle",
                        value=False,
                        label="Job or Component bound Axis",
                        style={"font-size": "16px", "font-family": "Open Sans"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "margin-bottom": "46px",
                },
            ),
            html.Div(
                [
                    dash_table.DataTable(
                        id="schedule_table",
                        columns=[
                            {"name": i, "id": i}
                            for i in ["type", "id", "job", "start", "end", "meta_info"]
                        ],
                        data=[
                            dict(item)
                            for item in data["schedules"] + data["transports"] + data["buffer"]
                        ],
                        page_size=10,
                        style_table={
                            "font-size": "14px",
                            "font-family": "Open Sans",
                            "margin": "auto",
                            "width": "100%",
                        },
                        style_header={"fontWeight": "bold"},
                        style_cell={"textAlign": "center"},
                        sort_action="native",
                        filter_action="native",
                    ),
                ],
                style={"display": "flex", "justify-content": "center", "margin-bottom": "12px"},
            ),
            html.Button(
                "Download",
                id="download_btn",
                style={
                    "font-size": "16px",
                    "font-family": "Open Sans",
                    "width": "140px",
                    "display": "inline-block",
                    "margin-bottom": "12px",
                    "height": "20px",
                    "verticalAlign": "top",
                },
            ),
            dcc.Download(id="download_db"),
            html.Button(
                "Download CSV",
                id="download_csv_btn",
                style={
                    "font-size": "16px",
                    "font-family": "Open Sans",
                    "width": "140px",
                    "display": "inline-block",
                    "margin-bottom": "12px",
                    "height": "20px",
                    "verticalAlign": "top",
                },
            ),
            dcc.Download(id="download_csv"),
        ],
        style={
            "text-align": "center",
            "font-size": "20px",
            "font-family": "Open Sans",
            "padding": "20px",
        },
    )
    app.title = "JobShopLab Dashboard"
    return app


@callback(
    Output("gantt", "figure"),
    Input("data", "data"),
    Input("current_time", "data"),
    Input("show_transport", "on"),
    Input("show_schedules", "on"),
    Input("show_buffer", "on"),
    Input("axis_toggle", "value"),
)
def _update_fig(data, current_time, s0, s1, s2, axis):
    filterd_data = []

    if s0:
        filterd_data += data["transports"]
    if s1:
        filterd_data += data["schedules"]
    if s2:
        filterd_data += data["buffer"]
    if len(filterd_data) == 0:
        return go.Figure()
    fig = _build_figure(filterd_data, current_time, axis)
    return fig


@callback(
    Output("download_db", "data"),
    Input("data", "data"),
    Input("current_time", "data"),
    Input("num_jobs", "data"),
    Input("num_machines", "data"),
    Input("download_btn", "n_clicks"),
    prevent_initial_call=True,
)
def _download_as_file(data, current_time, num_jobs, num_machines, n_clicks):
    return dcc.send_bytes(
        pickle.dumps((data, num_jobs, num_machines, current_time)), "dashboard_db.lab"
    )


@callback(
    Output("download_csv", "data"),
    Input("data", "data"),
    Input("download_csv_btn", "n_clicks"),
    prevent_initial_call=True,
)
def _download_as_csv(data, n_clicks):
    df = pd.DataFrame(data["schedules"] + data["transports"] + data["buffer"])
    return dcc.send_data_frame(df.to_csv, "dashboard_data.csv")


def _map_key_to_sort(key):
    if key.startswith("j"):
        return int(key[2:])
    if key.startswith("m"):
        return int(key[2:])
    if key.startswith("t"):
        return int(key[2:]) + 1000
    if key.startswith("t"):
        return int(key[2:]) + 2000


def _get_color_mapping(keys):
    colors = {}
    job_colors = plotly_colors.qualitative.Plotly
    machine_colors = plotly_colors.qualitative.Plotly
    buffer_colors = plotly_colors.colorbrewer.Greens
    transport_colors = plotly_colors.colorbrewer.Greys[3:]
    for key in keys:
        if key.startswith("j"):
            colors[key] = job_colors[int(key[2:]) % len(job_colors)]
        if key.startswith("m"):
            colors[key] = machine_colors[int(key[2:]) % len(machine_colors)]
        if key.startswith("t"):
            colors[key] = transport_colors[int(key[2:]) % len(transport_colors)]
        if key.startswith("b"):
            colors[key] = buffer_colors[int(key[2:]) % len(buffer_colors)]
    return colors


def _make_hover_text(d):
    match d["type"]:
        case "Schedule":
            return f"Typ: {d["type"]}<br>Job: {d["job"]}<br>Start: {d['start']}<br>End: {d['end']}<br>ID: {d['id']}"
        case "Transport":
            return f"Typ: {d["type"]}<br>Job: {d["job"]}<br>Start: {d['start']}<br>End: {d['end']}<br>Route: {d['meta_info']}"


def _build_figure(data, current_time, axis):
    fig = go.Figure()
    y = "id" if axis else "job"
    mc = "job" if axis else "id"
    color_mapping = _get_color_mapping(set([d[mc] for d in data]))
    seen_mc = set()
    data = sorted(data, key=lambda x: x["start"])
    data = sorted(data, key=lambda x: x[y])
    for _d in data:
        showlegend = _d[mc] not in seen_mc
        seen_mc.add(_d[mc])
        fig.add_trace(
            go.Bar(
                x=[_d["end"] - _d["start"]],
                y=[_d[y]],
                offsetgroup=_d["type"],
                base=[_d["start"]],
                name=_d[mc],
                orientation="h",
                hovertext=_make_hover_text(_d),
                hoverinfo="text",
                showlegend=showlegend,
                marker=dict(
                    color=color_mapping[_d[mc]],
                ),
            )
        )
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

    fig = fig.update_xaxes(
        title_text="time",
        overwrite=True,
    )
    fig = fig.update_yaxes(
        title_text="Job" if not axis else "Component",
    )
    sorted_components = sorted(set([d[y] for d in data]), key=lambda x: _map_key_to_sort(x))
    fig = fig.update_layout(
        yaxis=dict(
            categoryorder="array", categoryarray=sorted_components
        ),  # Order tasks by duration
        barmode="group" if not axis else "overlay",  # Bars are overlaid without stacking
        bargroupgap=0,
        bargap=0.3,  # Gap between bars of adjacent location coordinates
        legend=dict(traceorder="normal"),  # Preserve the trace order in legend
        height=800,
        font=dict(
            family="Open Sans, sans-serif",  # Plotly's default font family
            size=14,
            color="black",
        ),
    )

    return fig


def _map_states_to_schedule_data(last_state, latest_time):
    data = []
    for job in last_state.jobs:
        active_operation = next(
            filter(
                lambda x: x.operation_state_state == OperationStateState.PROCESSING, job.operations
            ),
            None,
        )
        for operation in tuple(
            filter(lambda x: x.operation_state_state == OperationStateState.DONE, job.operations)
        ):
            data.append(
                dict(
                    job=job.id,
                    start=operation.start_time.time,
                    end=operation.end_time.time,
                    id=operation.machine_id,
                    type="Schedule",
                    meta_info=None,
                )
            )
        if active_operation is not None:
            start = active_operation.start_time.time
            finish = active_operation.end_time.time
            data.append(
                dict(
                    job=job.id,
                    start=start,
                    end=finish,
                    id=active_operation.machine_id,
                    type="Schedule",
                    meta_info=None,
                )
            )
    return tuple(data)


def _map_transports_to_data(transport, current_time):
    return dict(
        type="Transport",
        id=transport.id,
        job=transport.transport_job,
        start=current_time,
        end=transport.occupied_till.time,
        meta_info=f"route: {transport.location.location}",
    )


def _make_transport_data(transports):
    for _, group in groupby(transports, lambda x: x[0].id):
        group = list(group)
        for _, sub_group in groupby(group, lambda x: x[0].location.location):
            sub_group = list(sub_group)
            yield _map_transports_to_data(sub_group[-1][0], sub_group[0][1])


def _map_states_to_transport_data(history, latest_time):
    transports = tuple()
    transport_states = ((tran, h.time.time) for h in history for tran in h.transports)
    transports = filter(lambda x: x[0].state != TransportStateState.IDLE, transport_states)
    transports = sorted(tuple(transports), key=lambda x: (int(x[0].id[2:]), x[1]))
    _transports = list(_make_transport_data(transports))
    return tuple(_transports)


def _map_states_to_buffer_data(history, latest_time):
    return tuple()


def _get_latest_time(last_state):
    latest_time = max(
        [
            operation.end_time.time
            for job in last_state.jobs
            for operation in job.operations
            if operation.end_time != NoTime()
        ]
    )
    return latest_time


def _add_sub_states_to_history(history):
    for h in history:
        yield from h.sub_states
        yield h.state


def _map_states_to_gant_data(history):
    history = tuple(_add_sub_states_to_history(history))
    latest_time = _get_latest_time(history[-1])
    mapped_schedules = _map_states_to_schedule_data(history[-1], latest_time)
    mapped_transports = _map_states_to_transport_data(history, latest_time)
    mapped_buffer = _map_states_to_buffer_data(history, latest_time)
    return {"schedules": mapped_schedules, "transports": mapped_transports, "buffer": mapped_buffer}


def file_load_cli():
    parser = argparse.ArgumentParser(description="Job Shop Lab Dashboard")
    parser.add_argument("dir", type=str, help="Directory of the file to load")
    parser.add_argument("--debug", type=bool, default=False, help="Enable debug mode")
    parser.add_argument("--port", type=int, default=8050, help="Port to run the dashboard on")

    args = parser.parse_args()
    dir = args.dir
    debug = args.debug
    port = args.port
    start_dashboard_from_file(dir, debug, port)
