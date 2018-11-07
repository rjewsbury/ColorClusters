"""
This module provides a collection of distance formulas for comparing colors.
"""


def _default_scale():
    """
    A generator for the 1-vector in arbitrary dimensions. used as a default value for the scaled norm distance.
    :return: a generator that always returns 1
    """
    while True:
        yield 1


def norm_distance(p=2, scale=_default_scale()):
    """
    Creates a function that computes the p-norm distance after scaling the input vectors.
    The distance function takes two vectors x,y as tuples. if they are different lengths, only the shared
    dimensions are used for the computation (i.e ||(x,y,z)-(x,y,z,w)|| would ignore the w-dimension)
    :param p:       the p-value used for the p-norm distance. must be >= 1 to preserve the triangle inequality
    :param scale:   a vector that scales the input vectors component-wise.
                        if dimensions are missing, they are treated as 0
    :return:        a p-norm distance function
    """

    def calculate_dist(x, y):
        dist = 0
        for xi, yi, si in zip(x, y, scale):
            dist += abs(si * (xi - yi)) ** p
        dist = dist ** (1 / p)
        return dist

    return calculate_dist


euclidean = norm_distance(2)
"""
Euclidean distance is a special case of 2-norm distance
Computes the straight line distance between two points
"""

manhattan = norm_distance(1)
"""
Manhattan distance (aka: Taxicab distance) is a special case of 1-norm distance.
Uses only cardinal directions to move between points
"""

def chebyshev(x, y):
    """
    Chebyshev distance (aka: Chessboard distance) behaves like a King moving on a chess board.
    square diagonals are treated as the same distance as square edges.
    """
    dist = 0
    for xi, yi in zip(x, y):
        if abs(xi - yi) > dist:
            dist = abs(xi - yi)
    return dist
