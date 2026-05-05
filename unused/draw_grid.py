# create a white background of width: 1500 units and height: 2800 units. 
# draw the grids with 100 units spacing
import matplotlib.pyplot as plt
import numpy as np

# Set dimensions
width = 2800
height = 1500
spacing = 100

# Create figure and axis
fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)

# Set white background
ax.set_facecolor('white')
fig.patch.set_facecolor('white')

# Set limits
ax.set_xlim(0, width)
ax.set_ylim(0, height)

# Create grid coordinates
x_grid = np.arange(0, width + spacing, spacing)
y_grid = np.arange(0, height + spacing, spacing)

# Draw grid lines
for x in x_grid:
    ax.axvline(x, color='gray', linewidth=5, alpha=0.5)
    
for y in y_grid:
    ax.axhline(y, color='gray', linewidth=5, alpha=0.5)

# Remove axes and borders
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

# Set equal aspect ratio
ax.set_aspect('equal')

# Show plot
plt.tight_layout()
plt.savefig("field_grid.png")
plt.show()