#include <boost/python.hpp>
#include <XnOpenNI.h>

class Nui {
public:
  Nui() {
    
  }
};

BOOST_PYTHON_MODULE(pynui)
{
  using namespace boost::python;
  class_<Nui>("Nui")
  ;
}
