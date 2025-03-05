import os

import mermaid as md
from IPython.display import HTML, display
from mermaid.graph import Graph


def change_to_jobshoplab():
    target_dir = "jobshoplab"
    current_dir = os.getcwd()

    while True:
        if os.path.basename(current_dir) == target_dir:
            print(f"Already in the desired directory: {current_dir}")
            break
        elif target_dir in os.listdir(current_dir):
            os.chdir(os.path.join(current_dir, target_dir))
            print(f"Changed directory to: {os.getcwd()}")
            break
        else:
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached the root directory
                raise FileNotFoundError(
                    f"Directory '{target_dir}' not found in the directory tree."
                )
            current_dir = parent_dir
            os.chdir(current_dir)


def show_mermaid(dir):
    display(
        HTML(
            """
            <style>
            div.output_area {
                max-height: none !important;
                overflow-y: visible !important;
            }
            </style>
            """
        )
    )
    with open(dir, "r") as file:
        mdd_str = file.read()
    sequence = Graph("Sequence-diagram", mdd_str)
    return md.Mermaid(sequence)
