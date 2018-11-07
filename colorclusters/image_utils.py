from math import inf
from PIL import Image, ImagePalette
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

def map_to_paletted_image(img, colors, distance=euclidean):
    """
    Converts an RGB or RGBA image to an Indexed-Color image.
    :param img: an Image object with 'RGB' or 'RGBA' mode
    :param colors: a list of 3-tuples (r,g,b) or 4-tuples (r,g,b,a) used as the color palette
    :param distance: the function used to compute the closest palette color for each pixel's color
    :return: an indexed-color image using the given colors for the palette
    """

    if not (0 < len(colors) <= 256):
        raise ValueError('Number of colors out of bounds')

    # palettes work off of RGB values, so the image must be in this format
    if img.mode not in ('RGB', 'RGBA'):
        raise ValueError('Incompatible image format')

    # store the result in a paletted image
    palette_image = Image.new('P', img.size)

    # if there's a transparency channel, it needs to be recorded in img.info
    if len(colors[0]) > 3:
        transparency = [0] * 256
        transparency[0:len(colors)] = [color[3] for color in colors]
        palette_image.info['transparency'] = bytes(transparency)

    # store the RGB channels in an ImagePalette
    palette_data = [color[i] for i in range(3) for color in colors]
    palette = ImagePalette.ImagePalette('RGB', palette_data, 3 * len(colors))
    # use the indexed colors in the image palette
    palette_image.putpalette(palette)

    # map the pixels to the nearest palette color
    data = []
    color_map = {}
    for pixel in list(img.getdata()):
        # if we've already computed the nearest color, use it
        if pixel in color_map:
            data.append(color_map[pixel])
        else:
            index = get_closest_color_index(pixel, colors, distance)
            # remember the result
            color_map[pixel] = index
            data.append(index)

    # record indexed data
    palette_image.putdata(data)

    return palette_image
