"""
str_format.py

Parse format strings

    - Author: HP (2026)
"""
import re
import numpy as np
import matplotlib as mpl


def unpack_plot_args(args, default_fmt: str = "k-"):
    """ Unpack the first args in the .plot() call into x, y and fmt (marker format) """
    if len(args) == 3:
        # Plot X and Y data with given format string
        x, y, fmt = args
    elif len(args) == 2:
        if isinstance(args[-1], str):
            # Plot Y data with X = index
            y, fmt = args
            if not isinstance(y, (list, tuple, np.ndarray)):
                y = [y]
            x = np.arange(0, len(y), 1)
        else:
            x, y = args
            fmt = default_fmt
    elif len(args) == 1:
        if isinstance(args[0], str):
            # Plot single point (no data specified)
            x, y = 0, 0
        else:
            # Plot y data with X = index and default format
            y = args[0]
            if isinstance(y, (list, tuple, np.ndarray)):
                x = np.arange(0, len(y), 1)
            else:
                # Single y value plotted
                x = y
        fmt = default_fmt

    return x, y, fmt


def parse_arrow_fmt(fmt: str) -> str:
    """
    Parse a format (`fmt`) string containing the custom '->' format type
    into a string understood by matplotlib plotting methods
    """
    base_colors = list(mpl.colors.BASE_COLORS.keys())
    match = re.search(rf"[{''.join(base_colors)}]", fmt)
    color = ""
    if match is not None:
        color = match.group(0)
    base_markers = [
        m for m in mpl.markers.MarkerStyle.markers.keys()
        if m not in ("None", "none", " ", "")
    ]
    match = re.search(
        rf"[{''.join([str(i) for i in base_markers])}]",
        fmt
    )
    marker = "x"
    if match is not None:
        marker = match.group(0)
    
    fmt = f"{color}{marker}" # Remove '-' from fmt
    return color, fmt
