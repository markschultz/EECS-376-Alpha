#include <ros/ros.h>
#include <iostream>
#include "lib_blob.h"
#include <msg_alpha/BlobDistance.h>
#include <sensor_msgs/CameraInfo.h>
#include <message_filters/subscriber.h>
#include <message_filters/synchronizer.h>
#include <message_filters/sync_policies/exact_time.h>
#include <message_filters/sync_policies/approximate_time.h>
#include <geometry_msgs/Twist.h>

#include <boost/format.hpp>

#include <vector>
#include <ctime>

// OpenCV includes
#include <image_transport/image_transport.h>
#include <image_transport/subscriber_filter.h>
#include <cv_bridge/cv_bridge.h>
#include <sensor_msgs/image_encodings.h>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/opencv.hpp>

// PCL includes
#include "pcl_ros/point_cloud.h"
#include <pcl/ros/conversions.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/octree.h>
#include <pcl/octree/octree_pointcloud.h>




using std::string;
namespace enc = sensor_msgs::image_encodings;
using namespace cv;

// Global variables here
ros::Publisher             cloud_pub_;
image_transport::Publisher image_pub_;
string window_name_;
cv_bridge::CvImagePtr cv_ptr; //conversion variable for ROS Image to cvImage

class KinectNode {
public:
  KinectNode();

  //member functions
  void imageCallback(const sensor_msgs::ImageConstPtr& msg);
  void detectStrap();
  pcl::PointXYZRGBA computeCentroids(pcl::PointCloud<pcl::PointXYZ>);
  pcl::PointXYZRGBA getSearchPoint(pcl::PointXYZRGBA);
  
private:
  ros::NodeHandle nh_;
  image_transport::ImageTransport it_;
  image_transport::Subscriber sub_;
  //image_transport::Publisher image_pub_;
  msg_alpha::BlobDistance blobDist;
  ros::Publisher blobPub;
  int params[10];
  int dilationIterations;
};

KinectNode::KinectNode():
  it_(nh_)
{
  ros::NodeHandle private_nh("~");
  private_nh.param("hl",params[0], 0);
  private_nh.param("hh",params[1], 255);
  private_nh.param("sl",params[2], 0);
  private_nh.param("sh",params[3], 255);
  private_nh.param("vl",params[4], 0);
  private_nh.param("vh",params[5], 255);
  private_nh.param("dilationIterations",dilationIterations,10);
  private_nh.param("sliceLength",params[7],5);
  private_nh.param("zTolLow",params[8],10);
  private_nh.param("zTolHigh",params[9],10);
  private_nh.param("gridSize",params[10], 255);


  std::cout << params[0] << params[1] << params[2] << params[3] << params[4] << params[5] << std::endl;
  std::cout << dilationIterations << std::endl;
  sub_ = it_.subscribe("in_image", 1, &KinectNode::imageCallback, this);
  //image_pub_ = it_.advertise("out_image", 1);
  blobPub = nh_.advertise<msg_alpha::BlobDistance>("blob_dist",1);
}



/* Function to receive Kinect Data
   @param The Image from the center
   @type sensor_msg
   @return nothing

*/
void KinectNode::imageCallback(const sensor_msgs::ImageConstPtr& image_msg)
{

  //Convert the image from ROS Format to OpenCV format
  try	{
    cv_ptr = cv_bridge::toCvCopy(image_msg, enc::BGR8);
  }
  catch (cv_bridge::Exception& e) {
    ROS_ERROR_STREAM("cv_bridge exception: " << e.what());
    return;
  }
}


/*
  Function to Highlight the path strap from Kinect Data
  @param none
  @type cv::Mat which is an OpenCV Matrix 
  @return an openCV Matrix of the image in black and white -- the path segment is white while the surrondings are black
  @author Eddie, Devin 
*/
void KinectNode::detectStrap()	
{

  cv::Mat output;
  try {
	
    cv::cvtColor(cv_ptr->image, output, CV_BGR2HSV);
	
    cv::Mat temp;

    //Make a vector of Mats to hold the invidiual B,G,R channels
    vector<Mat> mats;

    //Split the input into 3 separate channels
    split(temp, mats);
   
    //create the range of HSV values that determine the color we desire to threshold based on launch file params
    cv::Scalar lowerBound = cv::Scalar(params[0],params[2],params[4]);
    cv::Scalar upperBound = cv::Scalar(params[1],params[3],params[5]);

    //threshold the image based on the HSV values
    cv::inRange(output,lowerBound,upperBound,output);

    erode(output, output, Mat());

    dilate(output, output, Mat(), Point(-1,-1), dilationIterations);

    //	cv::imshow("view",output);
    //	cvWaitKey(5);

    //	return output;
  }

  catch (cv_bridge::Exception& e) {

    ROS_ERROR("Could not convert to 'bgr8'. Ex was %s", e.what());
  }
}

/*Function to computer centroids given a set of pixels 
  @param cloud
  @type PointCloud that has already been extracted to only look at the floor
  @return the closest centroid
  @type int
  @author Eddie
*/
pcl::PointXYZRGBA KinectNode::computeCentroids(pcl::PointCloud<pcl::PointXYZ> cloud)
{

  std::vector<int> centroids; //vector of each centroid computed
  std::vector<int> indicies;
  int closestCentroid; //the centroid closest to the robot
  pcl::PointXYZRGBA curSearchPoint; //coordinate value which we are currently computing the centroid for
  pcl::PointXYZRGBA closest; //the coords of the closet centroid


  //turn the points from the filtered cloud into an octree
  float resolution = 128.0f; //describes the smallest voxel at the lowest octree level
  pcl::octree::OctreePointCloud<pcl::PointXYZ> *octree;
						
  octree = (new pcl::octree::OctreePointCloud<pcl::PointXYZRGB>(resolution));
  octree->setInputCloud(cloud);
  octree->addPointsFromInputCloud();

 


  //Generate each point in the cloud and assign it to the search point
  //precondition: x,y,z are 0 referring to the xyz value of the point cloud
  //loop invariant xyz are each < the point cloud
  //postcondition: xyz refer to the very last point in the cloud
  for(int x = 0; x < cloud.points.size(); x++)
    {
      for(int y = 0; y < cloud.points.size(); y++)
	{
	  for(int z = 0; z < cloud.points.size(); z++)
	    {	
	      //establish what the point is in a point cloud data type
	      pcl::PointXYZRGBA searchPoint; 
	      searchPoint.x = x;
	      searchPoint.y = y;
	      searchPoint.z = z;
	
	      curSearchPoint = getSearchPoint(searchPoint); //save the value for use in the voxel search
	    }
	}	
    }	
  
	      
    
  //perform a neighboors within Vowel search
  std::vector<int> pointIdxVec;
  std::vector< std::vector<int> > points;

  if(octree.voxelSearch(curSearchPoint,pointIdxVec))			  
    {
      for(size_t i = 0; i < pointIdxVec.size(); i++)
	{
	  //assign the search point to the corresponding leaf voxel
	  cloud->points[pointIdxVec[i]].x;
	  cloud->points[pointIdxVec[i]].y;
	  cloud->points[pointIdxVec[i]].z;

	  //compute the centroid of that voxel and find the lowest centroid of all voxels
	  centroid = pcl::compute3DCentroid(cloud,pointIdxVec); 	  
	  centroids.push_back(centroid);
	  points.push_back(pointIdxVec); 
	  
	  int lowestCentroid = std::min_element(centroids.begin(),centroids.end()); 
	  int centIdx = std::lower_bound(centroids.begin(),centroids.end(),lowestCentroid); //index of lowest centroid
	  
	  //the point with the lowest centroid is the index that had the lowest centroid
	  closest = points[centIdx]; 
	}
	  	
    }	
  return closest;
}
	  




/* Function that gets what point that the octree needs to search through
   @param the search point
   @type pci::PointXYZ -- point cloud point
   @return the search point
   @type pci::PointXYZ -- point cloud point
   @author Eddie
*/
pcl::PointXYZRGBA KinectNode::getSearchPoint(pcl::PointXYZRGBA searchPoint)
{

  return searchPoint;

}
   
pcl::PointXYZRGBA KinectNode::centroids(pcl::PointCloud<pcl::PointXYZ cloud>)
{

  //create voxel grid and downsample the data to a left size of 1cm
  pcl::VoxelGrid<pcl::PointXYZ> vg;
  pcl::PointCloud<pcl::PointXYZRGB>::Ptr originalCloud = cloud;  
  pcl::PointCloud<pcl::PointXYZ>::Ptr cloud_filtered (new pcl::PointCloud<pcl::PointXYZ>);
  vg.setInputCloud(cloud);
  vg.setLeafSize(0.01f, 0.01f, 0.01f);
  vg.filter(*cloud_filtered);


  //create segmentation model
  
  pcl::SACSegmentation<pcl::PointXYZ> seg;
  pcl::PointIndices::Ptr inliers (new pcl::PointIndices);
  pcl::ModelCoefficients::Ptr coefficients (new pcl::ModelCoefficients);
  pcl::PointCloud<pcl::PointXYZ>::Ptr cloud_plane (new pcl::PointCloud<pcl::PointXYZ> ());
  seg.setOptimizeCoefficients (true);
  seg.setModelType (pcl::SACMODEL_PLANE);
  seg.setMethodType (pcl::SAC_RANSAC);
  seg.setMaxIterations (100);
  seg.setDistanceThreshold (0.02);

  int i=0, nr_points = (int) cloud_filtered->points.size ();
  while (cloud_filtered->points.size () > 0.3 * nr_points)
    {
      // Segment the largest planar component from the remaining cloud
      seg.setInputCloud (cloud_filtered);
      seg.segment (*inliers, *coefficients);
      if (inliers->indices.size () == 0)
	{
	  std::cout << "Could not estimate a planar model for the given dataset." << std::endl;
	  break;
	}

      // Extract the planar inliers from the input cloud
      pcl::ExtractIndices<pcl::PointXYZ> extract;
      extract.setInputCloud (cloud_filtered);
      extract.setIndices (inliers);
      extract.setNegative (false);

      // Write the planar inliers to disk
      extract.filter (*cloud_plane);
      std::cout << "PointCloud representing the planar component: " << cloud_plane->points.size () << " data points." << std::endl;

      // Remove the planar inliers, extract the rest
      extract.setNegative (true);
      extract.filter (*cloud_f);
      cloud_filtered = cloud_f;
    }
  // Creating the KdTree object for the search method of the extraction
  pcl::search::KdTree<pcl::PointXYZ>::Ptr tree (new pcl::search::KdTree<pcl::PointXYZ>);
  tree->setInputCloud (cloud_filtered);

  std::vector<pcl::PointIndices> cluster_indices;
  pcl::EuclideanClusterExtraction<pcl::PointXYZ> ec;
  ec.setClusterTolerance (0.02); // 2cm
  ec.setMinClusterSize (100);
  ec.setMaxClusterSize (25000);
  ec.setSearchMethod (tree);
  ec.setInputCloud (cloud_filtered);
  ec.extract (cluster_indices);

  std::vector<int> centroids;


  int j = 0;
  for (std::vector<pcl::PointIndices>::const_iterator it = cluster_indices.begin (); it != cluster_indices.end (); ++it)
    {
      pcl::PointCloud<pcl::PointXYZ>::Ptr cloud_cluster (new pcl::PointCloud<pcl::PointXYZ>);
      for (std::vector<int>::const_iterator pit = it->indices.begin (); pit != it->indices.end (); pit++)
	cloud_cluster->points.push_back (cloud_filtered->points[*pit]); //*
      cloud_cluster->width = cloud_cluster->points.size ();
      cloud_cluster->height = 1;
      cloud_cluster->is_dense = true;
      
      centroid = pcl::compute3DCentroid(cloud_cluster[it]);
      centroids.pushback(centorid);
					
      


      std::cout << "PointCloud representing the Cluster: " << cloud_cluster->points.size () << " data points." << std::endl;
      std::stringstream ss;
      ss << "cloud_cluster_" << j << ".pcd";
      writer.write<pcl::PointXYZ> (ss.str (), *cloud_cluster, false); //*
      
      j++;
    }
   return centroids[std::lower_bound(centroids.begin(), centroids.end())];
} 
    
  





 
  
    
  




/*
//find the centroid of each grid square and assign a value to the closest centroid based on the point cloud
//precondition: i = 0, centroid = 0
//invariant: i < the index of the point cloud
//postcondition: centroid = the closest centroid to the robot
for(int i = 0; i < cloud_filtered->width; i++ )
{
for(int j = 0; j < cloud_filtered->length; j++)
{
temp = centroid;

if(temp < centroid)
{
centroid = temp;
}
	  
if(temp == centroid)
{
centroid = centroid;
}
	  
if(temp > centroid)
{
centroid = centroid;
}
}
}
return centroid;
}
*/

 


   
   
 
//Return closest centroid
//Whats the xyz of the corners of the image -- resolution
//Function in bills code -- I found something interesting... 
//Take in a param, sizeOFGrid of how many gridSquares to have (pref)
//Divde the grid into squares
//Give me the pixels between (step sizes )
//upper - lower / step size
//is this centroid closer than the prev best
//if it is remeber it
//if Point is Null
//whats the XY compared to my robot
//if its closer than my prev best
//find out how to tell that no Orange is found









int main(int argc, char **argv)
{
  ros::init(argc, argv, "kinect_alpha");
  cv::namedWindow("view"); //these cv* calls are need if you want to use cv::imshow anywhere in your program
  cvStartWindowThread();
  KinectNode motion_tracker;
  ros::spin();
  cvDestroyWindow("view");
}
