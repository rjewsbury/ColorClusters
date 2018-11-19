from colorclusters import distance, image_utils
from datastructures.EuclideanSpace import EuclideanSpace
from PIL import Image
from timeit import default_timer


def mine(points, distance_alg=distance.euclidean, max_centroids=256):
    """
    Uses the mean-shift algorithm to produce the set of average points that best represents the points given
    :param points: The points to be mined
    :param distance_alg: Distance algorithm used in calculation
    :param max_centroids: The number of centroids to start mining with. Defaults to 256 as that is the maximum
                                number of colours image_utils.map_to_paletted_images will accept
    :return: A list of colours that best represent the image
    """

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
    print(len(points))
    space = EuclideanSpace(points, spheres_per_dimension, space_min, space_max)
    print(space.total_points)

    final_centroids = find_final_centroids(space, centroids, distance_alg, radius)
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


def find_final_centroids(space, centroids, distance_alg, radius):
    """
    The core of the algorithm. Recursively move the centroids around until we find all local density maxima
    :param space: All data points in the space
    :param centroids: The potential local maxima
    :param distance_alg: The distance algorithm to use
    :param radius: The radius of every sphere centred at a centroid
    :return: The set of local density maxima
    """
    min_movement = 5
    print(min_movement)
    final_centroids = []
    while len(centroids) > 0:
        print(len(centroids))
        sets_of_points_in_spheres = [None]*len(centroids)

        for i, centroid in enumerate(centroids):
            if i % 10 == 0:
                print(i)
            potential_points_in_sphere = space.get_points_in_range(centroid, radius)
            points_in_sphere = get_points_in_sphere(potential_points_in_sphere, centroid, distance_alg, radius)
            if len(points_in_sphere) is 0:
                centroids[i] = None
                continue
            sets_of_points_in_spheres[i] = points_in_sphere
        while centroids.__contains__(None):
            centroids.remove(None)
        while sets_of_points_in_spheres.__contains__(None):
            sets_of_points_in_spheres.remove(None)

        centroids_to_remove = []
        for i, centroid in enumerate(centroids):
            average = get_average_of_points(sets_of_points_in_spheres[i])
            distance_moved = distance_alg(average, centroid)
            centroids[i] = average
            if distance_moved < min_movement:
                centroids_to_remove.append(centroids[i])
                final_centroids.append(centroids[i])
        for i in range(len(centroids_to_remove)):
            centroids.remove(centroids_to_remove[i])
    prune_similar_points_by_distance(final_centroids, distance_alg, radius)
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


def prune_similar_points_by_intersections_of_sets(centroids, sets_of_points_in_spheres):
    """
    Remove centroids from the set based on the similarity between the sets of points within their respective spheres
    :param centroids: The set of centre points
    :param sets_of_points_in_spheres: Sets of points contained in the spheres centred at individual centroids. The
    indices of the set correspond to the indices of centroids
    :return: Nothing
    """
    for i in range(len(sets_of_points_in_spheres)):
        for j in range(i+1, len(sets_of_points_in_spheres)):
            if percentage_similar(sets_of_points_in_spheres[i], sets_of_points_in_spheres[j]) > 0.9:
                centroids[i] = None
                sets_of_points_in_spheres[i] = None
                break
    while None in centroids:
        centroids.remove(None)
        sets_of_points_in_spheres.remove(None)


def percentage_similar(x, y):
    """
    A method to assess the similarity between two sets of points. Similarity is determined
    :param x: a set
    :param y: another set
    :return: the percentage similarity
    """
    if len(x) is 0 or len(y) is 0:
        return 0
    intersection = 0
    for item in x:
        if item in y:
            intersection += 1
    return intersection/max(len(y), len(x))


def prune_similar_points_by_distance(centroids, distance_alg, radius):
    """
    Remove centroids from the set based on the euclidean distance between centers
    :param centroids: Set of sphere centre points
    :param distance_alg: the distance algorithm to use
    :param radius: sphere radii
    :return: Nothing, sets are changed in place
    """
    for i in range(len(centroids)):
        for j in range(i+1, len(centroids)):
            if distance_alg(centroids[i], centroids[j]) < radius/50000:
                centroids[i] = None
                break
    while None in centroids:
        centroids.remove(None)


def first(elem):
    return elem[0]

if __name__ == "__main__":
    image = Image.open('/home/erik/workspace/ColorClusters/tests/git.png')
    pixels = list(image.getdata())
    print("picture loaded")
    start_time = default_timer()
    color_palette = mine(pixels, distance.euclidean)
    end_time = default_timer()
    print((end_time-start_time)//60,"minutes",round((end_time-start_time)%60,3),"seconds")
    new_image = image_utils.map_to_paletted_image(image, color_palette)
    new_image.convert('RGBA').show()
    new_image.save('/home/erik/workspace/ColorClusters/tests/after_mean_shift.png')
