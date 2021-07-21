# Color Clusters

CPSC 473 - Data Mining



### Overview

​	This project uses cluster mining techniques to convert RGB and RGBA images to index color images, reducing the file size. either the *K-Means* or *Mean Shift* algorithm can be used to produce a compressed, paletted copy of their original image. 



### K-Means

​	This method begins by distributing k "mean-points" through the color space in a way that spreads them out among the colors of the image. Then it iterates through the following process:

	- Assign each color to its nearest mean-point
	- For each mean-point, take the weighted average of all the colors assigned to it
	- Move each mean-point to its average
	- Repeat until no mean-point moves more than some predefined amount

| Original 24-bit RGB (10,891 kb)  | K-means 4-bit Indexed (721 kb)          |
| -------------------------------- | :-------------------------------------- |
| ![Original](.\assets\flower.png) | ![Indexed](.\assets\flower_kmean16.png) |

By taking the averages of all points in the space, K-means will tend to do well representing the dominant colors of an image.



### Mean Shift

​	This method starts with centroids uniformly distributed in the color space, then it iterates through the following process:

- Find all the colors within a fixed distance of the centroid
- Move the centroid to the average
- Repeat until the centroid no longer moves
- Repeat for each centroid
- Prune the centroids that have converged to the same color

| Original 24-bit RGB (1032 kb)                                | Mean-Shift 8-bit Indexed (99 colors, 182 kb)                 |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| ![Original](D:\ryley\PycharmProjects\ColorClusters\assets\rainbow_cat.png) | ![Indexed](D:\ryley\PycharmProjects\ColorClusters\assets\rainbow_cat_meanshift99.png) |

For images with many distinct color clusters, mean shift is able to quickly determine how many colors are necessary, and what they should be.
