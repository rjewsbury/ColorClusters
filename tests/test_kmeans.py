from PIL import Image
from colorclusters import distance
from colorclusters.image_utils import map_index_to_paletted_image
from colorclusters.k_means import KMeans
from timeit import default_timer

img = Image.open("./images/flower.png")

algorithm = KMeans(16,list(img.getdata()),distance.euclidean)

start = default_timer()
algorithm.compute_until_max_distance(5, True)
end = default_timer()
print((end-start)//60,"minutes",round((end-start)%60,3),"seconds")

img = map_index_to_paletted_image(img, algorithm.get_clustering(), algorithm.get_centroids())

# save the indexed result
img.save("./images/post_flower_test.png")
