# -*- coding: utf-8 -*-

# CMD: python -m unittest test.test_metrics

import sys, os 


import unittest


testdir = os.path.dirname(__file__)
srcdir = '../../'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

from x2polygons.thematic_distance import * 


import math
class TestThematicDistance(unittest.TestCase):
   
    
    
    # setUp() will run BEFORE each test
    # Here we can define the common test cases
    def setUp(self):
        print("setUp")
        
        # Polygon 1: Simple square - CCW - total must be 360               
        self.s1 = "Hacettepe University"
        self.s2 = "Hacettepe  University"
        self.s3 = "Hacettepe Univ."
        self.s4 = "Beytepe Campus"
        
    def test_Levenshtein(self):
        #setUp() function will work
        # So, we have self.emp_1
        print("test Levenshtein distance")
        
        self.assertEqual(levenshtein_distance(self.s1, self.s1), 0)
        self.assertEqual(levenshtein_distance(self.s2, self.s2), 0)
        
        self.assertEqual(levenshtein_distance(self.s1, self.s2), 1)
        
        self.assertEqual(levenshtein_distance(self.s1, self.s3), 6)
        
        self.assertEqual(levenshtein_distance(self.s1, self.s4), 13)
        
if __name__ == '__main__':
    unittest.main()