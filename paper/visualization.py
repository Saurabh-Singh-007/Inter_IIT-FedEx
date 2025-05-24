import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def draw_box(ax, origin, size, color="blue", alpha=0.5, box_id=None):
    x, y, z = origin
    dx, dy, dz = size

    # Define the vertices of the box
    vertices = [
        [x, y, z], [x + dx, y, z], [x + dx, y + dy, z], [x, y + dy, z],
        [x, y, z + dz], [x + dx, y, z + dz], [x + dx, y + dy, z + dz], [x, y + dy, z + dz]
    ]

    # Define the six faces of the box
    faces = [
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # Bottom
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # Top
        [vertices[0], vertices[3], vertices[7], vertices[4]],  # Left
        [vertices[1], vertices[2], vertices[6], vertices[5]],  # Right
        [vertices[0], vertices[1], vertices[2], vertices[3]],  # Front
        [vertices[4], vertices[5], vertices[6], vertices[7]],  # Back
    ]

    # Add the faces to the plot
    box_poly = Poly3DCollection(faces, facecolors=color, linewidths=1, edgecolors="k", alpha=alpha)
    ax.add_collection3d(box_poly)

    # Annotate the box ID at the center of the box
    if box_id:
        center = (x + dx / 2, y + dy / 2, z + dz / 2)
        ax.text(center[0], center[1], center[2], box_id, color="black", fontsize=10, ha='center', va='center')

def visualize_container(container_info, boxes):
    uld_id = container_info["id"]
    container_size = (container_info["width"], container_info["length"], container_info["height"])
    fig = plt.figure(figsize=(10, 7))
    fig.suptitle(f"ULD ID: {uld_id}", fontsize=12)
    ax = fig.add_subplot(111, projection='3d')

    # Draw the container (as a transparent box)
    draw_box(ax, (0, 0, 0), container_size, color="blue", alpha=0.2)

    # Draw each box
    for box in boxes:
        origin = tuple(box['placement'])
        size = tuple(box['dimensions'])
        color = box.get('color', 'blue')  # Default color is blue
        box_id = box['box_id']
        type = box["type"]
        if (type == "Priority") : draw_box(ax, origin, size, color='red', alpha=0.7, box_id=box_id)
        else: draw_box(ax, origin, size, color='green', alpha=0.7, box_id=box_id)

    # Set axis limits
    ax.set_xlim([0, container_size[0]])
    ax.set_ylim([0, container_size[1]])
    ax.set_zlim([0, container_size[2]])

    # Set axis labels
    ax.set_xlabel('Length')
    ax.set_ylabel('Width')
    ax.set_zlabel('Height')

    # Show the plot
    plt.show()
