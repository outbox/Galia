#include <boost/python.hpp>
#include "openni.h"
#include <string>

using namespace boost::python;

struct JointTransform {
  object position, orientation;
  str repr() {
    std::string p = extract<std::string>(position.attr("__repr__")());
    std::string o = extract<std::string>(orientation.attr("__repr__")());
    return str(std::string("Joint(") + p + ", " + o + ")");
  }
};

struct Nui {
  nui_data data;
  object main, vec3, mat3;
  object users;
  
  Nui() {
    main = import("__main__");
    object global(main.attr("__dict__"));
    exec("from panda3d.core import *", global, global);
    vec3 = global["Vec3"];
    mat3 = global["Mat3"];
    
    users = dict();
    
    create_openni_thread(false, 0);
  }
  
  void update() {
    get_nui_data(&data);
    users = dict();
    for(int i=0;i<max_users;++i) {
      if(data.users[i]) {
        dict joints;
        for(int j=0;j<joint_count;++j) {
          XnVector3D p = data.joints[i][j].position.position;
          float* o = data.joints[i][j].orientation.orientation.elements;
          JointTransform joint = { 
            vec3(p.X, p.Y, p.Z), 
            mat3(o[0], o[1], o[2], o[3], o[4], o[5], o[6], o[7], o[8])
          };
          joints[j] = joint;
        }
        users[i] = joints;
      }
    }
  }
};

BOOST_PYTHON_MODULE(pynui)
{
  using namespace boost::python;

  class_<Nui>("Nui")
    .def("update", &Nui::update)
    .def_readonly("users", &Nui::users)
  ;
  
  class_<JointTransform>("JointTransform")
    .def_readonly("position", &JointTransform::position)
    .def_readonly("orientation", &JointTransform::orientation)
    .def("__repr__", &JointTransform::repr)
  ;
  
  enum_<XnSkeletonJoint>("joint")
    .value("head", XN_SKEL_HEAD)
    .value("neck", XN_SKEL_NECK)
    .value("torso", XN_SKEL_TORSO)
    .value("waist", XN_SKEL_WAIST)

    .value("left_collar", XN_SKEL_LEFT_COLLAR)
    .value("left_shoulder", XN_SKEL_LEFT_SHOULDER)
    .value("left_elbow", XN_SKEL_LEFT_ELBOW)
    .value("left_wrist", XN_SKEL_LEFT_WRIST)
    .value("left_hand", XN_SKEL_LEFT_HAND)
    .value("left_fingertip", XN_SKEL_LEFT_FINGERTIP)

    .value("right_collar", XN_SKEL_RIGHT_COLLAR)
    .value("right_shoulder", XN_SKEL_RIGHT_SHOULDER)
    .value("right_elbow", XN_SKEL_RIGHT_ELBOW)
    .value("right_wrist", XN_SKEL_RIGHT_WRIST)
    .value("right_hand", XN_SKEL_RIGHT_HAND)
    .value("right_fingertip", XN_SKEL_RIGHT_FINGERTIP)

    .value("left_hip", XN_SKEL_LEFT_HIP)
    .value("left_knee", XN_SKEL_LEFT_KNEE)
    .value("left_ankle", XN_SKEL_LEFT_ANKLE)
    .value("left_foot", XN_SKEL_LEFT_FOOT)
    
    .value("right_hip", XN_SKEL_RIGHT_HIP)
    .value("right_knee", XN_SKEL_RIGHT_KNEE)
    .value("right_ankle", XN_SKEL_RIGHT_ANKLE)
    .value("right_foot", XN_SKEL_RIGHT_FOOT)
  ;
}
