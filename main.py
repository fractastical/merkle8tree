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
        self.merkle_root = None  # Add attribute to store merkle root
        self.storage_identifier = None  # Add attribute to store storage identifier

class OctreeNode:
    def __init__(self, bounds):
        self.bounds = bounds
        self.data = None
        self.children = None
        self.hash = None

    def is_leaf(self):
        return self.children is None

    def compute_node_hash(self):
        # For leaf nodes
        if self.data:
            self.hash = compute_hash(self.data.data)
        # For non-leaf nodes
        elif self.children:
            combined_hashes = ''.join(child.hash for child in self.children if child and child.hash)
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
            node = node.children[idx] if node.children else None
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
        if self.is_leaf() and self.data:
            existing_point = self.data
            self.data = None
            self.subdivide()
            self.children[self.get_child_index(existing_point)].insert(existing_point)

        # Insert the new point into the correct child node.
        idx = self.get_child_index(point)
        if self.children[idx].insert(point):
            self.compute_node_hash()
            return True

        return False

    def textual_representation(self, indent=0):
        def format_data(data):
            if isinstance(data, Point3D):
                return f"{data.data} ({indent})"
            else:
                return '...'

        prefix = '  ' * indent
        output = ""

        if self.data or (self.children and any(child for child in self.children)):
            output += f"{prefix}{format_data(self.data)}\n"
            if self.children:
                for child in self.children:
                    if child:
                        output += child.textual_representation(indent + 1)
        return output

    def subdivide(self):
        x, y, z = self.bounds.center
        d = self.bounds.dimension / 4.0
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
        return self.x1 <= x < self.x2 and self.y1 <= y < self.y2 and self.z1 <= z < self.z2

# Test the Octree

# Initialize the octree with bounding box spanning from 0 to 100 in all dimensions.
octree = OctreeNode(OctreeBoundingBox(0, 100, 0, 100, 0, 100))

# Insert some random data
points = [Point3D(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100), f"Point-{i}") for i in range(100)]
for point in points:
    octree.insert(point)

# Print the octree
print(octree.textual_representation())
