#include <boost/python.hpp>
#include "openni.h"
#include <string>

using namespace boost::python;

struct Joint {
  object position, orientation;
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
        Skeleton skel;
	skel.head = joint(data, i, XN_SKEL_HEAD);
	skel.neck = joint(data, i, XN_SKEL_NECK);
	skel.torso = joint(data, i, XN_SKEL_TORSO);

	skel.right.shoulder = joint(data, i, XN_SKEL_RIGHT_SHOULDER);
	skel.right.elbow = joint(data, i, XN_SKEL_RIGHT_ELBOW);
	skel.right.hand = joint(data, i, XN_SKEL_RIGHT_HAND);
	skel.right.hip = joint(data, i, XN_SKEL_RIGHT_HIP);
	skel.right.knee = joint(data, i, XN_SKEL_RIGHT_KNEE);
	skel.right.foot = joint(data, i, XN_SKEL_RIGHT_FOOT);

	skel.left.shoulder = joint(data, i, XN_SKEL_LEFT_SHOULDER);
	skel.left.elbow = joint(data, i, XN_SKEL_LEFT_ELBOW);
	skel.left.hand = joint(data, i, XN_SKEL_LEFT_HAND);
	skel.left.hip = joint(data, i, XN_SKEL_LEFT_HIP);
	skel.left.knee = joint(data, i, XN_SKEL_LEFT_KNEE);
	skel.left.foot = joint(data, i, XN_SKEL_LEFT_FOOT);

        users[i] = skel;
      }
    }
  }

  Joint joint(nui_data data, int user, int joint) {
    XnVector3D p = data.joints[user][joint].position.position;
    float* o = data.joints[user][joint].orientation.orientation.elements;
    Joint transform = { 
      vec3(p.X, p.Y, p.Z), 
      mat3(o[0], o[1], o[2], o[3], o[4], o[5], o[6], o[7], o[8])
    };
    return transform;
  }
};

BOOST_PYTHON_MODULE(pynui)
{
  using namespace boost::python;

  class_<Nui>("Nui")
    .def("update", &Nui::update)
    .def_readonly("users", &Nui::users)
    ;
  
  class_<Joint>("Joint")
    .def_readonly("position", &Joint::position)
    .def_readonly("orientation", &Joint::orientation)
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
