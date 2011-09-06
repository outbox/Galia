#include "openni.h"

int main(int argc, char* argv[]) {
  create_openni_thread(false, argc > 1 ? argv[1] : 0);
  nui_data data;
  while(1) {
    get_nui_data(&data);
    usleep(50*1000);
  }
}
