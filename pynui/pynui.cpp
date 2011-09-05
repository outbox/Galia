#include <boost/python.hpp>
#include "openni.h"

class Nui {
public:
  Nui() {
    create_openni_thread(false, 0);
  }
};

BOOST_PYTHON_MODULE(pynui)
{
  using namespace boost::python;
  class_<Nui>("Nui")
  ;
}
