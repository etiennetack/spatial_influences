"""
This module contains the functionality to find the distance between thematic (textual) attributes. 
    
Distance Functions:
    - ``Levenshtein Distance`` `[code] <https://stackabuse.com/levenshtein-distance-and-text-similarity-in-python/>`_.


"""
import numpy as np

def levenshtein_distance(seq1, seq2):
    '''
    Calculates the Levenshtein distance between two input strings (e.g. the names of matching buildings).  
    
    Args:
        - **seq1** (*str*): First polygon's thematic attribute value.
        - **seq2** (*str*): Second polygon's thematic attribute value.
    
    Returns:
        - **int**: The Levenshtein distance between seq1 and seq2 
    '''   
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros ((size_x, size_y))
    for x in range(size_x):
        matrix [x, 0] = x
    for y in range(size_y):
        matrix [0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x-1] == seq2[y-1]:
                matrix [x,y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y-1],
                    matrix[x, y-1] + 1
                )
            else:
                matrix [x,y] = min(
                    matrix[x-1,y] + 1,
                    matrix[x-1,y-1] + 1,
                    matrix[x,y-1] + 1
                )
    
    return (matrix[size_x - 1, size_y - 1])