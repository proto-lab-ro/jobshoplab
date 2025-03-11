<div align="center">
    <img src="docs/assets/JobShopLabLogo.svg" alt="JobShopLab Logo" width="100"/>
</div>

# JobShopLab: A Scheduling Framework for Reinforcement Learning Under Real-World Constraints 
<p align="center">
    <a href="https://lbesson.mit-license.org/" alt="Backers on Open Collective">
        <img src="https://img.shields.io/badge/License-MIT-green.svg?logo=github" /></a>
</p>


JobShopLab is a flexible and modular framework designed to advance research and development in job shop scheduling using Reinforcement Learning (RL) techniques. It provides an adaptable Gym environment, enabling users to test and benchmark different scheduling algorithms under realistic constraints found in industrial settings.

## Features

- **Modular Gym Environment**: A customizable and extensible framework for testing diverse scheduling strategies and problem specifications.
- **Reinforcement Learning Ready**: Seamless integration with RL algorithms via the standard Gym Interface.
- **Real-World Constraints**: Incorporates transport logistics, buffer management, machine breakdowns, setup times, and stochastic processing conditions.
- **Multi-Objective Optimization**: Supports scheduling based on multiple objectives, such as makespan, energy efficiency, machine utilization, and lead time.
- **Pip Installable**: Easy installation from the repository, ensuring quick setup and integration into existing projects.

## Installation

> JobShopLab requires Python 3.12 or higher.


To install JobShopLab, clone the repository and install it in editable mode using `pip`.

```bash

cd <desired_dir>

# ssh
git clone git@github.com:proto-lab-ro/jobshoplab.git

# or https
git clone https://github.com/proto-lab-ro/jobshoplab.git

# install python module in edible mode
pip install -e <repo_dir>
```

Replace `<desired_dir>` with your target directory and `<repo_dir>` with the path to your local clone of the JobShopLab repository.

## Getting Started

After installation, you can initialize and interact with JobShopLab in your Python scripts as follows:

```python
from jobshoplab import JobShopLabEnv, load_config
from pathlib import Path

# Load a pre-defined configuration
config = load_config(config_path=Path("./data/config/getting_started_config.yaml"))

# Create the environment
env = JobShopLabEnv(config=config)

# Run with random actions until done
done = False
while not done:
    action = env.action_space.sample()
    obs, reward, truncated, terminated, info = env.step(action)
    done = truncated or terminated

# Visualize the final schedule
env.render()
```

We also provide a **Getting Started Jupyter Notebook** that walks you through the framework setup, environment interaction, and running basic reinforcement learning experiments. You can find this notebook in the repository under `jupyter/getting_started.ipynb`.

## Framework Overview

JobShopLab extends the classical Job Shop Scheduling Problem (JSSP) by considering real-world production constraints and enabling RL-based optimization. It provides a state-machine-based simulation model that includes:

- **Machines**: Modeled with setup times, breakdowns, and stochastic processing.
- **Transport Units**: Handling job movements between machines with delays and constraints.
- **Buffers**: Limited storage capacity impacting scheduling decisions.

## Experiments

To validate the framework, we trained an RL agent and compared its scheduling performance against traditional Priority Dispatch Rules (PDRs). Using the PPO algorithm from Stable Baselines3, the agent learned to optimize makespan efficiently. Compared to heuristic methods like Shortest Processing Time (SPT) and Most Work Remaining (MWKR), the RL-based approach achieves superior scheduling performance out of the box, in the standard academic cases and also with significantly increased complexity due to additional constraints such as buffer and transport constraints.

Academic instances found in Literature. Definitions can be found in `data/jssp_instances/*.yaml`

![RL vs. Heuristic Comparison](docs/assets/results_validation.svg)

| Instance | mwkr | spt  | lb   | rl |
| -------- | ---- | ---- | ---- | ---- |
| ft06     |      |      | 55   | 55   |
| ft10     |      |      | 930  | 981  |
| la16     | 1238 | 1588 | 945  | 978  |
| ta01     | 1786 | 1872 | 1231 | 1231 |
| ta41     | 2632 | 3067 | 2005 | 2496 |


> Note on RL Results: Results from individual hyperparameter optimizations 

**Extendet real-world constrains**

Academic instances with arbitrary transport times between machines
definitions can be found in 
`data/instances/jssptransport/*.yaml`

![RL vs. Heuristic Comparison for Real-World Instances](docs/assets/results_verification.svg)


| Instance | fifo| mwkr | spt | rl|
|---------|---------|---------|---------|---------|
| ft06-t  | 83      | 85      | 85      | 76      |
| ft10-t  | 1463    | 1286    | 1167    | 1061    |
| ft20-t  | 1714    | 1763    | 1790    | 1567    |
| la01-t  | 1200    | 1221    | 936     | 771     |
| la02-t  | 973     | 993     | 1023    | 782     |
| la03-t  | 971     | 1098    | 945     | 789     |
| la04-t  | 1122    | 1113    | 1113    | 828     |
| la05-t  | 784     | 851     | 776     | 681     |
| la06-t  | 1405    | 1366    | 1240    | 1112    |
| la07-t  | 1419    | 1332    | 1356    | 1127    |
| la08-t  | 1363    | 1337    | 1357    | 1143    |
| la09-t  | 1379    | 1403    | 1332    | 1120    |
| la10-t  | 1295    | 1205    | 1226    | 1044    |
| la11-t  | 1534    | 1689    | 1675    | 1409    |
| la12-t  | 1552    | 1638    | 1447    | 1248    |
| la13-t  | 1782    | 1599    | 1689    | 1400    |
| la14-t  | 2036    | 1954    | 1883    | 1712    |
| la15-t  | 1719    | 1752    | 1631    | 1512    |
| la16-t  | 1502    | 1634    | 1338    | 1186    |
| la17-t  | 1307    | 1318    | 1318    | 999     |
| la18-t  | 1226    | 1235    | 1261    | 1089    |
| la19-t  | 1147    | 1409    | 1129    | 1092    |
| la20-t  | 1476    | 1359    | 1195    | 1123    |
| la21-t  | 1675    | 1655    | 1575    | 1369    |
| la22-t  | 1637    | 1920    | 1499    | 1340    |
| la23-t  | 1617    | 1504    | 1450    | 1325    |
| la24-t  | 1774    | 1616    | 1620    | 1277    |

> Note on RL Results: Training was performed with one set of hyperparameter over all instances

## Testing

JobShopLab uses pytest for testing. The test suite includes unit tests, integration tests, and end-to-end tests.

To run the test suite:

```bash
# Run all tests
pytest

# Run tests with coverage report
./scripts/get_test_coverage.sh

# Run specific test categories
pytest tests/unit_tests/
pytest tests/integration_tests/
```

## Contributing

We welcome contributions to JobShopLab! If you have ideas for improvements or bug fixes, feel free to submit an issue, or pull request on our repository.

### How to Contribute

1. Fork the repository.
2. Create a new branch for your feature or fix.
3. Implement your changes and ensure they are well-documented.
4. Submit a pull request with a detailed explanation of your modifications.
