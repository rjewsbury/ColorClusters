from math import inf
from random import randrange, choices
from collections import Counter
from .distance import euclidean
from .closest_color import get_closest_color_index, map_pixels_to_closest_color_index, get_sum_squared_error


class KMeans():
    """
    Stores the state of the current iteration of K-Means. Allows more control over how the algorithm proceeds
    between iterations, and allows for more types of result data.
    """
    def __init__(self, k_value, datapoints, distance=euclidean, use_histogram=True, use_kmeans_plus_plus=False):
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
        self.use_histogram = use_histogram

        # k_means_plus_plus requires the histogram and a list of unique points
        if use_histogram or use_kmeans_plus_plus:
            self.histogram = self.create_histogram()
            if use_kmeans_plus_plus:
                self.unique = list(self.histogram)

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
        if use_kmeans_plus_plus:
            self.k_means_plus_plus()
        else:
            self.centroids = [datapoints[randrange(len(datapoints))] for i in range(k_value)]

    def k_means_plus_plus(self):
        """Uses weighted probability to choose the initial centroids"""
        self.centroids = []

        #pick a first point
        point = self.data[randrange(len(self.data))]
        self.centroids.append(point)
        weights = [(self.dist(point,x)**2) * self.histogram[x] for x in self.unique]

        for i in range(1,self.k_value):
            point = choices(self.unique,weights)[0]
            self.centroids.append(point)
            #update new weights
            for j,x in enumerate(self.unique):
                weight = (self.dist(point,x)**2) * self.histogram[x]
                if weight < weights[j]:
                    weights[j] = weight

    def create_histogram(self):
        """gets the counts of items in data."""

        # histogram = {}
        # for pixel in self.data:
        #     histogram[pixel] = histogram.get(pixel, 0) + 1
        # return histogram

        # supposedly Counter is more efficient
        return Counter(self.data)

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

    def shift_centroids_histogram(self):
        """
        Computes one iteration of K-means, and shifts the centroids to a better position.
        Uses the histogram to improve efficiency
        """
        centroids = [[0] * self.dimensions for i in range(self.k_value)]
        count = [0] * self.k_value

        # count and sum each cluster set in preparation for averaging
        for pixel in self.histogram:
            i = get_closest_color_index(pixel,self.centroids, self.dist)
            count[i] += self.histogram[pixel]
            for d in range(self.dimensions):
                centroids[i][d] += pixel[d]*self.histogram[pixel]

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

    def shift_centroids(self):
        """Computes one iteration of K-means, and shifts the centroids to a better position"""
        if self.use_histogram:
            self.shift_centroids_histogram()
            return

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
