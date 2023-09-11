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
    def __init__(self, bounds, depth=0, max_depth=8, cluster_size=4):
        self.bounds = bounds
        self.children = [None] * 8
        self.points = []
        self.hash = None
        self.depth = depth
        self.max_depth = max_depth
        self.cluster_size = cluster_size

    def insert(self, point):
        if not self.bounds.contains_point(point):
            return

        if self.depth < self.max_depth and len(self.points) >= self.cluster_size:
            idx = self.bounds.get_child_index(point)
            if not self.children[idx]:
                self.children[idx] = OctreeNode(self.bounds.get_child_bounds(idx), self.depth + 1, self.max_depth, self.cluster_size)
            self.children[idx].insert(point)
            
            to_reinsert = self.points.copy()
            self.points = []  # Clear points from current node

            for p in to_reinsert:
                idx = self.bounds.get_child_index(p)
                if not self.children[idx]:
                    self.children[idx] = OctreeNode(self.bounds.get_child_bounds(idx), self.depth + 1, self.max_depth, self.cluster_size)
                self.children[idx].insert(p)
            self.points = []  # Clear points from current node
        else:
            self.points.append(point)
        self.compute_node_hash()

    def compute_node_hash(self):
        combined_hashes = ''.join((child.hash if (child and child.hash) else '') for child in self.children)
        if combined_hashes:
            self.hash = hashlib.sha256(combined_hashes.encode()).hexdigest()
        if self.points:
            combined_points = ''.join((str(p) for p in self.points))
            self.hash = hashlib.sha256(combined_points.encode()).hexdigest()

    def __repr__(self, depth=0):
        indent = '  ' * depth
        if self.children:
            children_repr = ''.join(
                f"{indent}Child {i}:\n{child.__repr__(depth+1)}\n" for i, child in enumerate(self.children) if child)
            return f"{indent}Node at Depth {depth} with Hash {self.hash}\n{children_repr}"
        else:
            return f"{indent}Leaf at Depth {depth} with Points {self.points} and Hash {self.hash}"

    def __str__(self, level=0):
        ret = "\t"*level + self.hash + "\n" if self.hash else ""
        for child in self.children:
            if child:
                ret += child.__str__(level+1)
        return ret

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
        for point in self.points:
            xs.append(point.x)
            ys.append(point.y)
            zs.append(point.z)
        for child in self.children:
            if child:
                child.collect_points(xs, ys, zs)

class OctreeNode:
    def __init__(self, bounds, depth=0, max_depth=8, cluster_size=1):
        self.bounds = bounds
        self.children = [None] * 8
        self.points = []
        self.hash = None
        self.depth = depth
        self.max_depth = max_depth
        self.cluster_size = cluster_size

    def collect_points(self, xs, ys, zs):
        for point in self.points:
            xs.append(point.x)
            ys.append(point.y)
            zs.append(point.z)
        for child in self.children:
            if child:
                child.collect_points(xs, ys, zs)

    def insert(self, point):
        if not self.bounds.contains(point):
            return

        if self.depth < self.max_depth and len(self.points) < self.cluster_size:
            self.points.append(point)
            return
        
        if self.depth == self.max_depth:
            self.points.append(point)
            return

        idx = self._get_octant(point)
        if not self.children[idx]:
            self.children[idx] = OctreeNode(self.bounds.get_child_bounds(idx), self.depth + 1, self.max_depth, self.cluster_size)
        
        self.children[idx].insert(point)

    def _get_octant(self, point):
        x, y, z = point.x, point.y, point.z
        mid_x = (self.bounds.x1 + self.bounds.x2) / 2
        mid_y = (self.bounds.y1 + self.bounds.y2) / 2
        mid_z = (self.bounds.z1 + self.bounds.z2) / 2
        
        if x < mid_x:
            if y < mid_y:
                if z < mid_z: return 0
                return 4
            else:
                if z < mid_z: return 2
                return 6
        else:
            if y < mid_y:
                if z < mid_z: return 1
                return 5
            else:
                if z < mid_z: return 3
                return 7

    def compute_hash(self):
        hasher = hashlib.sha256()
        for child in self.children:
            if child:
                child.compute_hash()
                hasher.update(child.hash.encode('utf-8'))

        for point in self.points:
            hasher.update(str(point).encode('utf-8'))

        self.hash = hasher.hexdigest()

    def __str__(self, level=0):
        ret = "\t"*level + self.hash + "\n" if self.hash else ""
        for child in self.children:
            if child:
                ret += child.__str__(level+1)
        return ret


class OctreeBounds:
    def __init__(self, x1, x2, y1, y2, z1, z2):
        self.x1, self.x2 = x1, x2
        self.y1, self.y2 = y1, y2
        self.z1, self.z2 = z1, z2

    def contains_point(self, point):
        return self.x1 <= point.x < self.x2 and self.y1 <= point.y < self.y2 and self.z1 <= point.z < self.z2

    def contains(self, point):
        x, y, z = point.x, point.y, point.z
        return self.x1 <= x < self.x2 and self.y1 <= y < self.y2 and self.z1 <= z < self.z2

    def get_child_index(self, point):
        midx, midy, midz = (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2, (self.z1 + self.z2) / 2
        idx = 0
        if point.x >= midx:
            idx |= 1
        if point.y >= midy:
            idx |= 2
        if point.z >= midz:
            idx |= 4
        return idx

    def get_child_bounds(self, index):
        midx, midy, midz = (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2, (self.z1 + self.z2) / 2
        if index & 1:
            x1, x2 = midx, self.x2
        else:
            x1, x2 = self.x1, midx
        if index & 2:
            y1, y2 = midy, self.y2
        else:
            y1, y2 = self.y1, midy
        if index & 4:
            z1, z2 = midz, self.z2
        else:
            z1, z2 = self.z1, midz
        return OctreeBounds(x1, x2, y1, y2, z1, z2)

Octree.MAX_DEPTH = 4  # Adjust as necessary

# Testing the octree with random data
points = [Point3D(random.uniform(0, 100), random.uniform(0, 100), random.uniform(0, 100), str(random.randint(0, 1e6))) for _ in range(1000)]
octree = Octree(OctreeBounds(0, 100, 0, 100, 0, 100))

for _ in range(10):  # example insertions
    point = Point3D(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
    octree.insert(point)
print(octree)


# Visualizing
octree.visualize()

# Text representation
print(octree)

# Computing size
tree_size = asizeof.asizeof(octree)
print(f"Size of the Octree: {tree_size} bytes")
