import os

import mermaid as md
from IPython.display import HTML, display
from mermaid.graph import Graph


def change_to_jobshoplab():
    target_dir_content = "pyproject.toml"
    current_dir = os.getcwd()

    while True:
        if current_dir == "/":
            raise Exception("Repository root not found - reached system root")
        if target_dir_content in os.listdir(current_dir):
            print(f"Already in the desired directory: {current_dir}")
            break
        elif target_dir_content not in os.listdir(current_dir):
            os.chdir("..")
            current_dir = os.getcwd()


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
