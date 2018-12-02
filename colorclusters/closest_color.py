from math import inf
from colorclusters.distance import euclidean


def get_sum_squared_error(pixels, clustering, centroids, distance=euclidean):
    error = 0
    for i, pixel in zip(clustering, pixels):
        error += distance(centroids[i], pixel) ** 2
    return error

def get_closest_color_index(pixel, colors, distance=euclidean):
    """
    Computes the closest color to a point out of a given color list
    :param pixel: an n-tuple representing a point
    :param colors: a list of n-tuples to compare against
    :param distance: a distance function. Uses euclidean distance by default
    :return: the index in the color array of the closest color
    """
    min_dist = inf
    index = -1
    # compare against each color, and choose the closest
    for i, color in enumerate(colors):
        dist = distance(pixel, color)
        if dist < min_dist:
            min_dist = dist
            index = i
    return index


def map_pixels_to_closest_color_index(pixels, colors, output_queue=None, distance=euclidean):
    """
    Computes the closest color for all of a list of points to a color list.
    Remembers past results for repeat pixels to improve performance.
    :param pixels: a list of n-tuples representing points
    :param colors: a list of n-tuples to compare against
    :param output_queue: Queue for printing info to the UI
    :param distance: a distance function. uses euclidean by default
    :return: a list of color array indexes, representing the closest color to each pixel
    """
    data = []
    color_map = {}
    percent_complete = 0
    num_pixels = len(pixels)
    for i, pixel in enumerate(list(pixels)):
        if output_queue is not None:
            percent = int((i/num_pixels)*100)
            if percent > percent_complete:
                percent_complete = percent
                output_queue.put("%d distinct colors found\nDrawing new image\nRemapping pixels: %d%% complete" % (len(colors), percent_complete))
        # if we've already computed the nearest color, use it
        if pixel in color_map:
            data.append(color_map[pixel])
        else:
            index = get_closest_color_index(pixel, colors, distance)
            # remember the result
            color_map[pixel] = index
            data.append(index)
    return data