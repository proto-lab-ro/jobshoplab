from collections import defaultdict

import numpy as np

from jobshoplab.types.instance_config_types import InstanceConfig
from jobshoplab.utils.utils import get_id_int


def make_solution_action_sequence(dir):
    """
    Create a solution action sequence.
    This function reads a file from the specified directory, processes its contents,
    and returns a tuple containing the machine, job, and start_time in each row.
    Args:
        dir (str): The directory path to the file containing the solution data.
    Returns:
        tuple: A tuple containing the machine, job, and start_time sequences.
    """
    sol_arr = []
    with open(dir, "r") as file:
        for line in file:
            line = line.split("\n")[0]
            sol_arr.append([int(_str_num) for _str_num in line.split(" ")])
    return tuple(get_machine_job_time_sequence(sol_arr))


def group_by_time(tuples):
    """
    Groups a list of tuples by their start time.
    Args:
        tuples (list of tuple): A list where each tuple contains three elements:
            - machine: The machine identifier.
            - job: The job identifier.
            - start_time: The start time of the job on the machine.
    Returns:
        dict: A dictionary where the keys are start times and the values are lists of tuples,
              each containing a machine and a job that start at that time.
              start_time = [(machine, job), ...]

    """
    grouped = defaultdict(list)

    # Loop through each tuple in the input
    for machine, job, start_time in tuples:
        # Group by start_time
        grouped[start_time].append((machine, job))

    return dict(grouped)


def get_machine_job_time_sequence(sol_arr):
    """
    Generator function that yields the machine-job-time sequence from a given solution array.
    Args:
        sol_arr (list of list of float): A 2D list where each sublist represents a job and each element in the sublist
                                         represents the time required on a specific machine.
    Yields:
        tuple: A tuple containing the best machine index, best job index, and the lowest time found in the current iteration.
               The best machine and job are the ones with the lowest processing time that hasn't been processed yet.

    """
    lowest_time = np.inf
    best_machine = None
    best_job = None
    while not all(r == None for c in sol_arr for r in c):
        for job, line in enumerate(sol_arr):
            for machine, time in enumerate(line):
                if time != None:
                    if time < lowest_time:
                        lowest_time = time
                        best_machine = machine
                        best_job = job
                        break
        yield (best_machine, best_job, lowest_time)
        sol_arr[best_job][best_machine] = None
        lowest_time = np.inf
        best_machine, best_job = None, None


def get_make_span(sol_seq, instance: InstanceConfig) -> int:
    """
    Calculate the makespan (total completion time) for a solution sequence.

    The makespan is the maximum end time of all last operations across all jobs.
    For each job's last operation, find its corresponding entry in the solution
    sequence, calculate its end time, and return the maximum end time.

    Args:
        sol_seq: Solution sequence with tuples of (machine, job, start_time)
        instance: Instance configuration with job specifications

    Returns:
        int: The makespan (maximum completion time) of the solution
    """
    # best_machine, best_job, lowest_time
    sol_seq = list(sol_seq)
    last_operations = [(job.operations[-1], job.id) for job in instance.instance.specification]
    machine_end_times = []
    # for every last operation of a job, find the matching sol_seq operation and calculate the end time
    for op, job_id in last_operations:
        for sol_el in sol_seq[::-1]:
            if get_id_int(op.machine) == sol_el[0] and get_id_int(job_id) == sol_el[1]:
                machine_end_times.append(sol_el[2] + int(op.duration.duration))

    return max(machine_end_times)
