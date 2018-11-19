import math


class EuclideanSpace(object):
    def __init__(self, points, partitions, min_val, max_val, dimension=0):
        if len(points) == 0:
            self.points = points
            self.sub_spaces = None
            self.total_points = 0
        else:
            if dimension == len(points[0]):
                self.points = points
                self.sub_spaces = None
                self.total_points = len(points)
            else:
                self.points = None
                self.sub_spaces = generate_sub_spaces(points, partitions, min_val, max_val, dimension)
                self.total_points = 0
                for sub_space in self.sub_spaces.values():
                    self.total_points += sub_space.total_points

    def get_points_in_range(self, center, radius, dimension=0):
        """
        Find all points in a cube surrounding the sphere centered at 'center' and with radius 'radius'
        :param center: Center of the sphere
        :param radius: Radius of sphere
        :return: The set of points within the bounds
        """
        if self.points is not None:
            return self.points
        else:
            min_val = center[dimension] - radius
            max_val = center[dimension] + radius
            sub_spaces_to_get = []
            for key in self.sub_spaces.keys():
                if ranges_intersect(key, (min_val, max_val)):
                    sub_spaces_to_get.append(self.sub_spaces[key])
            points_to_return = []
            for sub_space in sub_spaces_to_get:
                points_to_return = points_to_return + sub_space.get_points_in_range(center, radius, dimension+1)
            return points_to_return


def generate_sub_spaces(points, partitions, min_val, max_val, dimension):
    sub_spaces = {}
    partition_size = (max_val+1-min_val)/partitions
    sort_function = sort_by(dimension)
    points.sort(key=sort_function)

    last_partition_ended_at = 0
    for i in range(int(partitions)):
        sub_space_points = []
        min_val_for_sub_space = min_val + partition_size*(i)
        max_val_for_sub_space = min_val + partition_size*(i+1)
        for j in range(last_partition_ended_at, len(points)):
            if points[j][dimension] < max_val_for_sub_space:
                sub_space_points.append(points[j])
            else:
                last_partition_ended_at = j
                break
            if j == len(points) - 1:
                last_partition_ended_at = j+1
        sub_spaces[(min_val_for_sub_space, max_val_for_sub_space)] = \
            (EuclideanSpace(sub_space_points, partitions, min_val, max_val, dimension+1))

    return sub_spaces


def sort_by(x):
    def sort_by_elem(elem):
        return elem[x]
    return sort_by_elem


def ranges_intersect(space_key, centroid_range):
    space_key_min = space_key[0]
    space_key_max = space_key[1]
    centroid_range_min = centroid_range[0]
    centroid_range_max = centroid_range[1]
    return space_key_min <= centroid_range_min < space_key_max or space_key_min <= centroid_range_max <space_key_max
