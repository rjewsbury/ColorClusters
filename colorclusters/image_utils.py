from PIL import Image, ImagePalette
from .distance import euclidean
from .closest_color import map_pixels_to_closest_color_index


def map_index_to_paletted_image(size, index_data, colors):
    """
    Creates a paletted image from the given data
    :param size: an (x,y) tuple
    :param index_data: a list of indexes of length x*y, corresponding to indexes in the color array
    :param colors: a list of (r,g,b) or (r,g,b,a) tuples
    :return: a paletted image with the given pixel data
    """
    if not (0 < len(colors) <= 256):
        raise ValueError('Number of colors out of bounds')

    # store the result in a paletted image
    palette_image = Image.new('P', size)

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
    # record indexed data
    palette_image.putdata(index_data)

    return palette_image


def map_to_paletted_image(img, colors, output_queue, distance=euclidean):
    """
    Converts an RGB or RGBA image to an Indexed-Color image.
    :param img: an Image object with 'RGB' or 'RGBA' mode
    :param colors: a list of 3-tuples (r,g,b) or 4-tuples (r,g,b,a) used as the color palette
    :param distance: the function used to compute the closest palette color for each pixel's color
    :return: an indexed-color image using the given colors for the palette
    """
    # palettes work off of RGB values, so the image must be in this format
    if img.mode not in ('RGB', 'RGBA'):
        raise ValueError('Incompatible image format')

    index_data = map_pixels_to_closest_color_index(list(img.getdata()), colors, output_queue, distance)

    return map_index_to_paletted_image(img.size, index_data, colors)


def add_transparency_grid(img=None, *_, dest=(0,0), source=(0,0),
                          grid_spacing=8, size=None, color1=0xFFA9A9A9, color2=0xFFC9C9C9):
    """
    Draws a grid of grey squares behind a transluscent image, with way more optional parameters
    than I'm ever going to use. See the source if you really want to know what they are.
    :param img: an RGBA image
    :return: a completely opaque image, with grey squares filling in transparency
    """
    # figure out how big to make the grid
    if size is None and img is None:
        raise ValueError('No image or size given')
    elif size is None:
        size = img.size

    # draw the grey grid
    color_diff = color2-color1
    bg_img = Image.new("RGBA", size)
    bg_img.putdata(
        [color1 + (x // grid_spacing + y // grid_spacing) % 2 * color_diff
         for x in range(size[0]) for y in range(size[1])])

    # draw the RGBA image on top of it
    if img is not None:
        bg_img.alpha_composite(img.convert('RGBA'),dest,source)
    return bg_img