"""
easy_plot.py

Matplotlib wrapper for easier and cleaner plot scripting

    - Author: Henry Pickersgill (2026)
"""

import re
from pathlib import Path
from typing import get_args
import pickle

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
import scipy as sp

from easy_plot.types import SPINE, SPINES, LabelCfg


class Figure():
    all_figs = []
    visible_figs = []

    def __init__(
        self,
        title: str = "",
        grid_on: bool = True,
        grid_ls = "--",
        grid_lw = 0.5,
        legend_on: bool = False,
        nrows: int = 1,
        ncols: int = 1,
        figsize: tuple[int] = (12, 8),
        default_label_fsize: int = 10,
        default_legend_fsize: int = 10,
        default_legend_alpha: float = 1.0
    ):
        self.fig, self.axes = plt.subplots(figsize=figsize, nrows=nrows, ncols=ncols)
        self.nrows, self.ncols = nrows, ncols
        self.multi_plot: bool = nrows > 1 or ncols > 1
        self.np, self.pd, self.sp, self.plt = self.plt = np, pd, sp, plt

        self.title = title
        if self.multi_plot:
            self.fig.suptitle(self.title, y=0.95)
        else:
            self.axes.set_title(self.title)

        # Grid and legend config
        axes = self.axes
        if not self.multi_plot:
            axes = [self.axes]

        if grid_on:
            if nrows > 1 or ncols > 1:
                # Flatten 2D array for loop
                axes = axes.flatten()
            for ax in axes:
                if grid_on:
                    ax.grid(ls=grid_ls, lw=grid_lw)

        self.legend_on = legend_on
        self.legends = []

        # Keep track of this instance in the class attribute `all_figs`
        self.all_figs.append(self)

        # For controlling daughter Figures.
        # (Click events can be configured to plot data on another figure)
        self.has_daughter = False
        self.daughter = None

        # Default parameters
        self.default_label_fsize = default_label_fsize
        self.default_fmt = "kx"
        self.default_legend_fsize = default_legend_fsize
        self.default_legend_alpha = default_legend_alpha


    ### Plotting methods
    def plot(
        self,
        *args, # x, y, fmt
        mfc: str | None = "none",
        mec: str | None = None,
        xlabel: str | dict | LabelCfg | None = None,
        ylabel: str | dict | LabelCfg | None = None,
        row_idx: int = 0,
        col_idx: int = 0,
        xticklabel_fontsize: int | None = None,
        yticklabel_fontsize: int | None = None,
        plot_type: str = "plot",
        connect_data: dict | None = None,
        legend_alpha: float | None = None,
        **kwargs
    ):
        """ Add data to the axes """
        ax = self._getAx(row_idx, col_idx)

        x, y, fmt = self._unpack_plot_args(args)
        arrows = False
        if "->" in fmt[1:]:
            # Custom arrow format found
            # colour = re.search(r"[]")
            fmt_color, fmt = self._parse_arrow_fmt(fmt)
            arrows = True

        # Only create connected daughter Figure for plots of singular points
        create_daughter = self._shouldCreateDaughter(x, y, connect_data)

        if self.daughter is not None:
            kwargs["picker"] = 5 # 5 point click radius

        if create_daughter:
            self.has_daughter = True
            self._createDaughter()

        # Execute plot method
        if plot_type == "plot":
            kwargs["markeredgecolor"] = mec
            kwargs["markerfacecolor"] = mfc
            point, = ax.plot(x, y, fmt, **kwargs)

            if arrows:
                color = fmt_color
                if not fmt_color:
                    # No color present in fmt string
                    color = point.get_color()
                self._draw_arrows(ax, x, y, color=color)

            # Connect click event to daughter Figure
            if self.daughter is not None:
                self._connectToDaughter(connect_data, point)

        elif plot_type == "bar":
            ax.bar(x, y, **kwargs)

        # Extract label fontsizes if given
        axis_labels = {}
        for name, lab_obj in (
            ("x", xlabel),
            ("y", ylabel)
        ):
            if isinstance(lab_obj, LabelCfg):
                pass
            elif isinstance(lab_obj, dict):
                lab_obj = LabelCfg(
                    lab_obj.get("label", name),
                    lab_obj.get("fontsize", self.default_label_fsize)
                )
            elif isinstance(lab_obj, str):
                lab_obj = LabelCfg(lab_obj, self.default_label_fsize)
            elif lab_obj is None:
                attr_label = getattr(self, f"{name}label", None)
                if attr_label:
                    lab_obj = LabelCfg(attr_label, self.default_label_fsize)
                else:
                    axis_labels[name] = None
            else:
                raise TypeError(
                    f"Unexpected type for {name}label. Expected str | dict | LabelCfg but got {type(lab_obj)}"
                )

            if lab_obj is not None:
                lab = getattr(lab_obj, "label", name)
                fsize = getattr(lab_obj, "fontsize", self.default_label_fsize)

                axis_labels[name] = {
                    "label": lab, "fontsize": fsize
                }

        if axis_labels["x"] is not None:
            ax.set_xlabel(axis_labels["x"]["label"], fontsize=axis_labels["x"]["fontsize"])
        if axis_labels["y"] is not None:
            ax.set_ylabel(axis_labels["y"]["label"], fontsize=axis_labels["y"]["fontsize"])

        if xticklabel_fontsize is not None:
            ax.tick_params(axis="x", which="major", labelsize=xticklabel_fontsize)
        if yticklabel_fontsize is not None:
            ax.tick_params(axis="y", which="major", labelsize=yticklabel_fontsize)

        if self.legend_on:
            ax.legend(
                fontsize=self.default_legend_fsize,
                framealpha=legend_alpha or self.default_legend_alpha
            )


    def scatter(self, *args, **kwargs):
        """ Create a scatter plot. Interface directly to self.plot """
        return self.plot(*args, **kwargs)


    def bar(self, *args, colour: str | tuple | list | None = None, **kwargs):
        """ Create a bar chart. Interface to self.plot """
        x, y, fmt = self._unpack_plot_args(args)

        if colour is None:
            if not kwargs.get("color"):
                # Get colour from format string if not specified elsewhere
                kwargs["color"] = fmt[0]
        else:
            if isinstance(colour, (list, tuple, np.ndarray)):
                ncols, ndata = len(colour), len(x)
                if ncols > 1:
                    if ncols != ndata:
                        print(
                            f"Length of 'colour' did not match length of data ({ncols} != {ndata}). "\
                            f"Setting colour to first colour value, '{colour[0]}'"
                        )
                        colour = colour[0]

            elif isinstance(colour, str):
                if not colour.startswith("#"):
                    # Colour is a string of multiple letters
                    colour = [c for c in colour]

            kwargs["color"] = colour


        kwargs["zorder"] = 9999 # Always draw bars on top of grid
        return self.plot(x, y, **kwargs, plot_type="bar")


    def hline(
        self,
        y,
        xmin: int = 0,
        xmax: int = 0,
        row_idx: int = 0,
        col_idx: int = 0,
        colour: str = "k",
        linestyle: str = "--",
        linewidth: float = 1.0,
        **kwargs
    ):
        """ Draw a horizontal line spanning a given range. Defaults to full range """
        ax = self._getAx(row_idx, col_idx)
        kwargs["color"] = colour
        kwargs["linestyle"] = linestyle
        kwargs["linewidth"] = linewidth
        ax.axhline(y, xmin=xmin, xmax=xmax, **kwargs)


    def vline(
        self,
        x,
        ymin: int = 0,
        ymax: int = 0,
        row_idx: int = 0,
        col_idx: int = 0,
        colour: str = "k",
        linestyle: str = "--",
        linewidth: float = 1.0,
        **kwargs
    ):
        """ Draw a vertical line spanning a given range. Defaults to full range """
        ax = self._getAx(row_idx, col_idx)
        kwargs["color"] = colour
        kwargs["linestyle"] = linestyle
        kwargs["linewidth"] = linewidth
        ax.axvline(x, ymin=ymin, ymax=ymax, **kwargs)


    def hline_full(self, y, row_idx: int = 0, col_idx: int = 0, **kwargs):
        """ Draw a horizontal line spanning the full width of the given axis """
        return self.hline(y, xmin=0, xmax=1, row_idx=row_idx, col_idx=col_idx, **kwargs)


    def vline_full(self, x, row_idx: int = 0, col_idx: int = 0, **kwargs):
        """ Draw a vertical line spanning the full height of the given axis """
        return self.vline(x, ymin=0, ymax=1, row_idx=row_idx, col_idx=col_idx, **kwargs)



    ### Text handling
    def legend(
        self,
        loc = "best",
        row_idx: int = 0,
        col_idx: int = 0,
        all_axes: bool = False,
        legend_alpha: float = 1.0,
        fontsize: int | None = None
    ):
        """ Create a legend on a given axis """
        if all_axes:
            # Create a legend on all the available axes
            axes = [self.axes] if not self.multi_plot else self.axes
        else:
            # Create a legend on specified axis only
            ax = self._getAx(row_idx, col_idx)
            axes = [ax] # Iterable for below loop

        self.legends = []
        for ax in axes:
            leg = ax.legend(
                loc=loc,
                framealpha=legend_alpha,
                fontsize=fontsize or self.default_legend_fsize
            )
            self.legends.append(leg)


    def add_text(
        self,
        pos,
        text,
        row_idx: int = 0,
        col_idx: int = 0,
        box: bool = False,
        box_border_colour: str = None,
        box_face_colour: str = None,
        box_alpha: float = None,
        fontsize: int = 12,
        **kwargs
    ) -> None:
        """ Add text to a given axes object """
        ax = self._getAx(row_idx, col_idx)

        bbox = kwargs.get("bbox")
        if bbox is None:
            bbox = None
            if box or any(val is not None for val in (box_border_colour, box_face_colour, box_alpha)):
                if box_border_colour is None:
                    box_border_colour = "black"
                if box_face_colour is None:
                    box_face_colour = "white"
                if box_alpha is None:
                    box_alpha = 1.0
                bbox = {
                    "edgecolor": box_border_colour,
                    "facecolor": box_face_colour,
                    "alpha"    : box_alpha
                }
        else:
            # Passing in bbox directly overrides custom parameters
            kwargs.pop("bbox")

        x, y = pos
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        if not xmin <= x <= xmax:
            xmid = 0.5 * (xmin + xmax)
            x = xmid
            print(f"add_text --> text X coordinate out of axis range! Setting x to {xmid:.1f}")
        if not ymin <= y <= ymax:
            ymid = 0.5 * (ymin + ymax)
            y = ymid
            print(f"add_text --> text Y coordinate out of axis range! Setting y to {ymid:.1f}")

        # High zorder to force matplotlib to paint textbox on top of grid lines and data
        ax.text(x, y, text, fontsize=fontsize, bbox=bbox, zorder=99999, **kwargs)


    def add_textbox(self, *args, **kwargs):
        """ Interface to add_text to also force drawing of bounding box """
        kwargs["box"] = True
        self.add_text(*args, **kwargs)


    def set_axis_spine_colour(
        self,
        colour: str,
        all: bool = True,
        spines: SPINES | None = None,
        row_idx: int = 0,
        col_idx: int = 0
    ):
        """ Set the colour of one or more spines of the figure """
        ax = self._getAx(row_idx, col_idx)
        all_spines = set(get_args(SPINE)) # Get a set of all valid spine names
        if all:
            spines = all_spines
        else:
            if spines is None:
                spines = all_spines
            else:
                if any(spine not in all_spines for spine in spines):
                    raise ValueError(f"Unrecognised spine! Spines must be any set of {all_spines}")

        for spine in spines:
            ax.spines[spine].set_color(colour)


    def set_xlabel(self, xlabel):
        """ Interface to ax.set_xlabel. Also stores xlabel in self.xlabel. TODO: functionality for multi plots """
        self.xlabel = xlabel
        self.axes.set_xlabel(xlabel)


    def set_ylabel(self, ylabel):
        """ Interface to ax.set_ylabel. Also stores ylabel in self.ylabel. TODO: functionality for multi plots  """
        self.ylabel = ylabel
        self.axes.set_ylabel(ylabel)


    def remove_legend(self, row_idx: int = 0, col_idx: int = 0):
        """ TODO: fix for row AND col index """
        if self.legends:
            ax = self._getAx(row_idx, col_idx)
            ax.get_legend().remove()


    def tight_layout(self, *args, **kwargs): return self.fig.tight_layout(*args, **kwargs)
    def suptitle(self, *args, **kwargs): return self.fig.suptitle(*args, **kwargs)


    ### Methods for showing plots to user
    def show(self):
        """ Show only this object's figure by marking this instance as visible """
        self.visible_figs.append(self)
        if self.has_daughter:
            self.visible_figs.append(self.daughter)


    @classmethod
    def display(cls):
        """ Show all figures that have been marked as visible with individual calls to self.show() """
        if cls.visible_figs:
            to_show_figs = cls.visible_figs
        else:
            # No figures were marked as visible by calling .show(). Therefore, show all figs
            to_show_figs = cls.all_figs

        to_show_figs = [f.fig for f in to_show_figs] # Unpack internal mpl figure object
        for fignum in plt.get_fignums():
            fig = plt.figure(fignum)
            if fig not in to_show_figs:
                plt.close(fig)

        # Final call to show plots to user. Note that if .show() was not called,
        # any given plot will be permanently closed unless explicitly opened again.
        # However, if no figs called .show(), all figs will be shown
        plt.show()


    def save_interactive(self, filename: str | Path = "figure"):
        """
        Save this Figure's fig attribute as interactive file

        TODO: this currently relies on pickle. Must transition to
        custom format for maximum compatibility
        """
        if not filename.endswith(".eplot"):
            filename += ".eplot"
        with open(filename, "wb") as f:
            pickle.dump(self.fig, f)


    ### PRIVATE METHODS
    def _unpack_plot_args(self, args):
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
                fmt = self.default_fmt
        elif len(args) == 1:
            if isinstance(args[0], str):
                # Plot single point (no data specified)
                x, y = 0, 0
            else:
                # Plot y data with X = index and default format
                y = args[0]
                if isinstance(y, (list, tuple, np.ndarray)):
                    x = np.arange(0, len(y) + 1, 1)
                else:
                    # Single y value plotted
                    x = y
            fmt = self.default_fmt

        return x, y, fmt


    def _parse_arrow_fmt(self, fmt) -> str:
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


    def _draw_arrows(self, ax, x, y, color) -> None:
        """ Draw arrows connecting points if '->' marker fmt was specified """
        for k in range(0, len(x) - 1):
            ax.annotate(
                "",
                xy=(x[k + 1], y[k + 1]),
                xytext=(x[k], y[k]),
                arrowprops=dict(
                    arrowstyle="->",
                    color=color,
                    lw=1,
                ),
            )


    def _getAx(self, row_idx: int, col_idx: int) -> mpl.axes.Axes:
        """ Get a single Axes object given row and column indices """
        if self.multi_plot:
            if self.nrows == 1:
                ax = self.axes[col_idx]
            elif self.ncols == 1:
                ax = self.axes[row_idx]
            else:
                ax = self.axes[row_idx][col_idx]
        else:
            ax = self.axes

        return ax


    ### Daughter plot handling
    def _shouldCreateDaughter(self, x, y, connect_data: dict) -> bool:
        """ Determine whether a daughter Figure should be created or not """
        if self.daughter is None:
            if connect_data is not None:
                for data in (x, y):
                    if isinstance(data, (np.ndarray, list, tuple)):
                        return False
                return True
        return False


    def _createDaughter(self) -> None:
        """ Create a daughter Figure connected to this instance """
        self.daughter = Figure(figsize=(6, 3))
        btn_pos = self.daughter.fig.add_axes([0.75, 0.92, 0.15, 0.075])
        self.daughter.clear_btn = mpl.widgets.Button(btn_pos, "Clear data")
        self.daughter.clear_btn.label.set_fontsize(10)

        def on_click(_):
            for artist in list(self.daughter.axes.lines):
                artist.remove()
            for artist in list(self.daughter.axes.collections):
                artist.remove()
            self.daughter.fig.canvas.draw_idle()

        self.daughter.clear_btn.on_clicked(on_click)


    def _connectToDaughter(self, connect_data: dict, point: mpl.lines.Line2D) -> bool:
        """ Connect this Figure to a daughter Figure with the given data """
        x, y = connect_data.get("x"), connect_data.get("y")
        if x is None or y is None:
            raise ValueError("Expected 'x' and 'y' data in `connect_data` dict")

        fmt = connect_data.get("fmt", "ko")
        xlabel = connect_data.get("xlabel", "X")
        ylabel = connect_data.get("ylabel", "Y")

        self.daughter.set_xlabel(xlabel)
        self.daughter.set_ylabel(ylabel)
        self.daughter.fig.tight_layout()
        self.daughter.fig.subplots_adjust(top=0.9, left=0.13)

        def on_pick(event, x=x, y=y, fmt=fmt):
            if event.artist is point:
                self.daughter.plot(x, y, fmt)
                self.daughter.fig.canvas.draw_idle()

        self.fig.canvas.mpl_connect("pick_event", on_pick)
