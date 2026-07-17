"""
saving.py

Functions related to saving Figures

    - Author: HP (2026)
"""
import pickle


def save_figure(fig, filename: str = "figure"):
    """
    Save this Figure's fig attribute as interactive file

    TODO: this currently relies on pickle. Must transition to
    custom format for maximum compatibility
    """
    if not filename.endswith(".pltex"):
        filename += ".pltex"
    with open(filename, "wb") as f:
        pickle.dump(fig, f)
