#include <boost/python.hpp>
#include "openni.h"
#include <string>
#include <vector>
#include <Python.h>
#include <cmath>
#include "pymath.h"

using namespace boost::python;
using namespace std;

float lerp(float a, float b, float t) {
  return a * (1 - t) + b * t;
}

XnPoint3D lerp(XnPoint3D a, XnPoint3D b, float t) {
  XnPoint3D ret;
  ret.X = lerp(a.X, b.X, t);
  ret.Y = lerp(a.Y, b.Y, t);
  ret.Z = lerp(a.Z, b.Z, t);
  return ret;
}

struct Joint {
  object position, orientation, projection;
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
  object main, vec3, vec2, mat3;
  object users;
  std::vector<char> _label_map;
  
  float smooth_factor;
  XnSkeletonJointTransformation smooth_joints[max_users][joint_count];
  XnPoint3D smooth_projected_joints[max_users][joint_count];
  
  Nui() : smooth_factor(0.9) {
    main = import("__main__");
    object global(main.attr("__dict__"));
    exec("from panda3d.core import *", global, global);
    vec3 = global["Vec3"];
    vec2 = global["Vec2"];
    mat3 = global["Mat3"];
    
    users = dict();
    
    create_openni_thread(false, 0);
  }
  
  void update() {
    boost::lock_guard<boost::mutex> lock(get_nui_mutex());
    nui_data& data = get_nui_data();
    
    for (int i=0; i<max_events; ++i) {
      nui_event& event = data.events[i];
      switch (event.event) {
        case nui_event::new_user:
          memcpy(smooth_joints[event.user], data.joints[event.user], sizeof(data.joints[event.user]));
          memcpy(smooth_projected_joints[event.user], data.projected_joints[event.user], sizeof(data.projected_joints[event.user]));
          break;
        default: break;
      }
    }
    
    users = dict();
    for(int i=0;i<max_users;++i) {
      if(data.users[i]) {
        Skeleton skel;
        joint(data, skel.head, i, XN_SKEL_HEAD);
        joint(data, skel.neck, i, XN_SKEL_NECK);
        joint(data, skel.torso, i, XN_SKEL_TORSO);

        joint(data, skel.right.shoulder, i, XN_SKEL_RIGHT_SHOULDER);
        joint(data, skel.right.elbow, i, XN_SKEL_RIGHT_ELBOW);
        joint(data, skel.right.hand, i, XN_SKEL_RIGHT_HAND);
        joint(data, skel.right.hip, i, XN_SKEL_RIGHT_HIP);
        joint(data, skel.right.knee, i, XN_SKEL_RIGHT_KNEE);
        joint(data, skel.right.foot, i, XN_SKEL_RIGHT_FOOT);

        joint(data, skel.left.shoulder, i, XN_SKEL_LEFT_SHOULDER);
        joint(data, skel.left.elbow, i, XN_SKEL_LEFT_ELBOW);
        joint(data, skel.left.hand, i, XN_SKEL_LEFT_HAND);
        joint(data, skel.left.hip, i, XN_SKEL_LEFT_HIP);
        joint(data, skel.left.knee, i, XN_SKEL_LEFT_KNEE);
        joint(data, skel.left.foot, i, XN_SKEL_LEFT_FOOT);
        
        users[i] = skel;
      }
    }
    
    _label_map.resize(data.width * data.height * 4);
    for (size_t i = 0; i < _label_map.size(); i+=4) {
      XnLabel label = data.label_map[i/4];
      if (label) {
        _label_map[i] = 0xff;
        _label_map[i+1] = 0xff;
        _label_map[i+2] = 0xff;
        _label_map[i+3] = 0xff;
      } else {
        _label_map[i] = 0;
        _label_map[i+1] = 0;
        _label_map[i+2] = 0;
        _label_map[i+3] = 0;
      }
    }

    data.clear_events();
  }
  
  void joint(nui_data& data, Joint& transform, int user, int jointIndex) {
    const float scale = 1.f/1000;
    XnSkeletonJointTransformation& joint = data.joints[user][jointIndex];
    transform.valid = joint.position.fConfidence == 1;
    if (transform.valid) {
      XnVector3D p = joint.position.position;
      XnSkeletonJointTransformation& smooth_joint = smooth_joints[user][jointIndex];
      if (smooth_joint.position.fConfidence == 1) {
        p = lerp(p, smooth_joint.position.position, smooth_factor);
      }
      transform.position = vec3(p.X * scale, p.Y * scale, p.Z * scale);
      smooth_joint.position.position = p;
      smooth_joint.position.fConfidence = joint.position.fConfidence;
      
      p = data.projected_joints[user][jointIndex];
      XnPoint3D smooth_p = smooth_projected_joints[user][jointIndex];
      if (smooth_joint.position.fConfidence == 1 && !Py_IS_NAN(smooth_p.X) && !Py_IS_NAN(smooth_p.Y) && !Py_IS_NAN(smooth_p.Z)) {
        p = lerp(p, smooth_p, smooth_factor);
      }
      transform.projection = vec2(p.X / data.width, p.Y / data.height);
      smooth_projected_joints[user][jointIndex] = p;
            
      float* o = joint.orientation.orientation.elements;
      transform.orientation = mat3(o[0], o[1], o[2], o[3], o[4], o[5], o[6], o[7], o[8]);
    }
  }
  
  unsigned long label_map() {
    return (unsigned long)&_label_map[0];
  }
};

BOOST_PYTHON_MODULE(pynui)
{
  using namespace boost::python;
  PyEval_InitThreads();
  class_<Nui>("Nui")
  .def("update", &Nui::update)
  .def_readwrite("smooth_factor", &Nui::smooth_factor)
  .def_readonly("users", &Nui::users)
  .add_property("label_map", &Nui::label_map)
  ;
  
  class_<Joint>("Joint")
  .def_readonly("position", &Joint::position)
  .def_readonly("projection", &Joint::projection)
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
