#ifndef OPENNI_PROCESS
#define OPENNI_PROCESS

#include "nui_data.h"
#include <boost/thread.hpp>

void create_openni_thread(bool record, const char* replay);
boost::mutex& get_nui_mutex();
nui_data& get_nui_data();

#endif
