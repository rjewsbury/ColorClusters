from math import inf
from random import randint
from .distance import euclidean
from .closest_color import map_pixels_to_closest_color_index, get_sum_squared_error

# TODO: Implement K-Means++ algorithm for picking initial centroids? More complex, but converges faster

class KMeans():
    """
    Stores the state of the current iteration of K-Means. Allows more control over how the algorithm proceeds
    between iterations, and allows for more types of result data.
    """
    def __init__(self, k_value, datapoints, distance=euclidean):
        """
        Begins the K-Means algorithm on the given datapoints.
        :param k_value: the number of clusters to split the data into
        :param datapoints: the data to be clustered
        :param distance: the distance formula used to determine which cluster a point belongs in
        """
        # to prevent things breaking on empty data, adds one point
        if len(datapoints) == 0:
            datapoints = [(0, 0, 0)]

        self.k_value = k_value
        self.data = datapoints
        self.dist = distance
        # the dimensionality of the data space. typically 3 for RGB or 4 for RGBA
        self.dimensions = len(datapoints[0])
        # the distance each centroid moved after the previous iteration of the algorithm
        self.shift_distance = [inf] * k_value
        # the index of the centroid each data point maps to. stored to avoid repeated computation
        self.clustering = None
        # the Sum Squared Error of the current clustering. only computed when needed
        self.error = None
        # the centers of each cluster. Initially chosen randomly
        self.centroids = [datapoints[randint(0, len(datapoints))] for i in range(k_value)]

    def compute_until_predicate(self, predicate, debug=False):
        """
        Repeatedly computes the clustering and shifts the centroids until the predicate is met
        :param predicate: a Boolean-returning function
        :param debug: True if the user wants to see the shift_distance each iteration
        """
        while not predicate(self):
            self.shift_centroids()
            if debug:
                print(self.shift_distance)

    def compute_until_max_distance(self, max_distance, debug=False):
        """
        Runs K-means until no centroid shifts more than the given max distance
        :param max_distance: the maximum allowed shift
        """
        self.compute_until_predicate(lambda self: max(self.shift_distance) <= max_distance, debug)

    def shift_centroids(self):
        """Computes one iteration of K-means, and shifts the centroids to a better position"""
        centroids = [[0] * self.dimensions for i in range(self.k_value)]
        count = [0] * self.k_value

        # count and sum each cluster set in preparation for averaging
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
                centroids[i][d] /= count[i]
            self.shift_distance[i] = self.dist(self.centroids[i], centroids[i])

        # update the centroids to the new averages
        self.centroids = centroids
        # we don't know the new derived values for this set of centroids
        self.clustering = None
        self.error = None

    def get_clustering(self):
        """Gets the closest-color index for each pixel of data for the current centroids."""
        # dont re-compute the clustering if it's already been computed
        if self.clustering is None:
            self.clustering = map_pixels_to_closest_color_index(self.data, self.centroids, self.dist)
        return self.clustering

    def get_sum_square_error(self):
        """Calculates the Sum Square Error of the current clustering."""
        if self.error is None:
            self.error = get_sum_squared_error(self.data, self.clustering, self.centroids, self.dist)
        return self.error

    def get_exact_centroids(self):
        """Gets the current centroids."""
        return self.centroids

    def get_centroids(self):
        """Rounds the centroids to an integer before returning them"""
        return [[int(x) for x in centroid] for centroid in self.centroids]
