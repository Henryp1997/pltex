"""
easy_plot.py

Matplotlib wrapper for easier and cleaner plot scripting

    - Author: Henry Pickersgill (2026)
"""

from typing import get_args

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
import scipy as sp

from pltex.types import SPINE, SPINES, LabelCfg
from pltex.label_handler import extract_axis_labels
from pltex.str_format import unpack_plot_args, parse_arrow_fmt
from pltex.saving import save_figure


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
        self.fig, self.axes = plt.subplots(
            nrows=nrows, ncols=ncols,
            figsize=figsize,
            squeeze=False
        )
        self.nrows, self.ncols = nrows, ncols
        self.multi_plot: bool = nrows > 1 or ncols > 1
        self.np, self.pd, self.sp, self.plt = self.plt = np, pd, sp, plt

        self.title = title
        if self.multi_plot:
            self.fig.suptitle(self.title, y=0.95)
        else:
            self.axes[0, 0].set_title(self.title)

        if grid_on:
            for ax in self.axes:
                ax = ax[0]
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
        ax = self.axes[row_idx, col_idx]

        x, y, fmt = unpack_plot_args(args, default_fmt=self.default_fmt)
        arrows = False
        if "->" in fmt[1:]:
            # Custom arrow format found
            fmt_color, fmt = parse_arrow_fmt(fmt)
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
            drawn_data, = ax.plot(x, y, fmt, **kwargs)

            if arrows:
                color = fmt_color
                if not fmt_color:
                    # No color present in fmt string
                    color = drawn_data.get_color()
                self._draw_arrows(ax, x, y, color=color)

            # Connect click event to daughter Figure
            if self.daughter is not None:
                self._connectToDaughter(connect_data, drawn_data)

        elif plot_type == "bar":
            drawn_data, = ax.bar(x, y, **kwargs)

        # Extract label fontsizes if given
        axis_labels: dict = extract_axis_labels(
            xlabel, ylabel, self.default_label_fsize,
            current_labels={
                "x": getattr(self, "xlabel", None),
                "y": getattr(self, "ylabel", None)
            }
        )

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

        return drawn_data, drawn_data.get_color()


    def scatter(self, *args, **kwargs):
        """ Create a scatter plot. Interface directly to self.plot """
        return self.plot(*args, **kwargs)


    def bar(self, *args, colour: str | tuple | list | None = None, **kwargs):
        """ Create a bar chart. Interface to self.plot """
        x, y, fmt = unpack_plot_args(args, default_fmt=self.default_fmt)

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
        xmax: int = 1,
        row_idx: int = 0,
        col_idx: int = 0,
        colour: str = "k",
        linestyle: str = "--",
        linewidth: float = 1.0,
        **kwargs
    ):
        """ Draw a horizontal line spanning a given range. Defaults to full range """
        ax = self.axes[row_idx, col_idx]
        kwargs["color"] = colour
        kwargs["linestyle"] = linestyle
        kwargs["linewidth"] = linewidth
        ax.axhline(y, xmin=xmin, xmax=xmax, **kwargs)


    def vline(
        self,
        x,
        ymin: int = 0,
        ymax: int = 1,
        row_idx: int = 0,
        col_idx: int = 0,
        colour: str = "k",
        linestyle: str = "--",
        linewidth: float = 1.0,
        **kwargs
    ):
        """ Draw a vertical line spanning a given range. Defaults to full range """
        ax = self.axes[row_idx, col_idx]
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
    def add_text(self, *args, **kwargs):
        """ Add text to a given axes object. Interface to text_handler.add_text() """
        if "row_idx" not in kwargs:
            row_idx = 0
        if "col_idx" not in kwargs:
            col_idx = 0
        ax = self.axes[row_idx, col_idx]
        return self.text_handler.add_text(ax, *args, **kwargs)


    def add_textbox(self, *args, **kwargs):
        """ Interface to add_text to also force drawing of bounding box """
        self.text_handler.add_textbox(*args, **kwargs)


    ### Legend handling
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
            ax = self.axes[row_idx, col_idx]
            axes = [ax] # Iterable for below loop

        self.legends = []
        for ax in axes:
            leg = ax.legend(
                loc=loc,
                framealpha=legend_alpha,
                fontsize=fontsize or self.default_legend_fsize
            )
            self.legends.append(leg)

    
    def add_legend_label(
        self,
        *args,
        row_idx: int = 0,
        col_idx: int = 0
    ):
        """ Add a separate label to the legend not connected to any data points/lines """
        if len(args) == 0:
            print("pltex warning: No `label` or `fmt` specified in add_legend_label()")
            label, fmt = "None", "k-"
        elif len(args) == 1:
            # Default to args containing `fmt` only
            label = "None"
            fmt = args[0]
        elif len(args) == 2:
            # Label and fmt specified
            label, fmt = args
        
        # Dummy plot to add label to legend
        self.plot(
            np.nan, fmt, label=label, row_idx=row_idx, col_idx=col_idx
        )
        ax = self.axes[row_idx, col_idx]
        if ax.get_legend() is None:
            print(
                "pltex warning: specified axis has no legend. Set `legend_on=True` "\
                "or call legend() before using add_legend_label()"
            )


    def remove_legend(self, row_idx: int = 0, col_idx: int = 0):
        """ Remove the legend from a specified axis """
        if self.legends:
            ax = self.axes[row_idx, col_idx]
            ax.get_legend().remove()


    def set_axis_spine_colour(
        self,
        colour: str,
        all_spines: bool = True,
        spines: SPINES | None = None,
        row_idx: int = 0,
        col_idx: int = 0
    ):
        """ Set the colour of one or more spines of the figure """
        ax = self.axes[row_idx, col_idx]
        ALL_SPINES = set(get_args(SPINE)) # Get a set of all valid spine names
        if all_spines:
            spines = ALL_SPINES
        else:
            if spines is None:
                spines = ALL_SPINES
            else:
                if any(spine not in ALL_SPINES for spine in spines):
                    raise ValueError(f"Unrecognised spine! Spines must be any set of {ALL_SPINES}")

        for spine in spines:
            ax.spines[spine].set_color(colour)


    def set_xlabel(
        self,
        xlabel: str,
        row_idx: int = 0,
        col_idx: int = 0,
        fontsize: int | None = None
    ):
        """ Interface to self._set_label to set the X axis label """
        self._set_label("x", xlabel, row_idx, col_idx, fontsize)


    def set_ylabel(
        self,
        ylabel: str,
        row_idx: int = 0,
        col_idx: int = 0,
        fontsize: int | None = None
    ):
        """ Interface to self._set_label to set the Y axis label """
        self._set_label("y", ylabel, row_idx, col_idx, fontsize)


    def _set_label(
        self,
        axis: str,
        label: str,
        row_idx: int = 0,
        col_idx: int = 0,
        fontsize: int | None = None
    ):
        """ Interface to ax.set_xlabel or ax.set_ylabel """
        ax = self.axes[row_idx, col_idx]
        if axis == "x":
            self.xlabel = label
        else:
            self.ylabel = label
        
        if fontsize is None:
            fontsize = self.default_label_fsize
        
        getattr(ax, f"set_{axis}label")(label, fontsize=fontsize)


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


    def save_interactive(self, filename: str = "figure"):
        """ Save the current Figure as an interactive .pltex file """
        return save_figure(self.fig, filename)


    ### PRIVATE METHODS
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
