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
class TestPolygonDistance(unittest.TestCase):
   
    
    
    # setUp() will run BEFORE each test
    # Here we can define the common test cases
    def setUp(self):
        print("setUp")
        
        # Polygon 1: Simple square - CCW - total must be 360               
        self.p1 = Polygon([(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)])        
        self.p1_scaled = Polygon([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)])
        # Polygon 1 - CW - total must be -360 when turn function is used
        self.p1_cw = Polygon([(0, 0), (0, 5), (5, 5), (5, 0), (0, 0)])  
        # Polygon 1 - more vertex       
        self.p1_more_vertex = Polygon([(0, 0), (1,0), (3,0), (5,0), (5, 2.5), (5, 5), (1, 5), (0,5), (0, 2), (0,1), (0, 0) ])
        self.p1_more_vertex_cw = Polygon([(0, 0), (0, 1), (0, 2), (0, 5), (1, 5), (5, 5), (5, 2.5), (5, 0), (3, 0), (1, 0)] )
        # Polygon 1: complex representation: different initial vertex & number of vertices
        self.p1_more_vertex_different_start = Polygon([(5,2), (5,3), (5, 5), (3, 5), (0, 5), (0, 0), (5, 0), (5, 1), (5,2)])
        
        self.p1_extension_1m = Polygon([(0,0), (5,0), (5,6), (0,6), (0,0)])
        self.p1_extension_1m_N_vertices = Polygon([(0,0), (5,0), (5,6), (4,6),(3,6), (2,6), (1,6), (0,6), (0,0)])
        
        # Polygon 2: - notch included
        self.p2 = Polygon([(0, 0), (5, 0), (5, 5), (4, 5), (4, 6), (2, 6), (2, 5), (0, 5), (0, 0)])
        # Polygon 3 - triangular notch
        self.p3 = Polygon([(0, 0), (5, 0), (5, 5), (3, 6), (0, 5), (0, 0)])
        # Polygon 4 
        self.p4 = Polygon([(0, 0), (5, 0), (5, 5), (4, 6), (2, 6), (0, 5), (0, 0)]) 
        # Complex polygon
        self.p5 = Polygon([(3,2), (2,4), (0,4), (0,8), (7,8), (5,7), (7,4), (7,2), (3,2)])
        self.p5_different_start = Polygon([(7,8), (0,8), (0,4), (2,4), (3,2), (7,2), (7,4), (5,7), (7,8) ])
        
        self.p6 = Polygon([(1,1), (4,1), (6,3),  (8,5), (4,6), (8,8), (3,8), (2,7), (1,7), (1,1)])
        self.p6_shifted = Polygon([(2,2), (5,2), (9,6), (5,7), (9,9), (4,9), (3,8), (2,8), (2,2)])
        
        
    
    def test_Chamfer(self):
        #setUp() function will work
        # So, we have self.emp_1
        print("test Chamfer distance")
        
        self.assertEqual(chamfer_distance(self.p1, self.p1_more_vertex_cw), 0)
        self.assertEqual(chamfer_distance(self.p1, self.p1_more_vertex_different_start), 0)
        
        
        #self.assertEqual(chamfer_distance(self.p2, self.p1, symmetrize = "number_of_nodes"), (10+2*math.sqrt(125)) / (2*8))

    
    def test_Hausdorff(self):
        print("test Hausdorff distance")
        
        # self.assertEqual(hausdorff_distance(self.p1, self.p1_more_vertex_cw), 0)
        # self.assertEqual(hausdorff_distance(self.p1, self.p1_more_vertex_different_start), 0)
        
        self.assertEqual(hausdorff_distance(self.p1, self.p2, symmetrise="min"), 0)
    

    def test_Polis(self):
        print("test Polis distance")
        
        self.assertEqual(polis_distance(self.p1, self.p1_more_vertex_cw), 0)
        self.assertEqual(polis_distance(self.p1, self.p1_extension_1m_N_vertices, symmetrise = 'max'), 0.75)
        
        self.assertEqual(polis_distance(self.p1_extension_1m, self.p1, symmetrise='min'), 0)
        
        # self.assertEqual(polis_distance(self.p1, self.p2), 0)
        # self.assertEqual(polis_distance(self.p2, self.p1), 20/8) #2.5
        # self.assertEqual(polis_distance(self.p2, self.p1, symmetrize = "average"), 2.5 / 2)
        # self.assertEqual(polis_distance(self.p3, self.p1), (3+3) / 6)
        # self.assertEqual(polis_distance(self.p3, self.p1, symmetrize = "average"),  1 / 2)
        
        # self.assertEqual(polis_distance(self.p1, self.p4), 0)
        # self.assertEqual(polis_distance(self.p4, self.p1), 3/5)
        
        # self.assertEqual(polis_distance(self.p1, self.p5), 0)
        # self.assertEqual(polis_distance(self.p5, self.p1), (3+3) / 4)
        #self.assertEquals(polis_distance(self.p1, self.p1_more_vertex), 0)
    
    def test_Turn_Function(self):
        # self.assertEqual(round(sum(turn_function(self.p1)["angles"])), 360)
        # self.assertEqual(round(sum(turn_function(self.p1_cw, ccw = True)["angles"])), 360)
        # self.assertEqual(round(sum(turn_function(self.p1_more_vertex)["angles"])), 360)
        # self.assertEqual(round(sum(turn_function(self.p1_more_vertex_cw)["angles"])), -360)
        # self.assertEqual(round(sum(turn_function(self.p1_more_vertex_different_start, ccw = True)["angles"])), 360)
        
        
        # self.assertEqual(round(sum(turn_function(self.p1, plot = True)["angles"])), 360)
        # self.assertEqual(round(sum(turn_function(self.p2, plot = True)["angles"])), 360)
        
        self.assertEqual(round(sum(turning_function(self.p6)["angles"])), 360)

        
        
    def test_distance_between_turn_functions(self):
        # p1_turn = turn_function(self.p1, ccw = True)
        # p1_v2_turn = turn_function(self.p1_more_vertex_cw, ccw=True, plot=True )
        # # p1_complex = turn_function(self.p1_more_vertex_different_start, ccw = True)
        # p2_turn = turn_function(self.p2, ccw = True)
        # self.assertEqual(distance_between_turn_functions(p1_turn, p1_v2_turn)["total_distance"], 0)
        
        p6_turn = turning_function(self.p6, plot=True, ccw=True)
        # p6_shifted_turn = turn_function(self.p6_shifted, ccw=True)
        
        
        self.assertEqual(turning_function_distance(self.p1, self.p1_scaled), 0)
        self.assertEqual(turning_function_distance(self.p1, self.p1_cw), 0)
        self.assertEqual(turning_function_distance(self.p1, self.p1_more_vertex), 0)
        self.assertEqual(turning_function_distance(self.p1, self.p1_more_vertex_different_start), 0)
        
        self.assertEqual(turning_function_distance(self.p5, self.p5_different_start), 0)
        
        self.assertEqual(turning_function_distance(self.p6, self.p6_shifted), 0)
        
        
        
if __name__ == '__main__':
    unittest.main()