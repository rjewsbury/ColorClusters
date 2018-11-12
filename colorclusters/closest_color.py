from math import inf
from colorclusters.distance import euclidean


def get_closest_color_index(pixel, colors, distance=euclidean):
    min_dist = inf
    index = -1
    # compare against each color, and choose the closest
    for i, color in enumerate(colors):
        dist = distance(pixel, color)
        if dist < min_dist:
            min_dist = dist
            index = i
    return index


def map_pixels_to_closest_color_index(pixels, colors, distance=euclidean):
    data = []
    color_map = {}
    for pixel in list(pixels):
        # if we've already computed the nearest color, use it
        if pixel in color_map:
            data.append(color_map[pixel])
        else:
            index = get_closest_color_index(pixel, colors, distance)
            # remember the result
            color_map[pixel] = index
            data.append(index)
    return data