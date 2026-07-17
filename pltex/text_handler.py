"""
text_handler

Handle adding text/textboxes to Figures

    - Author: HP (2026)
"""

class TextHandler():
    def __init__(self) -> None:
        pass


    def add_text(
        self,
        ax,
        pos,
        text,
        box: bool = False,
        box_border_colour: str = None,
        box_face_colour: str = None,
        box_alpha: float = None,
        fontsize: int = 12,
        **kwargs
    ) -> None:
        """ Add text to a given axes object """
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
