import hashlib
import random
import numpy as np
from pympler import asizeof
import matplotlib.pyplot as plt


def compute_hash(data):
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


class Point3D:
    def __init__(self, x, y, z, data=""):
        self.x = x
        self.y = y
        self.z = z
        self.data = data


class Octree:
    def __init__(self, bounds, depth=0):
        self.bounds = bounds
        self.data = None
        self.children = [None for _ in range(8)]
        self.depth = depth
        self.hash = None

    def insert(self, point):
        if not self.bounds.contains_point(point):
            return False

        if self.depth == Octree.MAX_DEPTH:
            self.data = point
            self.hash = compute_hash(point.data)
            return True

        idx = self.bounds.get_child_index(point)
        if not self.children[idx]:
            new_bounds = self.bounds.get_child_bounds(idx)
            self.children[idx] = Octree(new_bounds, self.depth + 1)

        child_inserted = self.children[idx].insert(point)
        if child_inserted:
            self.compute_node_hash()
        return child_inserted

    def compute_node_hash(self):
        combined_hashes = ''.join(child.hash for child in self.children if child and child.hash)
        self.hash = compute_hash(combined_hashes)

    def visualize(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        xs, ys, zs = [], [], []
        self.collect_points(xs, ys, zs)
        ax.scatter(xs, ys, zs)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plt.show()

    def collect_points(self, xs, ys, zs):
        if self.data:
            xs.append(self.data.x)
            ys.append(self.data.y)
            zs.append(self.data.z)
        for child in self.children:
            if child:
                child.collect_points(xs, ys, zs)


class OctreeBounds:
    def __init__(self, x1, x2, y1, y2, z1, z2):
        self.x1, self.x2 = x1, x2
        self.y1, self.y2 = y1, y2
        self.z1, self.z2 = z1, z2

    def contains_point(self, point):
        return self.x1 <= point.x < self.x2 and self.y1 <= point.y < self.y2 and self.z1 <= point.z < self.z2

    def get_child_index(self, point):
        mid_x = (self.x1 + self.x2) / 2
        mid_y = (self.y1 + self.y2) / 2
        mid_z = (self.z1 + self.z2) / 2

        index = 0
        if point.x >= mid_x:
            index |= 1
        if point.y >= mid_y:
            index |= 2
        if point.z >= mid_z:
            index |= 4

        return index

    def get_child_bounds(self, index):
        mid_x = (self.x1 + self.x2) / 2
        mid_y = (self.y1 + self.y2) / 2
        mid_z = (self.z1 + self.z2) / 2

        if index & 1:
            x1, x2 = mid_x, self.x2
        else:
            x1, x2 = self.x1, mid_x

        if index & 2:
            y1, y2 = mid_y, self.y2
        else:
            y1, y2 = self.y1, mid_y

        if index & 4:
            z1, z2 = mid_z, self.z2
        else:
            z1, z2 = self.z1, mid_z

        return OctreeBounds(x1, x2, y1, y2, z1, z2)


Octree.MAX_DEPTH = 4  # Adjust as necessary

# Testing the octree with random data
points = [Point3D(random.uniform(0, 100), random.uniform(0, 100), random.uniform(0, 100), str(random.randint(0, 1e6))) for _ in range(1000)]
octree = Octree(OctreeBounds(0, 100, 0, 100, 0, 100))

for point in points:
    octree.insert(point)

# Visualizing
octree.visualize()

# Computing size
tree_size = asizeof.asizeof(octree)
print(f"Size of the Octree: {tree_size} bytes")
