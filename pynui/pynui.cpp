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
          Joint joint = { 
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
  
  class_<Joint>("Joint")
    .def_readonly("position", &Joint::position)
    .def_readonly("orientation", &Joint::orientation)
    .def("__repr__", &Joint::repr)
  ;
}
