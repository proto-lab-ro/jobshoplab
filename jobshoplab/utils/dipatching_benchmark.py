import os
import tempfile
from pathlib import Path

from heracless import load_config

from jobshoplab import JobShopLabEnv
from jobshoplab.compiler import Compiler
from jobshoplab.compiler.repos import DslRepository
from jobshoplab.utils.state_machine_utils import \
    dispatch_rules_uitls as dispatch_utils

# Load Config
temp_file = tempfile.NamedTemporaryFile(delete=False).name
config = load_config(Path("data/config/jonathan_conf.yaml"), Path(temp_file), True)


def fifo(env):
    next_possible_transition = env.state.possible_transitions[0]
    should_do = True

    # Dispatching Rules for Transport
    if next_possible_transition.component_id.startswith("t"):
        should_do = True

    # Dispatching Rules for the Machines
    elif next_possible_transition.component_id.startswith("m"):
        should_do = True

    return should_do


def spt(env):
    next_possible_transition = env.state.possible_transitions[0]
    should_do = True
    # Dispatching Rules for Transport
    if next_possible_transition.component_id.startswith("t"):
        should_do = True

    # Dispatching Rules for the Machines
    elif next_possible_transition.component_id.startswith("m"):
        next_job_at_machine = dispatch_utils.get_machine_prebuffer_jobs_by_processing_time(
            env.instance, env.state.state, mode="SPT"
        )
        should_do = (
            next_job_at_machine[next_possible_transition.component_id]
            == next_possible_transition.job_id
        )
    return should_do


def mwkr(env):
    next_possible_transition = env.state.possible_transitions[0]
    should_do = True
    # Dispatching Rules for Transport
    if next_possible_transition.component_id.startswith("t"):
        should_do = True

    # Dispatching Rules for the Machines
    elif next_possible_transition.component_id.startswith("m"):
        next_job_at_machine = dispatch_utils.get_machine_jobs_by_remaining_processing_time(
            env.instance, env.state.state, mode="srpt"
        )
        should_do = (
            next_job_at_machine[next_possible_transition.component_id]
            == next_possible_transition.job_id
        )
    return should_do


if __name__ == "__main__":
    dump_dir = Path("./tmp/tmp_heracless.py")
    instance_dir = "data/jssp_instances/transport"
    instance_names = [
        "ft06",
        "ft10",
        "la01",
        "la02",
        "la03",
        "la04",
        "la05",
        "la06",
        "la07",
        "la08",
        "la09",
        "la10",
        "la11",
        "la12",
        "la13",
        "la14",
        "la15",
        "la16",
        "la17",
        "la18",
        "la19",
        "la20",
        "la21",
        "la22",
        "la23",
        "la24",
        "la25",
        "la26",
        "la27",
        "la28",
        "la29",
        "la30",
        "la31",
        "la32",
        "la33",
        "la34",
        "la35",
        "la36",
        "la37",
        "la38",
        "la39",
        "la40",
    ]
    instance_dirs = map(lambda x: Path(os.path.join(instance_dir, x + ".yaml")), instance_names)
    repos = map(lambda x: DslRepository(x, loglevel="warning", config=config), instance_dirs)
    _compiler = map(lambda x: Compiler(config, loglevel="warning", repo=x), repos)
    envs = map(lambda x: JobShopLabEnv(config=config, compiler=x), _compiler)

    strategies = {
        "fifo": fifo,
        "spt": spt,
        "mwkr": mwkr,
    }
    run = map(lambda x: (x, strategies), envs)

    results = []

    for env, strategies in run:
        for name, strategy in strategies.items():
            env.reset()

            while not env.done:
                should_do = strategy(env)
                env.step(1 if should_do else 0)

            results.append(
                {
                    "strategy": name,
                    "instance": env.instance.description,
                    "time": env.state.state.time.time,
                }
            )

    with open("results.jsonl", "w") as f:
        for result in results:
            f.write(f"{result}\n".replace("'", '"'))
