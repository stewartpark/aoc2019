#include <stdio.h>
#include <stdlib.h>
#include "intcode_vm.h"

#define MAX_FILE_SIZE 10240


void print_usage(char *argv0) {
  printf("[+] Intcode VM (Advent of Code 2019)\n");
  printf("Usage: %s [file]\n", argv0);
}

int main(int argc, char **argv) {

  if (argc <= 1) {
    print_usage(argv[0]);
    return 1;
  }

  FILE* fp = fopen(argv[1], "r");
  char *buf = (char *)malloc(MAX_FILE_SIZE);
  fgets(buf, MAX_FILE_SIZE, fp);
  fclose(fp);

  intcode_vm* vm = intcode_vm_new(buf);
  printf("%d\n", intcode_vm_run(vm));
  intcode_vm_destroy(&vm);
  free(buf);

  return 0;
}
