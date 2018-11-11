from PIL import Image
import math
from colorclusters import distance
from colorclusters.image_utils import map_index_to_paletted_image
from colorclusters.k_means import KMeans

# creates a gradient image
img = Image.new('RGB', (255, 255))
img.putdata([
    (int(255 * math.sin((x - y)/256))
     ,int(255 * math.cos((x + y)/256))
     ,int(255 * math.sin((x + y)/256))
     #,(abs((y - 127)) + abs(x - 127))//4+170
    )
    for x in range(255) for y in range(255)])
img.save("./images/pre_kmean_test.png")

algorithm = KMeans(4,list(img.getdata()),distance.euclidean)

algorithm.compute_until_max_distance(5)

img = map_index_to_paletted_image(img, algorithm.get_clustering(), algorithm.get_centroids())

# save the indexed result
img.save("./images/post_kmean_test.png")
