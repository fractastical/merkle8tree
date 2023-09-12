import hashlib
import random
import matplotlib.pyplot as plt
import numpy as np
from pympler import asizeof
from mpl_toolkits.mplot3d import Axes3D

# Define basic structures

class Point3D:
    def __init__(self, x, y, z, data):
        self.x = x
        self.y = y
        self.z = z
        self.data = data

class OctreeNode:

    OFFSETS = [
        (0, 0, 0),
        (0.5, 0, 0),
        (0, 0.5, 0),
        (0.5, 0.5, 0),
        (0, 0, 0.5),
        (0.5, 0, 0.5),
        (0, 0.5, 0.5),
        (0.5, 0.5, 0.5)
    ]


    def __init__(self, x=0, y=0, z=0, size=1, metadata=None):
        self.children = [None] * 8
        self.data = None  # Placeholder for leaf node data
        self.metadata = metadata  
        self.x = x
        self.y = y
        self.z = z
        self.size = size

    def is_leaf(self):
        return all(child is None for child in self.children)

    def get_child_index(self, point):
        mid_x, mid_y, mid_z = self.x + self.size/2, self.y + self.size/2, self.z + self.size/2
        index = 0
        if point.x >= mid_x:
            index |= 1
        if point.y >= mid_y:
            index |= 2
        if point.z >= mid_z:
            index |= 4
        return index

    def depth_of_point(self, point):
        depth = 0
        node = self
        while node and (node.data is None or isinstance(node.data, Point3D)):
            idx = node.get_child_index(point)
            node = node.children[idx]
            depth += 1
        return depth

    def insert(self, point):
        # print(f"Inserting {point.data} into node at ({self.x}, {self.y}, {self.z}) with size {self.size}")
        
        if self.is_leaf():
            # print(f"Leaf node encountered for {point.data}. Current data: {self.data}")
            
            if self.data is None:
                self.data = point
            else:
                current_point = self.data
                self.data = None
                self.subdivide()
                # print(f"Subdividing for {point.data}. Re-inserting {current_point.data} and {point.data}.")
                self.insert(current_point)
                self.insert(point)
        else:
            idx = self.get_child_index(point)
            half = self.size / 2
            ox, oy, oz = OctreeNode.OFFSETS[idx]
            
            # print(f"Child index for {point.data} is {idx}. Checking child node...")
            
            if not self.children[idx]:
                # print(f"Child node is None. Creating new node for {point.data}.")
                self.children[idx] = OctreeNode(self.x + ox, self.y + oy, self.z + oz, half)
            # else:
            #     print(f"Child node exists. Proceeding to insert {point.data}.")
            
            self.children[idx].insert(point)

    def insert_into_octree(octree, point, data, metadata):
        node = find_or_create_node_for_point(octree, point)
        node.data = data
        node.metadata = metadata  # Attach the GLB reference or other metadata here

    def textual_representation(self, indent=0):
        # Helper function to format node's data for display
        def format_data(data):
            if isinstance(data, Point3D):
                return f"{data.data} ({indent})"
            elif isinstance(data, tuple):  # Checks if data is a tuple (merkle_root, storage_identifier)
                merkle_root, _ = data
                return f"Hash: {merkle_root.hash} ({indent})"
            else:
                return '...'

        # Indentation to show depth
        prefix = '  ' * indent

        # Node's data
        output = ""

        # If the node has data or children with data, print its representation
        if self.data or (self.children and any(child for child in self.children)):
            output += f"{prefix}{format_data(self.data)}\n"

            # Recurse on children if they exist
            if self.children:
                for child in self.children:
                    if child:
                        output += child.textual_representation(indent + 1)
        return output

    def subdivide(self):
        half = self.size / 2
        offsets = [
            (0, 0, 0),
            (half, 0, 0),
            (0, half, 0),
            (half, half, 0),
            (0, 0, half),
            (half, 0, half),
            (0, half, half),
            (half, half, half)
        ]
        for idx, (ox, oy, oz) in enumerate(offsets):
            self.children[idx] = OctreeNode(self.x + ox, self.y + oy, self.z + oz, half)

class MerkleNode:
    def __init__(self, data=None):
        self.left = None
        self.right = None
        self.data = data
        self.hash = self.compute_hash()

    def compute_hash(self):
        if self.data:
            return hashlib.sha256(self.data.encode()).hexdigest()
        left_hash = self.left.hash if self.left else ''
        right_hash = self.right.hash if self.right else ''
        return hashlib.sha256((left_hash + right_hash).encode()).hexdigest()

# Basic operations

def build_merkle_tree(data_list):
    nodes = [MerkleNode(data=d) for d in data_list]
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(None)
        it = iter(nodes)
        nodes = [combine_merkle_nodes(a, b) for a, b in zip(it, it)]
    return nodes[0]

def combine_merkle_nodes(left, right):
    parent = MerkleNode()
    parent.left = left
    parent.right = right
    parent.hash = parent.compute_hash()
    return parent

# Distributed storage mockup

def visualize_points(points, octree_root):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    # Pre-compute depths
    depths = [octree_root.depth_of_point(point) for point in points]
    min_depth, max_depth = min(depths), max(depths)
    
    # Normalize depths to range between min_depth and max_depth for color and size adjustments
    normalized_depths = [(depth - min_depth) / (max_depth - min_depth) for depth in depths]
    
    xs = [point.x for point in points]
    ys = [point.y for point in points]
    zs = [point.z for point in points]
    colors = [(1-depth, 0, depth) for depth in normalized_depths]  # Color transition: red (shallow) to blue (deep)
    sizes = [20 * (1-depth) + 5 for depth in normalized_depths]  # Size transition: large (shallow) to small (deep)
    
    ax.scatter(xs, ys, zs, c=colors, marker='o', s=sizes)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.show()


def store_to_distributed_system(data_chunk):
    return hashlib.sha256(data_chunk.encode()).hexdigest()

def retrieve_from_distributed_system(identifier):
    return "Sample data for " + identifier


cluster_centers = [
    Point3D(25, 25, 25, "center1"),
    Point3D(75, 75, 75, "center2"),
    Point3D(25, 75, 25, "center3"),
    Point3D(75, 25, 75, "center4")
]

# Define number of points per cluster and cluster radius
points_per_cluster = 70
cluster_radius = 15

# Generate points clustered around centers
points = []
for center in cluster_centers:
    for _ in range(points_per_cluster):
        # Generate a random offset from the cluster center
        offset = np.random.normal(0, cluster_radius, 3)
        point = Point3D(center.x + offset[0], center.y + offset[1], center.z + offset[2], f"data_{len(points)}")
        points.append(point)


# points = [
#     Point3D(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100), f"data{idx}")
#     for idx in range(100)
# ]

# 2. Insert the points into the octree
root = OctreeNode(0, 0, 0, 300)
for point in points:
    root.insert(point)

# 3. For each point (object), build a Merkle tree and store the tree's root in the octree
for point in points:
    # print(f"Processing point: {point.data}")
    merkle_root = build_merkle_tree([point.data])
    storage_identifier = store_to_distributed_system(point.data)

    node = root

    # while node and (node.data is None or isinstance(node.data, Point3D)):
    while node and node.is_leaf() == False:
        idx = node.get_child_index(point)
        node = node.children[idx]
    # if node is None:
    #     print(f"Encountered None node while processing point: {point.data}")
    #     break
    # if node.data is not None and not isinstance(node.data, Point3D):
    #     print(f"Encountered node with Merkle data while processing point: {point.data}")
    #     break
    if node and isinstance(node.data, Point3D):
        node.data = (merkle_root, storage_identifier)
    else:
        print(f"Failed to find a node for point: {point.data}")


print(root.textual_representation())

def draw_cube(ax, node):
    r = [node.x, node.x + node.size]
    s = [node.y, node.y + node.size]
    t = [node.z, node.z + node.size]

    for x in r:
        for y in s:
            for z in t:
                ax.scatter(x, y, z, color="b", s=50)
                if node.data:
                    ax.text(x, y, z, '%s' % (str(node.data)), size=10, zorder=1, color='k')

# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')


def visualize_octree_3d(node, ax):
    if node:
        draw_cube(ax, node)
        for child in node.children:
            visualize_octree_3d(child, ax)

# cool concept but too visually crowded
# visualize_octree_3d(root, ax)
# plt.show()

# Computing size
tree_size = asizeof.asizeof(root)
print(f"Size of the Octree: {tree_size} bytes")


visualize_points(points, root)


class OctreeHeatmap:
    
    @staticmethod
    def slice_heatmap(root, z_value, resolution=100):
        # Initialize a 2D grid to store depth values
        grid = np.zeros((resolution, resolution))
        
        # Calculate grid cell dimensions
        cell_size = root.size / resolution
        
        def traverse(node, x, y, z, size, depth):
            nonlocal grid
            
            # Check if the node's 3D cube intersects with the slice at z_value
            if z <= z_value <= (z + size):
                # Calculate grid coordinates for this node
                x_min, y_min = int(x / cell_size), int(y / cell_size)
                x_max, y_max = int(np.ceil((x + size) / cell_size)), int(np.ceil((y + size) / cell_size))
                
                # Update grid cells that overlap with this node
                grid[y_min:y_max, x_min:x_max] = np.maximum(grid[y_min:y_max, x_min:x_max], depth)
            
            # Recursively traverse child nodes
            if not node.is_leaf():
                for i, child in enumerate(node.children):
                    if child is not None:
                        ox, oy, oz = OctreeNode.OFFSETS[i]
                        new_x, new_y, new_z = x + ox * size, y + oy * size, z + oz * size
                        new_size = size / 2
                        traverse(child, new_x, new_y, new_z, new_size, depth + 1)
        
        # Start the traversal from the root
        traverse(root, root.x, root.y, root.z, root.size, 0)
        
        # Display the heatmap
        plt.imshow(grid, cmap='hot', interpolation='nearest')
        plt.colorbar(label='Depth')
        plt.title(f'Octree Slice Heatmap at z={z_value}')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.show()

OctreeHeatmap.slice_heatmap(root, 25, resolution=100)

