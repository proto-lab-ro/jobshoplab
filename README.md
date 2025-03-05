<div align="center">
    <img src="docs/assets/JobShopLabLogo.svg" alt="JobShopLab Logo" width="100"/>
</div>

# JobShopLab: A Scheduling Framework for Reinforcement Learning Under Real-World Constraints
<!-- 
<p align="center">
    <a href="https://lbesson.mit-license.org/" alt="Backers on Open Collective">
        <img src="https://img.shields.io/badge/License-MIT-green.svg?logo=github" /></a>
    <!-- <a href="https://shields.io/community#sponsors" alt="Sponsors on Open Collective">
        <img src="https://img.shields.io/opencollective/sponsors/shields" /></a>
    <a href="https://github.com/badges/shields/pulse" alt="Activity">
        <img src="https://img.shields.io/github/commit-activity/m/badges/shields" /></a>
    <a href="https://github.com/badges/shields/discussions" alt="Discussions">
        <img src="https://img.shields.io/github/discussions/badges/shields" /></a>
    <a href="https://github.com/badges/shields/actions/workflows/daily-tests.yml">
        <img src="https://img.shields.io/github/actions/workflow/status/badges/shields/daily-tests.yml?label=daily%20tests"
            alt="Daily Tests Status"></a>
    <a href="https://coveralls.io/github/badges/shields">
        <img src="https://img.shields.io/coveralls/github/badges/shields"
            alt="Code Coverage"></a>
    <a href="https://discord.gg/HjJCwm5">
        <img src="https://img.shields.io/discord/308323056592486420?logo=discord&logoColor=white"
            alt="Chat on Discord"></a> -->
</p>


JobShopLab is a flexible and modular framework designed to advance research and development in job shop scheduling using Reinforcement Learning (RL) techniques. It provides an adaptable gym environment, enabling users to test and benchmark different scheduling algorithms under realistic constraints found in industrial settings. -->

To validate the framework, we trained an RL agent and compared its scheduling performance against traditional Priority Dispatch Rules (PDRs). Using the PPO algorithm from Stable Baselines3, the agent learned to optimize makespan efficiently. Compared to heuristic methods like SPT and MWKR, the RL-based approach achieved superior scheduling performance, even under additional constraints like buffer and transport limitations.

## Features

- **Modular Gym Environment**: A customizable and extensible framework for testing diverse scheduling strategies and problem specifications.
- **Reinforcement Learning Ready**: Seamless integration with RL algorithms via the standard Gym Interface.
- **Real-World Constraints**: Incorporates transport logistics, buffer management, machine breakdowns, setup times, and stochastic processing conditions.
- **Multi-Objective Optimization**: Supports scheduling based on multiple objectives, such as makespan, energy efficiency, machine utilization, and lead time.
- **Pip Installable**: Easy installation from the repository, ensuring quick setup and integration into existing projects.

## Installation

To install JobShopLab, clone the repository and install it in editable mode using `pip`. It is recommended to use a venv.

```bash

cd <desired_dir>

# ssh
git clone git@inf-git.fh-rosenheim.de:proto-lab-2.0/jobshopagents.git !# TODO Change url

# or https
git clone https://inf-git.fh-rosenheim.de/proto-lab-2.0/jobshoplab.git !# TODO Change url

# activate venv
source <venv-activate>

# install from source
pip install -e <repo_dir>
```

Replace `<desired_dir>` with your target directory, `<venv-activate>` with the path to your virtual environment activation script, and `<repo_dir>` with the path to your local clone of the JobShopLab repository.

## Getting Started

After installation, you can initialize and interact with JobShopLab in your Python scripts as follows:

```python

from jobshoplab import JobShopEnv

# Initialize the environment
env = JobShopEnv()

# Your code to interact with the environment goes here

```

We also provide a **Getting Started Jupyter Notebook** that walks you through the framework setup, environment interaction, and running basic reinforcement learning experiments. You can find this notebook in the repository under `jupyter/getting_started.ipynb`.

## Framework Overview

JobShopLab extends the classical Job Shop Scheduling Problem (JSSP) by integrating real-world production constraints and enabling RL-based optimization. It provides a state-machine-based simulation model that includes:

- **Machines**: Modeled with setup times, breakdowns, and stochastic processing.
- **Transport Units**: Handling job movements between machines with delays and constraints.
- **Buffers**: Limited storage capacity impacting scheduling decisions.
- **Multi-Agent Interaction**: Supporting decision-making across various production elements.

### Reinforcement Learning Integration

JobShopLab is designed to work seamlessly with RL algorithms. It supports:

- **Custom Observation Spaces**: Define what state information is available to the RL agent.
- **Flexible Action Spaces**: Allowing discrete and continuous decision-making strategies.
- **Custom Reward Functions**: Adaptable to different optimization goals (e.g., reducing makespan, minimizing energy consumption).


## Experiments

**Definitions:** <br>
- **Instance** Problem solved<br>
- **fifo** First in First out Dispatching rule <br>
- **mwkr**  <br>
- **rl** Reinforcement Learning<br>
- **lb** known LowerBound <br>

### Academic
Academic instances found in Literature. Definitions can be found in `data/jssp_instances/*.yaml`


| Instance | fifo| mwkr | spt | rl| lb|
|---------|---------|---------|---------|---------|---------|
| ft06    | 83      | 85      | 85      | 76      |

> Note on RL Results: results from Hyperparameter Optimizations 

### Transport
*Academic instances with arbitrary transport times between machines
definitions can be found in 
`data/instances/jssptransport/*.yaml`
| Instance | fifo| mwkr | spt | rl|
|---------|---------|---------|---------|---------|
| ft06    | 83      | 85      | 85      | 76      |
| ft10    | 1463    | 1286    | 1167    | 1061    |
| ft20    | 1714    | 1763    | 1790    | 1567    |
| la01    | 1200    | 1221    | 936     | 771     |
| la02    | 973     | 993     | 1023    | 782     |
| la03    | 971     | 1098    | 945     | 789     |
| la04    | 1122    | 1113    | 1113    | 828     |
| la05    | 784     | 851     | 776     | 681     |
| la06    | 1405    | 1366    | 1240    | 1112    |
| la07    | 1419    | 1332    | 1356    | 1127    |
| la08    | 1363    | 1337    | 1357    | 1143    |
| la09    | 1379    | 1403    | 1332    | 1120    |
| la10    | 1295    | 1205    | 1226    | 1044    |
| la11    | 1534    | 1689    | 1675    | 1409    |
| la12    | 1552    | 1638    | 1447    | 1248    |
| la13    | 1782    | 1599    | 1689    | 1400    |
| la14    | 2036    | 1954    | 1883    | 1712    |
| la15    | 1719    | 1752    | 1631    | 1512    |
| la16    | 1502    | 1634    | 1338    | 1186    |
| la17    | 1307    | 1318    | 1318    | 999     |
| la18    | 1226    | 1235    | 1261    | 1089    |
| la19    | 1147    | 1409    | 1129    | 1092    |
| la20    | 1476    | 1359    | 1195    | 1123    |
| la21    | 1675    | 1655    | 1575    | 1369    |
| la22    | 1637    | 1920    | 1499    | 1340    |
| la23    | 1617    | 1504    | 1450    | 1325    |
| la24    | 1774    | 1616    | 1620    | 1277    |

> Note on RL Results: training was performed with one set of Hyperparameter over different random

## Contributing

We welcome contributions to JobShopLab! If you have ideas for improvements or bug fixes, feel free to submit an issue or pull request on our repository.

### How to Contribute

1. Fork the repository.
2. Create a new branch for your feature or fix.
3. Implement your changes and ensure they are well-documented.
4. Submit a pull request with a detailed explanation of your modifications.
