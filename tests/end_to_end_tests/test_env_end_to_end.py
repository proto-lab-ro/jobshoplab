import os
from dataclasses import replace
from pathlib import Path

import numpy as np

from jobshoplab import JobShopLabEnv
from jobshoplab.compiler import Compiler
from jobshoplab.compiler.repos import SpecRepository
from jobshoplab.types.instance_config_types import InstanceConfig
from jobshoplab.types.state_types import JobState, OperationStateState
from jobshoplab.utils import solutions
from jobshoplab.utils.load_config import Config
from jobshoplab.utils.utils import get_id_int


# def test_env_end_to_end3x3_multi_discrete_conf0(multi_discrete_conf0):
#     instances = ["3x3", "ft06", "dmu35"]
#     dump_dir = Path("./tmp/tmp_heracless.py")

#     for instance in instances:
#         config = multi_discrete_conf0
#         # Change the spec instance from yaml config
#         config = replace(
#             config,
#             compiler=replace(
#                 config.compiler,
#                 spec_repository=replace(
#                     config.compiler.spec_repository, dir=f"data/jssp_instances/{instance}"
#                 ),
#             ),
#         )

#         env = JobShopLabEnv(config=config)
#         solution_file = f"data/jssp_instances/solutions/{instance}_sol"
#         solution_sequence = sorted(
#             tuple(solutions.make_solution_action_sequence(solution_file)),
#             key=lambda x: (x[2], x[1], x[0]),
#         )
#         makespann = solutions.get_make_span(solution_sequence, env.instance)
#         solution_sequence_by_time = solutions.group_by_time(solution_sequence)
#         num_jobs = len(env.instance.instance.specification)

#         for start_time, sequence in solution_sequence_by_time.items():
#             while env.state.state.time.time < start_time:
#                 observation, reward, terminated, truncated, _ = env.step(np.array([0] * num_jobs))

#             assert env.state.state.time.time == start_time

#             jobs = [job for _, job in sequence]
#             action = np.array([0] * num_jobs)

#             for job in jobs:
#                 action[job] = 1

#             observation, reward, terminated, truncated, _ = env.step(action)
#         assert env.state.state.time.time == makespann
#         assert terminated

#         # env.render(model)


def test_env_end_to_end3x3_conf0_with_solution_sequence(config_simple_3x3):
    dump_dir = Path("./tmp/tmp_heracless.py")

    env = JobShopLabEnv(config=config_simple_3x3)
    solution_file = "data/jssp_instances/solutions/3x3_sol"
    solution_sequence = sorted(
        tuple(solutions.make_solution_action_sequence(solution_file)),
        key=lambda x: (x[2], x[1], x[0]),
    )
    makespann = solutions.get_make_span(solution_sequence, env.instance)
    for machine, job, start_time in solution_sequence:
        while env.state.state.time.time < start_time:
            observation, reward, terminated, truncated, _ = env.step(0)
        job_done = False
        while not job_done:
            event = env.state.possible_transitions[0]
            if get_id_int(event.job_id) == job:
                assert env.state.state.time.time == start_time
                assert get_id_int(event.component_id) == machine
                observation, reward, terminated, truncated, _ = env.step(1)
                job_done = True
                # env.render()
                break
            else:
                observation, reward, terminated, truncated, _ = env.step(0)
    assert env.state.state.time.time == makespann
    assert terminated

    # env.render()


def test_env_end_to_end3x3_conf0_random_action(config_simple_3x3):
    dump_dir = Path("./tmp/tmp_heracless.py")

    env = JobShopLabEnv(config=config_simple_3x3)

    import random

    for _ in range(100):
        while not env.done:
            observation, reward, terminated, truncated, _ = env.step(random.randint(0, 1))

        assert terminated != truncated
        env.reset()


def test_jssp_transport_3x3_random_action(config_3x3_transport):
    dump_dir = Path("./tmp/tmp_heracless.py")

    env = JobShopLabEnv(config=config_3x3_transport)

    import random

    for _ in range(100):
        while not env.done:
            observation, reward, terminated, truncated, _ = env.step(random.randint(0, 1))

        assert terminated != truncated
        env.reset()


def test_env_end_to_end(config: Config):
    dump_dir = Path("./tmp/tmp_heracless.py")
    instance_dir = "data/jssp_instances/"
    solution_dir = "data/jssp_instances/solutions/"
    solution_names = os.listdir(solution_dir)[0:7] + ["3x3_sol", "ft06_sol", "ft10_sol"]
    instance_dirs = map(lambda x: Path(os.path.join(instance_dir, x.split("_")[0])), solution_names)
    solution_dirs = map(lambda x: Path(os.path.join(solution_dir, x)), solution_names)
    repos = map(lambda x: SpecRepository(x, loglevel="warning", config=config), instance_dirs)
    _compiler = map(lambda x: Compiler(config, loglevel="warning", repo=x), repos)
    envs = map(lambda x: JobShopLabEnv(config=config, compiler=x), _compiler)
    for env in envs:
        solution_file = next(solution_dirs)
        solution_sequence = sorted(
            tuple(solutions.make_solution_action_sequence(solution_file)),
            key=lambda x: (x[2], x[1], x[0]),
        )
        makespan = solutions.get_make_span(solution_sequence, env.instance)
        for machine, job, start_time in solution_sequence:
            while env.state.state.time.time < start_time:
                observation, reward, terminated, truncated, _ = env.step(0)
            job_done = False
            while not job_done:
                event = env.state.possible_transitions[0]
                if get_id_int(event.job_id) == job:
                    assert env.state.state.time.time == start_time
                    assert get_id_int(event.component_id) == machine
                    observation, reward, terminated, truncated, _ = env.step(1)
                    job_done = True
                    # env.render()
                    break
                else:
                    observation, reward, terminated, truncated, _ = env.step(0)
        assert env.state.state.time.time == makespan
        assert terminated

        # env.render()
