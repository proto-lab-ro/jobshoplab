from functools import partial

import matplotlib.pyplot as plt
import networkx as nx

from jobshoplab.state_machine.core.transitions import (BufferTransition,
                                                       MachineTransition,
                                                       TransportTransition)


def render_state_transitions(config, loglevel, backend):
    """
    Render the state transitions.

    Args:
        config (Config): The configuration object.
        loglevel (int | str): The log level
        backend (callable): The backend to use for rendering.
    """
    graph = []

    fig, axs = plt.subplots(1, 3, figsize=(15, 5))

    for i, transition in enumerate(
        [BufferTransition(), TransportTransition(), MachineTransition()]
    ):
        G = nx.DiGraph()
        for node in transition.states:
            G.add_node(node, label=node)  # Add node with label
            _trans = transition.transitions[node]
            for edge in _trans:
                G.add_edge(node, edge, label=edge)  # Add edge with label

        pos = nx.circular_layout(G)  # Set the positions of the nodes

        nx.draw_networkx_nodes(
            G, pos, node_size=1000, ax=axs[i], node_color="white", edgecolors="black"
        )
        nx.draw_networkx_edges(
            G,
            pos,
            ax=axs[i],
            edge_color="black",
            arrows=True,
            arrowsize=10,
            min_source_margin=20,  # Adjust the value to make self-loops smaller
            min_target_margin=20,  # Adjust the value to make self-loops smaller
            connectionstyle="arc3,rad=0",
        )  # Show arrow heads
        nx.draw_networkx_labels(
            G,
            pos,
            labels=nx.get_node_attributes(G, "label"),
            ax=axs[i],
            font_color="black",
            font_size=8,
            font_weight="bold",
            verticalalignment="center",
        )  # Add node labels
        axs[i].set_title(transition.__class__.__name__)

    plt.tight_layout()
    backend(config=config, loglevel=loglevel, fig=fig)


if __name__ == "__main__":
    from jobshoplab.env.rendering.backends import save_to_file

    config = load_config()
    args = {"instance": None, "name": "state_transition_graph_representation"}
    backend = partial(save_to_file, **args)
    render_state_transitions(config, 0, backend=backend)
