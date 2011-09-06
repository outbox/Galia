#ifndef OPENNI_PROCESS
#define OPENNI_PROCESS

#include "nui_data.h"

void create_openni_thread(bool record, const char* replay);
void get_nui_data(nui_data* data);

#endif
