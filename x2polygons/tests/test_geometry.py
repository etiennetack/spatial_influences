# -*- coding: utf-8 -*-

# CMD: python -m unittest test.test_metrics

import sys, os 


import unittest


testdir = os.path.dirname(__file__)
srcdir = '../../'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

from x2polygons.polygon_distance import * 
from x2polygons.plot import *
from x2polygons.geometry import *

# -------------------------------
# 1.
# setUp() --> test --> tearDown()
   # Before running each test, the setUp() function works.
   # Then, the test
   # And finally - tearDown

# 2.
# Note: tests do not necessarily run in the order given!
# --> THEREFORE, tests MUST BE ISOLATED from one another

# 3.
# setUp and tearDown CLASS METHODS
   # It would also be nice if we have something that runs BEFORE EVERYTHING (not like setUp() which runs before every test)
   # and AFTER EVERYTHING

import math
class TestGeometry(unittest.TestCase):
   
    
    
    # setUp() will run BEFORE each test
    # Here we can define the common test cases
    def setUp(self):
        print("setUp")
        
        # Polygon 1: Simple square - CCW - total must be 360               
        self.p1 = Polygon([(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)])        
        self.p1_scaled = Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
        # Polygon 1 - CW - total must be -360 when turn function is used
        
        # Polygon 2: - notch included
        self.p2 = Polygon([(0, 0), (5, 0), (5, 5), (4, 5), (4, 6), (2, 6), (2, 5), (0, 5), (0, 0)])
        
        
        
    
    def test_Perimeter(self):
        #setUp() function will work
        # So, we have self.emp_1
        print("test Perimeter")
        
        self.assertEqual(polygon_perimeter(self.p1), 20)
        self.assertEqual(polygon_perimeter(self.p2), 22)
    
        
    def test_Area(self):
        #setUp() function will work
        # So, we have self.emp_1
        print("test x2 Area")
        
        self.assertEqual(x2_areas(self.p1, self.p2)["TP"], 25)
        
        
        
if __name__ == '__main__':
    unittest.main()