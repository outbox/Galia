#include "openni.h"

int main(int argc, char* argv[]) {
  create_openni_thread(false, argc > 1 ? argv[1] : 0);
  nui_data data;
  while(1) {
    clock_t before = clock();
    get_nui_data();
    printf("%fms\n", (clock()-before)*1000.f/CLOCKS_PER_SEC);
    usleep(50*1000);
  }
}
