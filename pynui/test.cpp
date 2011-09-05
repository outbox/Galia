#include "openni.h"

int main(int argc, char* argv[]) {
  create_openni_thread(false, argc > 1 ? argv[1] : 0);
  while(1);
}
