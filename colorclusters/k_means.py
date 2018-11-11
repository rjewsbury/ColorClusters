from .distance import euclidean
from math import inf
from random import randint
import colorclusters.image_utils as utils


def _choose_initial_centroids(k_value, datapoints):
    if not datapoints:
        return []
    centroids = [datapoints[randint(0, len(datapoints))] for i in range(k_value)]
    return centroids


class KMeans():
    def __init__(self, k_value, datapoints, distance=euclidean):
        # to prevent things breaking on empty data, adds one point
        if len(datapoints) == 0:
            datapoints = [(0, 0, 0)]

        self.k_value = k_value
        self.dimensions = len(datapoints[0])
        self.shift_distance = [inf] * k_value
        self.data = datapoints
        self.dist = distance
        self.clustering = None
        self.error = None
        self.centroids = _choose_initial_centroids(k_value, datapoints)

    def compute_until_predicate(self, predicate, debug=False):
        while not predicate(self):
            self.shift_centroids()
            if debug:
                print(self.shift_distance)

    def compute_until_max_distance(self, max_distance, debug=False):
        self.compute_until_predicate(lambda self: max(self.shift_distance) <= max_distance, debug)

    def shift_centroids(self):
        centroids = [[0] * self.dimensions for i in range(self.k_value)]
        count = [0] * self.k_value

        for i, pixel in zip(self.get_clustering(), self.data):
            count[i] += 1
            for d in range(self.dimensions):
                centroids[i][d] += pixel[d]

        # take the average of all points in the cluster
        for i in range(self.k_value):
            # if none of the points were closest to this point, leave it where it is
            if count[i] == 0:
                centroids[i] = self.centroids[i]
                self.shift_distance[i] = 0
                continue

            for d in range(self.dimensions):
                centroids[i][d] //= count[i]
            self.shift_distance[i] = self.dist(self.centroids[i], centroids[i])

        # update the centroids to the new averages
        self.centroids = centroids
        # we don't know the new derived values for this set of centroids
        self.clustering = None
        self.error = None

    def get_clustering(self):
        # dont re-compute the clustering if it's already been computed
        if self.clustering is None:
            self.clustering = utils.map_pixels_to_closest_color_index(self.data, self.centroids, self.dist)
        return self.clustering

    def get_sum_square_error(self):
        if self.error is None:
            error = 0
            for i, pixel in zip(self.get_clustering(), self.data):
                error += self.dist(self.centroids[i], pixel) ** 2
            self.error = error
        return self.error

    def get_centroids(self):
        return self.centroids
