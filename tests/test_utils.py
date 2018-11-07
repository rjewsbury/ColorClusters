from PIL import Image
from colorclusters import distance
from colorclusters.image_utils import map_to_paletted_image as map_img

# creates a gradient image
img = Image.new('RGBA',(255,255))
img.putdata([(x,y,x,y//2+128) for x in range(255) for y in range(255)])
img.save("./pre_map_test.png")

# arbitrary colors used
colors = [(10,10,10,150),(240,0,240,200),(30,180,30,180),(255,255,255,255)]
img = map_img(img, colors, distance.chebyshev)

#save the indexed result
img.save("./post_map_test.png")