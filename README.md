# easy_plot
`easy_plot` (https://github.com/Henryp1997/easy_plot) is a tool to aid programmers in creating Matplotlib figures quicker and easier. It is intended to remove a lot of the boilerplate involved in creating plots using Matplotlib. It also includes additional features, such as the ability to save .eplot files, which are serialised `Figure` objects, with the intention of being able to view these as _interactive figures_.

## Example
```
from easy_plot import Figure, np

fig = Figure(title="Test figure", figsize=(8, 5), legend_on=True)
x = np.array(list(range(10)))
fig.plot(
    x, x**2, "bo->",
    xlabel="X axis", ylabel="Y axis", label="Test data 1"
)
fig.plot(
    x, x**3, "r^-", label="Test data 2"
)
fig.show() # Mark figure as visible
Figure.display() # Display all figures marked as visible
```
<img width="768" height="480" alt="test" src="https://github.com/user-attachments/assets/a008a987-28b5-4e34-804e-f0a668bbf0e8" />
