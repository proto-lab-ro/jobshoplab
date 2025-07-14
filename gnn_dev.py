import os
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.distributions import CategoricalDistribution
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from torch_geometric.data import Data
from torch_geometric.nn import GINConv, aggr, global_mean_pool

from jobshoplab import JobShopLabEnv, load_config

MAX_NODES = 60  # Set this higher than any instance in your dataset
MAX_EDGES = 300  # Approximate upper bound on edge count
MAX_ELIGIBLE = 10  # Max eligible ops (usually ≤ num_jobs)
NUM_NODE_FEATURES = 6


class GINEncoder(nn.Module):
    """
    Graph Isomorphism Network (GIN) Encoder for node representation learning.

    Parameters
    ----------
    input_dim : int
        Number of input features per node.
    hidden_dim : int
        Number of hidden units per GIN layer and output embedding size.
    k_layers : int
        Number of GIN layers to use.

    Attributes
    ----------
    convs : nn.ModuleList
        List of GINConv layers, each implemented as a small MLP (2-layer MLP with ReLU).
    """

    def __init__(self, input_dim, hidden_dim, k_layers):
        super().__init__()
        self.convs = nn.ModuleList(
            [
                GINConv(
                    nn.Sequential(
                        nn.Linear(input_dim if i == 0 else hidden_dim, hidden_dim),
                        nn.ReLU(),
                        nn.Linear(hidden_dim, hidden_dim),
                    )
                )
                for i in range(k_layers)
            ]
        )

    def forward(self, x, edge_index):
        """
        Forward pass: applies K layers of GIN convolution to the input node features.

        Parameters
        ----------
        x : torch.Tensor
            Node features of shape (num_nodes, input_dim).
        edge_index : torch.LongTensor
            Graph connectivity in COO format, shape (2, num_edges).

        Returns
        -------
        torch.Tensor
            Node embeddings of shape (num_nodes, hidden_dim).
        """
        for conv in self.convs:
            x = conv(x, edge_index)
        return x  # node embeddings


class GNNFeatureExtractor(BaseFeaturesExtractor):
    """
    Extracts graph feature using a GINEncoder.
    Produces:
    - graph_emb: pooled graph representation (for value)
    - eligible_embs: (num_eligible, embed_dim) (for policy logits)
    """

    def __init__(
        self,
        observation_space,
        input_dim=64,
        hidden_dim=32,
        k_layers=1,
        # op_node_id,
        pooling="max",
    ):
        super().__init__(observation_space, features_dim=hidden_dim)
        self.gnn = GINEncoder(input_dim, hidden_dim, k_layers)
        self.hidden_dim = hidden_dim
        self.pooling = pooling
        # self.op_node_id = op_node_id
        # self.aggregate = aggr.MeanAggregation()
        self.aggregate = global_mean_pool

    def forward(self, observations):
        # observations is a dict of np arrays (from GraphEnv)
        # Convert to tensors if needed
        device = next(self.parameters()).device

        node_feats = observations["x"]
        edge_index = observations["edge_index"]
        edge_index = edge_index.to(torch.int64)

        X = self.gnn(node_feats, edge_index)  # [current_node, hidden_dim]

        graph_emb = self.aggregate(X, batch=observations["batch"])

        return X, graph_emb


log_dir = "./logs/"
save_dir = "./best_model/"


if __name__ == "__main__":
    config = load_config(config_path=Path("./data/config/config_gnn_classic_jssp.yaml"))
    env = JobShopLabEnv(config=config)

    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(save_dir, exist_ok=True)

    features_extractor_kwargs = dict(
        input_dim=NUM_NODE_FEATURES,
        hidden_dim=64,
        k_layers=1,
        # op_node_id=g_env.op_node_id,
        # observation_space = g_env.observation_space,
    )
    policy_kwargs = dict(
        features_extractor_class=GNNFeatureExtractor,
        features_extractor_kwargs=features_extractor_kwargs,
    )
    model = PPO(
        "GraphInputPolicy",
        env,
        policy_kwargs=policy_kwargs,
        learning_rate=1e-4,
        verbose=1,
        batch_size=32,
        tensorboard_log=log_dir,
    )

    eval_callback = EvalCallback(
        env,
        best_model_save_path=save_dir,
        log_path=log_dir,
        eval_freq=1000,  # Adjust evaluation frequency as needed
        deterministic=False,  # TODO: error when True -> IndexError: Dimension out of range (expected to be in range of [-1, 0], but got 1)
        render=False,
    )

    model.learn(callback=eval_callback, total_timesteps=100000, tb_log_name="GNN_PPO")
