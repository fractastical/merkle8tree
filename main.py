import hashlib
import random

# Define basic structures

class Point3D:
    def __init__(self, x, y, z, data):
        self.x = x
        self.y = y
        self.z = z
        self.data = data

class OctreeNode:
    def __init__(self, x=0, y=0, z=0, size=1):
        self.children = [None] * 8
        self.data = None  # Placeholder for leaf node data
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

    def insert(self, point):
        if self.is_leaf():
            if self.data is None:
                self.data = point
            else:
                current_point = self.data
                self.data = None
                self.subdivide()
                self.insert(current_point)
                self.insert(point)
        else:
            idx = self.get_child_index(point)
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
            ox, oy, oz = offsets[idx]
            if not self.children[idx]:
                self.children[idx] = OctreeNode(self.x + ox, self.y + oy, self.z + oz, half)
            self.children[idx].insert(point)

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

def store_to_distributed_system(data_chunk):
    return hashlib.sha256(data_chunk.encode()).hexdigest()

def retrieve_from_distributed_system(identifier):
    return "Sample data for " + identifier

# Sample usage

# 1. Generate 12 random 3D points
points = [
    Point3D(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100), f"data{idx}")
    for idx in range(12)
]

# 2. Insert the points into the octree
root = OctreeNode(0, 0, 0, 100)
for point in points:
    root.insert(point)

# 3. For each point (object), build a Merkle tree and store the tree's root in the octree
for point in points:
    merkle_root = build_merkle_tree([point.data])
    storage_identifier = store_to_distributed_system(point.data)

    node = root
    while node and (node.data is None or isinstance(node.data, Point3D)):
        idx = node.get_child_index(point)
        node = node.children[idx]

    if node:
        node.data = (merkle_root, storage_identifier)

# Outputs the data for the 12 points
print([point.data for point in points])
