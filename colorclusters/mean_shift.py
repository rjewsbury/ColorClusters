from colorclusters import distance
from datastructures.EuclideanSpace import EuclideanSpace


def mine(points, output_thread, distance_alg=distance.euclidean, min_movement=3, max_centroids=256):
    """
    Uses the mean-shift algorithm to produce the set of average points that best represents the points given
    :param points: The points to be mined
    :param output_thread: 
    :param distance_alg: Distance algorithm used in calculation
    :param max_centroids: The number of centroids to start mining with. Defaults to 256 as that is the maximum
                                number of colours image_utils.map_to_paletted_images will accept
    :return: A list of colours that best represent the image
    """

    min_movement = int(min_movement)
    max_centroids = int(max_centroids)
    if max_centroids > 256 or max_centroids < 16:
        raise ValueError
    num_dimensions = len(points[0])

    # determine the size of the space. This assumes the space is dimensionally symmetric
    space_max = points[0][0]
    space_min = points[0][0]
    for point in points:
        for dimension in point:
            if dimension > space_max:
                space_max = dimension
            if dimension < space_min:
                space_min = dimension

    space_length = space_max - space_min + 1

    # determine the number of spheres across each dimension
    # the number of spheres will be equal to the largest number which is less than max_centroids where the number of
    # spheres along each dimensional axis is equal (eg. if num_dimensions = 3, the total number of spheres will be the
    # largest perfect cube number less than max_centroids, and spheres_per_dimension will be the cube root of that
    # number
    spheres_per_dimension = max_centroids**(1/num_dimensions)//1

    # map the spheres into the euclidean space
    # The radius is chosen such that spheres will be as large as possible without any two spheres overlapping initially
    radius = space_length/spheres_per_dimension/2
    centroids = map_centroids_into_space(radius, spheres_per_dimension, num_dimensions, space_min)
    space = EuclideanSpace(points, spheres_per_dimension, space_min, space_max)

    final_centroids = mine_final_centroids(space, centroids, distance_alg, radius, min_movement, output_thread)
    for centroid in final_centroids:
        for i in range(len(centroid)):
            centroid[i] = int(centroid[i])
    return final_centroids


def map_centroids_into_space(radius, spheres_per_dimension, num_dimensions, space_min):
    """
    Creates initial potential centroids equally spaced throughout the euclidian space
    :param radius: The radius of the spheres centred at each centroid
    :param spheres_per_dimension: The number of centroids in any single direction (eg, n dimensions and
                                  m spheres_per_dimension will yield a space containing m^n total spheres
    :param num_dimensions: Total number of dimensions in the euclidean space
    :param space_min: the minimum value of the minimum values of each dimension in the space
    :return: A set of points equally distributed in the space
    """
    centroids = []
    counters = [0]*num_dimensions

    for i in range(int(spheres_per_dimension**num_dimensions)):
        centroids.append([])
        for j in range(num_dimensions):
            centroids[i].append(space_min + radius + radius*counters[j]*2)
        counters = increment_counters(counters, spheres_per_dimension)
    return centroids


def increment_counters(array, max_val):
    """
    If you imagine an array of integers as the odometer in a car where the least significant digit is stored in array[0]
    this methods increments that odometer by one
    :param array: The odometer
    :param max_val: The maximum value of any one digit in the array
    :return: The incremented odometer
    """
    for i in range(len(array)):
        if array[i] < max_val - 1:
            array[i] += 1
            return array
        else:
            array[i] = 0
        i += 1


def mine_final_centroids(space, centroids, distance_alg, radius, min_movement, output_thread):
    final_centroids = []
    for i in range(len(centroids)):
        output_thread.put("Moving centroid %d of %d" % (i+1, len(centroids)))
        settled = False
        current_centroid = centroids[i]
        iteration = 1
        while not settled:
            potential_points_in_sphere = space.get_points_in_range(current_centroid, radius)
            points_in_sphere = get_points_in_sphere(potential_points_in_sphere, current_centroid, distance_alg, radius)
            if len(points_in_sphere) is 0:
                break
            average = get_average_of_points(points_in_sphere)
            distance_moved = distance_alg(average, current_centroid)
            current_centroid = average
            output_thread.put("Moving centroid %d of %d\nIteration: %d, Shift: %f.2" % (i+1, len(centroids), iteration, distance_moved))
            iteration += 1
            if distance_moved < min_movement:
                final_centroids.append(current_centroid)
                settled = True

    output_thread.put("Pruning similar centroids")
    prune_similar_points_by_distance(final_centroids, distance_alg, min_movement)
    output_thread.put("%d distinct colors found\nDrawing new image" % len(final_centroids))
    return final_centroids


def get_points_in_sphere(points, center, distance_alg, radius):
    """
    Find all the points within a radius of the center
    :param points: The entire set of points in the space
    :param center: The center of the sphere
    :param distance_alg: The distance algorithm to use
    :param radius: the radius of the sphere
    :return: The set of points within the sphere
    """
    points_in_sphere = []
    for point in points:
        if distance_alg(point, center) <= radius:
            points_in_sphere.append(point)
    return points_in_sphere


def get_start_point(points, center, radius, min_val, max_val):
    if abs(min_val - max_val) < 10:
        return min_val
    if center[0] - radius < points[0][0]:
        return min_val
    center_point_of_array = int((max_val + min_val) / 2)
    if points[center_point_of_array][0] < center[0] - radius:
        return get_start_point(points, center, radius, center_point_of_array, max_val)
    else:
        return get_start_point(points, center, radius, min_val, center_point_of_array)


def get_average_of_points(points):
    """
    Get the average value of a set of points in euclidean space
    :param points: The set of points
    :return: The average
    """
    num_dimensions = len(points[0])
    average_point = [0] * num_dimensions
    for point in points:
        for i in range(num_dimensions):
            average_point[i] += point[i]
    for i in range(num_dimensions):
        average_point[i] /= len(points)
    return average_point


def prune_similar_points_by_distance(centroids, distance_alg, distinct_distance):
    """
    Remove centroids from the set based on the euclidean distance between centers
    :param centroids: Set of sphere centre points
    :param distance_alg: the distance algorithm to use
    :param distinct_distance: How far away two points must be to be considered distinct
    :return: Nothing, sets are changed in place
    """
    for i in range(len(centroids)):
        for j in range(i+1, len(centroids)):
            if distance_alg(centroids[i], centroids[j]) < distinct_distance:
                centroids[i] = None
                break
    while None in centroids:
        centroids.remove(None)


def first(elem):
    return elem[0]
