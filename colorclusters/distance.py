"""
This module provides a collection of distance formulas for comparing colors.
"""


def decode_string(string):
    alg = None
    try:
        # they may have tried to call distance functions, or create their own function
        alg = eval(string)
        # the algorithm must be a function
        if not callable(alg):
            alg = None
    except SyntaxError:
        alg = None
    return alg


def norm_distance(p=2):
    """
    Creates a function that computes the p-norm distance.
    The distance function takes two vectors x,y as tuples. if they are different lengths, only the shared
    dimensions are used for the computation (i.e ||(x,y,z)-(x,y,z,w)|| would ignore the w-dimension)
    :param p:       the p-value used for the p-norm distance. must be >= 1 to preserve the triangle inequality
    :return:        a p-norm distance function
    """

    def calculate_dist(x, y):
        dist = 0
        for xi, yi in zip(x, y):
            dist += abs(xi - yi) ** p
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


def scaled_distance(distance, scale_vector):
    """
    Creates a distance function that scales the input vectors before computing the distance
    :param distance: a distance function
    :param scale:   a vector that scales the input vectors component-wise.
                        if dimensions are missing, they are treated as 0
    :return: a new distance function
    """

    def calculate_dist(x, y):
        x = list(x)
        for i in range(len(x)):
            if i >= len(scale_vector):
                x[i] = 0
            else:
                x[i] *= scale_vector[i]
        y = list(y)
        for i in range(len(y)):
            if i >= len(scale_vector):
                y[i] = 0
            else:
                y[i] *= scale_vector[i]
        return distance(x, y)

    return calculate_dist


# shortened names
def norm(p=2):
    return norm_distance(p)


def scaled(distance, scale_vector):
    return scaled_distance(distance, scale_vector)
