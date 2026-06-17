from easy_plot import Figure

fig = Figure(title="Test figure")
fig.plot(
    [1,2,3], [4,5,6], "bo-",
    xlabel="X axis", ylabel="Y axis"
)
fig.set_axis_spine_colour(all=True, colour="r")
fig.show()
Figure.display()
