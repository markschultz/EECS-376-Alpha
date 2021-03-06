'''
Created on Apr 1, 2012

@author: Devin Schwab
'''
import unittest
import roslib
roslib.load_manifest('velocity_profiler_alpha')

from main import computeTrajectory,max_v_w
from msg_alpha.msg._PathSegment import PathSegment as PathSegmentMsg
from geometry_msgs.msg._Twist import Twist as TwistMsg
from geometry_msgs.msg._Point import Point as PointMsg
from tf.transformations import quaternion_from_euler
from math import pi

RATE = 20.0

class Test(unittest.TestCase):


    def setUp(self):
        self.currSeg = PathSegmentMsg()
        
        self.currSeg.seg_number = 1
        
        # set the initial tangent angle
        init_quat = quaternion_from_euler(0,0,0.0)
        self.currSeg.init_tan_angle.w = init_quat[3]
        self.currSeg.init_tan_angle.x = init_quat[0]
        self.currSeg.init_tan_angle.y = init_quat[1]
        self.currSeg.init_tan_angle.z = init_quat[2]
        
        self.nextSeg = PathSegmentMsg()
        
        self.nextSeg.seg_number = 2
        
        init_quat = quaternion_from_euler(0,0,0.0)
        self.currSeg.init_tan_angle.w = init_quat[3]
        self.currSeg.init_tan_angle.x = init_quat[0]
        self.currSeg.init_tan_angle.y = init_quat[1]
        self.currSeg.init_tan_angle.z = init_quat[2]

    def tearDown(self):
        pass

    def test_LINE_None(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 4.0
        self.currSeg.max_speeds.linear.x = 1
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg)
        
        self.assertAlmostEqual(sVAccel, 0.25, delta=.01)
        self.assertAlmostEqual(sVDecel, 0.75, delta=.01)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel, 1.0)
    
    def test_ARC_None(self):
        self.currSeg.seg_type = PathSegmentMsg.ARC
        self.currSeg.seg_length = pi/2.0
        self.currSeg.max_speeds.linear.x = 1
        self.currSeg.max_speeds.angular.z = .5
        self.currSeg.curvature = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg)
        
        self.assertAlmostEqual(sVAccel, 0.1592, delta=.0001)
        self.assertAlmostEqual(sVDecel, 0.8408, delta=.0001)
        self.assertAlmostEqual(sWAccel, sVAccel, delta=.0001)
        self.assertAlmostEqual(sWDecel, sVDecel, delta=.0001)
        
    def test_SPIN_None(self):
        self.currSeg.seg_type = PathSegmentMsg.SPIN_IN_PLACE
        self.currSeg.seg_length = pi/2.0
        self.currSeg.max_speeds.linear.x = 0.0
        self.currSeg.max_speeds.angular.z = .5
        self.currSeg.curvature = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg)
        
        self.assertEquals(sVDecel,1.0)
        self.assertEquals(sVAccel,0.0)
        self.assertAlmostEqual(sWAccel, 0.1592,delta=0.001)
        self.assertAlmostEqual(sWDecel, 1-0.1592,delta=0.001)
        
    def test_posLINE_LINE_GreaterThan(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 4.0
        self.currSeg.max_speeds.linear.x = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.LINE
        self.nextSeg.seg_length = 3.0
        self.nextSeg.max_speeds.linear.x = 2.0
        self.nextSeg.accel_limit = 0.5
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertEquals(sVDecel,1.0)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        self.assertTrue(sVDecel > sVAccel)
        
    def test_posLINE_LINE_SameAs(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 4.0
        self.currSeg.max_speeds.linear.x = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.LINE
        self.nextSeg.seg_length = 1.0
        self.nextSeg.max_speeds.linear.x = 1.0
        self.nextSeg.accel_limit = 0.7
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, .25, delta=.01)
        self.assertEquals(sVDecel,1.0)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_posLINE_LINE_LessThan(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 4.0
        self.currSeg.max_speeds.linear.x = 2.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.LINE
        self.nextSeg.seg_length = 1.0
        self.nextSeg.max_speeds.linear.x = 0.5
        self.nextSeg.accel_limit = 0.7
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertEquals(sVAccel,1.0)
        self.assertEquals(sVDecel,0.4375)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_posLINE_LINE_OppositeSign(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 6.0
        self.currSeg.max_speeds.linear.x = 2.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.LINE
        self.nextSeg.seg_length = 1.0
        self.nextSeg.max_speeds.linear.x = -1.0
        self.nextSeg.accel_limit = 0.7
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, 0.666, delta = 0.001)
        self.assertAlmostEqual(sVDecel, 0.333, delta = 0.001)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_negLINE_LINE_GreaterThan(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 4.0
        self.currSeg.max_speeds.linear.x = -1.0
        self.currSeg.accel_limit = -0.5
        self.currSeg.decel_limit = 0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.LINE
        self.nextSeg.seg_length = 3.0
        self.nextSeg.max_speeds.linear.x = -2.0
        self.nextSeg.accel_limit = -0.5
        self.nextSeg.decel_limit = 0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertEquals(sVDecel,1.0)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        self.assertAlmostEqual(sVAccel, 0.25, delta=.01)
        
    def test_negLINE_LINE_SameAs(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 4.0
        self.currSeg.max_speeds.linear.x = -1.0
        self.currSeg.accel_limit = -0.5
        self.currSeg.decel_limit = 0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.LINE
        self.nextSeg.seg_length = 1.0
        self.nextSeg.max_speeds.linear.x = -1.0
        self.nextSeg.accel_limit = -0.7
        self.nextSeg.decel_limit = 0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, .25, delta=.01)
        self.assertEquals(sVDecel,1.0)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_negLINE_LINE_LessThan(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 4.0
        self.currSeg.max_speeds.linear.x = -2.0
        self.currSeg.accel_limit = -0.5
        self.currSeg.decel_limit = 0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.LINE
        self.nextSeg.seg_length = 1.0
        self.nextSeg.max_speeds.linear.x = -0.5
        self.nextSeg.accel_limit = -0.7
        self.nextSeg.decel_limit = 0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertEquals(sVAccel,1.0)
        self.assertEquals(sVDecel,0.4375)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_negLINE_LINE_OppositeSign(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 6.0
        self.currSeg.max_speeds.linear.x = -2.0
        self.currSeg.accel_limit = -0.5
        self.currSeg.decel_limit = 0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.LINE
        self.nextSeg.seg_length = 1.0
        self.nextSeg.max_speeds.linear.x = 1.0
        self.nextSeg.accel_limit = 0.7
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, 0.666, delta = 0.001)
        self.assertAlmostEqual(sVDecel, 0.333, delta = 0.001)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_posLINE_ARC_GreaterThan(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 6.0
        self.currSeg.max_speeds.linear.x = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.ARC
        self.nextSeg.seg_length = 1.0
        self.nextSeg.curvature = 1.0
        self.nextSeg.max_speeds.linear.x = 3.0
        self.nextSeg.max_speeds.angular.z = 2.0
        self.nextSeg.accel_limit = 100.0 # this number would never actually be this large
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, 0.1667, delta = 0.0001)
        self.assertAlmostEqual(sVDecel, 1.0, delta = 0.0001)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_posLINE_ARC_SameAs(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 6.0
        self.currSeg.max_speeds.linear.x = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.ARC
        self.nextSeg.seg_length = 1.0
        self.nextSeg.curvature = 1.0
        self.nextSeg.max_speeds.linear.x = 1.0
        self.nextSeg.max_speeds.angular.z = 1.0
        self.nextSeg.accel_limit = 20.0
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, 0.1667, delta = 0.0001)
        self.assertAlmostEqual(sVDecel, 1.0, delta = 0.0001)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_posLINE_ARC_LessThan(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 6.0
        self.currSeg.max_speeds.linear.x = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.ARC
        self.nextSeg.seg_length = 1.0
        self.nextSeg.curvature = 1.0
        self.nextSeg.max_speeds.linear.x = 2.0
        self.nextSeg.max_speeds.angular.z = 2.0
        self.nextSeg.accel_limit = 0.7
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, 0.1667, delta = 0.0001)
        self.assertAlmostEqual(sVDecel, 0.8448, delta = 0.0001)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_posLINE_ARC_OppositeSign(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 6.0
        self.currSeg.max_speeds.linear.x = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.ARC
        self.nextSeg.seg_length = 1.0
        self.nextSeg.curvature = -1.0
        self.nextSeg.max_speeds.linear.x = 2.0
        self.nextSeg.max_speeds.angular.z = -2.0
        self.nextSeg.accel_limit = 0.7
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, 0.1667, delta = 0.0001)
        self.assertAlmostEqual(sVDecel, 0.8448, delta = 0.0001)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_LINE_SPIN_GreaterThan(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 4.0
        self.currSeg.max_speeds.linear.x = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.SPIN_IN_PLACE
        self.nextSeg.seg_length = pi/2
        self.nextSeg.curvature = 1.0
        self.nextSeg.max_speeds.linear.x = 0.0
        self.nextSeg.max_speeds.angular.z = 2.0
        self.nextSeg.accel_limit = 0.7
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, 0.2500, delta = 0.0001)
        self.assertAlmostEqual(sVDecel, 0.7500, delta = 0.0001)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_LINE_SPIN_SameAs(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 4.0
        self.currSeg.max_speeds.linear.x = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.SPIN_IN_PLACE
        self.nextSeg.seg_length = pi/2
        self.nextSeg.curvature = 1.0
        self.nextSeg.max_speeds.linear.x = 0.0
        self.nextSeg.max_speeds.angular.z = 1.0
        self.nextSeg.accel_limit = 0.7
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, 0.2500, delta = 0.0001)
        self.assertAlmostEqual(sVDecel, 0.7500, delta = 0.0001)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_LINE_SPIN_LessThan(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 4.0
        self.currSeg.max_speeds.linear.x = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.SPIN_IN_PLACE
        self.nextSeg.seg_length = pi/2
        self.nextSeg.curvature = 1.0
        self.nextSeg.max_speeds.linear.x = 0.0
        self.nextSeg.max_speeds.angular.z = 0.5
        self.nextSeg.accel_limit = 0.7
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, 0.2500, delta = 0.0001)
        self.assertAlmostEqual(sVDecel, 0.7500, delta = 0.0001)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_LINE_SPIN_OppositeSign(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 4.0
        self.currSeg.max_speeds.linear.x = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = PathSegmentMsg.SPIN_IN_PLACE
        self.nextSeg.seg_length = pi/2
        self.nextSeg.curvature = 1.0
        self.nextSeg.max_speeds.linear.x = 0.0
        self.nextSeg.max_speeds.angular.z = -2.0
        self.nextSeg.accel_limit = -0.7
        self.nextSeg.decel_limit = 0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, 0.2500, delta = 0.0001)
        self.assertAlmostEqual(sVDecel, 0.7500, delta = 0.0001)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_posARC_LINE_GreaterThan(self):
        self.fail("Unit test not yet implemented")
        
    def test_posARC_LINE_SameAs(self):
        self.fail("Unit test not yet implemented")
        
    def test_posARC_LINE_LessThan(self):
        self.fail("Unit test not yet implemented")
        
    def test_posARC_LINE_OppositeSign(self):
        self.fail("Unit test not yet implemented")
        
    def test_posARC_ARC_GreaterThan(self):
        self.fail("Unit test not yet implemented")
        
    def test_posARC_ARC_SameAs(self):
        self.fail("Unit test not yet implemented")
        
    def test_posARC_ARC_LessThan(self):
        self.fail("Unit test not yet implemented")
        
    def test_posARC_ARC_OppositeSign(self):
        self.fail("Unit test not yet implemented")
        
    def test_posARC_SPIN_GreaterThan(self):
        self.fail("Unit test not yet implemented")
        
    def test_posARC_SPIN_SameAs(self):
        self.fail("Unit test not yet implemented")
        
    def test_posARC_SPIN_LessThan(self):
        self.fail("Unit test not yet implemented")
        
    def test_posARC_SPIN_OppositeSign(self):
        self.fail("Unit test not yet implemented")
        
    def test_posSPIN_LINE_GreaterThan(self):
        self.fail("Unit test not yet implemented")
        
    def test_posSPIN_LINE_SameAs(self):
        self.fail("Unit test not yet implemented")
        
    def test_posSPIN_LINE_LessThan(self):
        self.fail("Unit test not yet implemented")
        
    def test_posSPIN_LINE_OppositeSign(self):
        self.fail("Unit test not yet implemented")
        
    def test_posSPIN_ARC_GreaterThan(self):
        self.fail("Unit test not yet implemented")
        
    def test_posSPIN_ARC_SameAs(self):
        self.fail("Unit test not yet implemented")
        
    def test_posSPIN_ARC_LessThan(self):
        self.fail("Unit test not yet implemented")
        
    def test_posSPIN_ARC_OppositeSign(self):
        self.fail("Unit test not yet implemented")
        
    def test_posSPIN_SPIN_GreaterThan(self):
        self.fail("Unit test not yet implemented")
        
    def test_posSPIN_SPIN_SameAs(self):
        self.fail("Unit test not yet implemented")
        
    def test_posSPIN_SPIN_LessThan(self):
        self.fail("Unit test not yet implemented")
        
    def test_posSPIN_SPIN_OppositeSign(self):
        self.fail("Unit test not yet implemented")
        
    def test_LINE_Unknown(self):
        self.currSeg.seg_type = PathSegmentMsg.LINE
        self.currSeg.seg_length = 4.0
        self.currSeg.max_speeds.linear.x = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = 4
        self.nextSeg.seg_length = pi/2
        self.nextSeg.curvature = 1.0
        self.nextSeg.max_speeds.linear.x = 0.0
        self.nextSeg.max_speeds.angular.z = 2.0
        self.nextSeg.accel_limit = 0.7
        self.nextSeg.decel_limit = -0.5
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        self.assertAlmostEqual(sVAccel, 0.2500, delta = 0.0001)
        self.assertAlmostEqual(sVDecel, 0.7500, delta = 0.0001)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_posARC_Unknown(self):
        self.currSeg.seg_type = PathSegmentMsg.ARC
        self.currSeg.seg_length = pi/2
        self.currSeg.curvature = 2.0
        self.currSeg.max_speeds.linear.x = 1.0
        self.currSeg.max_speeds.angular.z = 1.0
        self.currSeg.accel_limit = 0.5
        self.currSeg.decel_limit = -0.5
        
        self.nextSeg.seg_type = 4
        
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        
        # these numbers may not be right
        self.assertAlmostEqual(sVAccel, 0.25, delta = 0.0001)
        self.assertAlmostEqual(sVDecel, 0.7500, delta = 0.0001)
        self.assertEquals(sWAccel,0.0)
        self.assertEquals(sWDecel,1.0)
        
    def test_posSPIN_Unknown(self):
        self.fail("Unit test not yet implemented")
        
    def test_None(self):
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        self.assertEqual(sVAccel, 0.0)
        self.assertEqual(sVDecel, 0.0)
        self.assertEqual(sWAccel, 0.0)
        self.assertEqual(sWDecel, 0.0)
        
    def test_Unknown(self):
        (sVAccel,sVDecel,sWAccel,sWDecel) = computeTrajectory(self.currSeg, self.nextSeg)
        self.assertEqual(sVAccel, 0.0)
        self.assertEqual(sVDecel, 0.0)
        self.assertEqual(sWAccel, 0.0)
        self.assertEqual(sWDecel, 0.0)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()