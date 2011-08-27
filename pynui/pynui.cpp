#include <boost/python.hpp>
#include <string>

class Nui {
  std::string str;

public:
  Nui() {
    str = "asd";
  }

  std::string greet() {
    return str;
  }
};

BOOST_PYTHON_MODULE(pynui)
{
  using namespace boost::python;
  class_<Nui>("Nui")
    .def("greet", &Nui::greet)
  ;
}
