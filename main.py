import hashlib
import random
import matplotlib.pyplot as plt
import numpy as np
from pympler import asizeof

# Define basic structures

def compute_hash(data):
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

class Point3D:
    def __init__(self, x, y, z, data):
        self.x = x
        self.y = y
        self.z = z
        self.data = data

class OctreeNode:
    def __init__(self, bounds):
        self.bounds = bounds
        self.data = None
        self.children = None
        self.hash = None

    def is_leaf(self):
        if self.children is None:
            return True
        return all(child is None for child in self.children)

    def compute_node_hash(self):
        # For leaf nodes
        if self.data:
            self.hash = compute_hash(self.data.data)
        # For non-leaf nodes
        elif self.children:
            combined_hashes = ''.join(child.hash for child in self.children if child)
            self.hash = compute_hash(combined_hashes)

    def get_child_index(self, point):
        mid_x, mid_y, mid_z = self.bounds.center
        index = 0
        if point.x > mid_x:
            index |= 1
        if point.y > mid_y:
            index |= 2
        if point.z > mid_z:
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
        # Ensure the point belongs within the node's bounds.
        if not self.bounds.contains_point(point.x, point.y, point.z):
            return False

        # If node is a leaf and empty, store the point.
        if self.is_leaf() and self.data is None:
            self.data = point
            self.compute_node_hash()
            return True

        # If node is a leaf but has a point, subdivide.
        if self.is_leaf() and self.data is not None:
            # Store current data
            existing_point = self.data
            # Clear current data
            self.data = None
            # Subdivide
            self.subdivide()
            # Insert the existing point into the correct child
            for child in self.children:
                if child.insert(existing_point):
                    break

        # Insert the new point into the correct child node.
        for child in self.children:
            if child.insert(point):
                return True

        # If all else fails, return False
        return False


    def textual_representation(self, indent=0):
        # Helper function to format node's data for display
        def format_data(data):
            if isinstance(data, Point3D):
                return f"{data.data} ({indent})"
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
        x, y, z = self.bounds.center
        d = self.bounds.dimension / 4.0
        # Note: When creating a new OctreeNode, pass only the bounding box object
        self.children = [
            OctreeNode(OctreeBoundingBox(x - d, x, y - d, y, z - d, z)),
            OctreeNode(OctreeBoundingBox(x, x + d, y - d, y, z - d, z)),
            OctreeNode(OctreeBoundingBox(x - d, x, y, y + d, z - d, z)),
            OctreeNode(OctreeBoundingBox(x, x + d, y, y + d, z - d, z)),
            OctreeNode(OctreeBoundingBox(x - d, x, y - d, y, z, z + d)),
            OctreeNode(OctreeBoundingBox(x, x + d, y - d, y, z, z + d)),
            OctreeNode(OctreeBoundingBox(x - d, x, y, y + d, z, z + d)),
            OctreeNode(OctreeBoundingBox(x, x + d, y, y + d, z, z + d))
        ]


class OctreeBoundingBox:
    def __init__(self, x1, x2, y1, y2, z1, z2):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.z1 = z1
        self.z2 = z2
        self.center = ((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2)
        self.dimension = max(x2 - x1, y2 - y1, z2 - z1)

    def contains_point(self, x, y, z):
        return (self.x1 <= x < self.x2 and
                self.y1 <= y < self.y2 and
                self.z1 <= z < self.z2)

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
points_per_cluster = 25
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

# Create a bounding box for the root node
root_bounds = OctreeBoundingBox(0, 100, 0, 100, 0, 100)
root = OctreeNode(root_bounds)
for point in points:
    root.insert(point)

# 3. For each point (object), build a Merkle tree and store the tree's root in the octree
for point in points:
    merkle_root = build_merkle_tree([point.data])
    storage_identifier = store_to_distributed_system(point.data)

    node = root
    while node:
        if node.is_leaf():
            if node.data is None:  # Empty leaf node
                node.data = (point.x, point.y, point.z, merkle_root, storage_identifier)
                break
            else:  # Leaf node with existing data
                existing_data = node.data
                node.data = None
                node.subdivide()  # Ensure this method correctly initializes `children` as a list of 8.
                # Re-insert the existing data
                x, y, z, _, _ = existing_data
                idx_existing = node.get_child_index(Point3D(x, y, z))
                node.children[idx_existing].data = existing_data

        # Navigate to the appropriate child node for the current point
        idx = node.get_child_index(point)
        node = node.children[idx]


# # After generating the points and before visualizing
# for point in points:
#     print(f"Point {point.data} Depth: {root.depth_of_point(point)}")

print(root.textual_representation())

tree_size = asizeof.asizeof(root)

print(f"Merkle root of the octree: {root.hash}")

print(f"Total size of the octree structure: {tree_size} bytes")

visualize_points(points, root)

