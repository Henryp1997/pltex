"""
easy_plot.py

Matplotlib wrapper for easier and cleaner plot scripting

    - Author: Henry Pickersgill (2026)
"""

from pathlib import Path
from dataclasses import dataclass
from typing import get_args
import pickle

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
import scipy as sp

from easy_plot.types import SPINE, SPINES


@dataclass
class LabelCfg():
    label: str
    fontsize: int = 12


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
        legend_fontsize: int = 8,
        nrows: int = 1,
        ncols: int = 1,
        figsize: tuple[int] = (12, 8),
        default_fontsize: int = 10
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
        self.default_fontsize = default_fontsize
        self.default_fmt = "kx"

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
        self.legend_fontsize = legend_fontsize
        self.legends = []

        # Keep track of this instance in the class attribute `all_figs`
        self.all_figs.append(self)


    def plot(
        self,
        *args, # x, y, fmt
        mfc: str | None = "none",
        mec: str | None = None,
        xlabel: str | dict | LabelCfg = "X",
        ylabel: str | dict | LabelCfg = "Y",
        row_idx: int = 0,
        col_idx: int = 0,
        xticklabel_fontsize: int | None = None,
        yticklabel_fontsize: int | None = None,
        plot_type: str = "plot",
        **kwargs
    ):
        """ Add data to the axes """
        ax = self._getAx(row_idx, col_idx)

        x, y, fmt = self._unpack_plot_args(args)
        plot_method = getattr(ax, plot_type)

        if plot_method == "plot":
            kwargs["mec"], kwargs["mfc"] = mec, mfc
            args = (x, y, fmt)
        elif plot_method == "bar":
            args = (x, y)
        
        plot_method(*args, **kwargs)

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
                    lab_obj.get("fontsize", self.default_fontsize)
                )
            elif isinstance(lab_obj, str):
                lab_obj = LabelCfg(lab_obj, self.default_fontsize)
            else:
                raise TypeError(
                    f"Unexpected type for {name}label. Expected str | dict | LabelCfg but got {type(lab_obj)}"
                )

            lab = getattr(lab_obj, "label", name)
            fsize = getattr(lab_obj, "fontsize", self.default_fontsize)

            axis_labels[name] = {
                "label": lab, "fontsize": fsize
            }

        ax.set_xlabel(axis_labels["x"]["label"], fontsize=axis_labels["x"]["fontsize"])
        ax.set_ylabel(axis_labels["y"]["label"], fontsize=axis_labels["y"]["fontsize"])

        if xticklabel_fontsize is not None:
            ax.tick_params(axis="x", which="major", labelsize=xticklabel_fontsize)
        if yticklabel_fontsize is not None:
            ax.tick_params(axis="y", which="major", labelsize=yticklabel_fontsize)

        if self.legend_on:
            ax.legend(fontsize=self.legend_fontsize)


    def bar(self, *args, **kwargs):
        """ Create a bar chart. Interface to self.plot """
        x, y, fmt = self._unpack_plot_args(args)
        kwargs["color"] = fmt[0]
        kwargs["zorder"] = 9999 # Always draw bars on top of grid
        return self.plot(x, y, **kwargs, plot_type="bar")


    def legend(
        self,
        loc = "best",
        row_idx: int = 0,
        col_idx: int = 0,
        all_axes: bool = False,
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
            leg = ax.legend(loc=loc, fontsize=fontsize or self.legend_fontsize)
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


    def axline(
        self,
        pos: float
    ):
        """ Draw a horizontal or vertical line spanning the full width/height of the axes """


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
