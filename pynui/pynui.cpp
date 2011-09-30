#include <boost/python.hpp>
#include "openni.h"
#include <string>

using namespace boost::python;

float lerp(float a, float b, float t) {
  return a * (1 - t) + b * t;
}

struct Joint {
  object position, orientation;
  bool valid;
  str repr() {
    std::string p = extract<std::string>(position.attr("__repr__")());
    std::string o = extract<std::string>(orientation.attr("__repr__")());
    return str(std::string("Joint(") + p + ", " + o + ")");
  }
};

struct SkeletonSide {
  Joint shoulder, elbow, hand, hip, knee, foot;
};

struct Skeleton {
  Joint head, neck, torso;
  SkeletonSide right, left;
};

struct Nui {
  nui_data data;
  object main, vec3, mat3;
  object users;
  
  float smooth_factor;
  XnSkeletonJointTransformation smooth_joints[max_users][joint_count];
  
  Nui() : smooth_factor(0.9) {
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
    
    for (int i=0; i<max_events; ++i) {
      nui_event& event = data.events[i];
      switch (event.event) {
        case nui_event::new_user:
          memcpy(smooth_joints[event.user], data.joints[event.user], sizeof(data.joints[event.user]));
          break;
        default: break;
      }
    }
    
    users = dict();
    for(int i=0;i<max_users;++i) {
      if(data.users[i]) {
        Skeleton skel;
        joint(skel.head, i, XN_SKEL_HEAD);
        joint(skel.neck, i, XN_SKEL_NECK);
        joint(skel.torso, i, XN_SKEL_TORSO);
        
        joint(skel.right.shoulder, i, XN_SKEL_RIGHT_SHOULDER);
        joint(skel.right.elbow, i, XN_SKEL_RIGHT_ELBOW);
        joint(skel.right.hand, i, XN_SKEL_RIGHT_HAND);
        joint(skel.right.hip, i, XN_SKEL_RIGHT_HIP);
        joint(skel.right.knee, i, XN_SKEL_RIGHT_KNEE);
        joint(skel.right.foot, i, XN_SKEL_RIGHT_FOOT);
        
        joint(skel.left.shoulder, i, XN_SKEL_LEFT_SHOULDER);
        joint(skel.left.elbow, i, XN_SKEL_LEFT_ELBOW);
        joint(skel.left.hand, i, XN_SKEL_LEFT_HAND);
        joint(skel.left.hip, i, XN_SKEL_LEFT_HIP);
        joint(skel.left.knee, i, XN_SKEL_LEFT_KNEE);
        joint(skel.left.foot, i, XN_SKEL_LEFT_FOOT);
        
        users[i] = skel;
      }
    }
  }
  
  void joint(Joint& transform, int user, int jointIndex) {
    const float scale = 1.f/1000;
    XnSkeletonJointTransformation& smooth_joint = smooth_joints[user][jointIndex];
    XnSkeletonJointTransformation& joint = data.joints[user][jointIndex];
    XnVector3D old_p = smooth_joint.position.position;
    XnVector3D p = joint.position.position;
    transform.valid = joint.position.fConfidence == 1;
    if (transform.valid) {
      if (smooth_joint.position.fConfidence == 1) {
        p.X = lerp(p.X, old_p.X, smooth_factor);
        p.Y = lerp(p.Y, old_p.Y, smooth_factor);
        p.Z = lerp(p.Z, old_p.Z, smooth_factor);
      }
      transform.position = vec3(p.X * scale, p.Y * scale, p.Z * scale);
            
      float* o = joint.orientation.orientation.elements;
      transform.orientation = mat3(o[0], o[1], o[2], o[3], o[4], o[5], o[6], o[7], o[8]);

      smooth_joint.position.position = p;
      smooth_joint.position.fConfidence = joint.position.fConfidence;
    }
  }
};

BOOST_PYTHON_MODULE(pynui)
{
  using namespace boost::python;
  
  class_<Nui>("Nui")
  .def("update", &Nui::update)
  .def_readwrite("smooth_factor", &Nui::smooth_factor)
  .def_readonly("users", &Nui::users)
  ;
  
  class_<Joint>("Joint")
  .def_readonly("position", &Joint::position)
  .def_readonly("orientation", &Joint::orientation)
  .def_readonly("valid", &Joint::valid)
  .def("__repr__", &Joint::repr)
  ;
  
  class_<Skeleton>("Skeleton")
  .def_readonly("head", &Skeleton::head)
  .def_readonly("neck", &Skeleton::neck)
  .def_readonly("torso", &Skeleton::torso)
  .def_readonly("right", &Skeleton::right)
  .def_readonly("left", &Skeleton::left)
  ;
  class_<SkeletonSide>("SkeletonSide")
  .def_readonly("shoulder", &SkeletonSide::shoulder)
  .def_readonly("elbow", &SkeletonSide::elbow)
  .def_readonly("hand", &SkeletonSide::hand)
  .def_readonly("hip", &SkeletonSide::hip)
  .def_readonly("knee", &SkeletonSide::knee)
  .def_readonly("foot", &SkeletonSide::foot)
  ;
}
