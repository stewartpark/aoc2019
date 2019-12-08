#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "intcode_vm.h"

intcode_vm* intcode_vm_new(const char *source) {
  intcode_vm* vm = (intcode_vm *)malloc(sizeof(intcode_vm));
  unsigned int size = 1;

  // Calculate the size of memory needed.
  for(const char *src = source; *src != '\0'; src++) {
    if (*src == ',') size++;
  }

  vm->mem      = (intcode_int*)malloc(size * sizeof(intcode_int));
  vm->mem_size = size;
  vm->ip       = 0;

  // Fill out the allocated memory with the given source.
  intcode_int* mem = vm->mem;
  for(const char *src = source; *src != '\0'; src++) {
    if (*(src - 1) == ',' || src == source) {
      sscanf(src, "%lld", mem);
      mem = &mem[1];
    }
  }

  return vm;
}

void intcode_vm_destroy(intcode_vm** vm) {
  free((*vm)->mem);
  free((void *)*vm);
  *vm = (intcode_vm *)NULL;
}

const char *intcode_vm_get_opcode_str(intcode_int opcode) {
  switch(opcode) {
  case OP_ADD:
    return "ADD";
  case OP_MUL:
    return "MUL";
  case OP_IN:
    return "IN";
  case OP_OUT:
    return "OUT";
  case OP_HALT:
    return "HALT";
  default:
    return "INVALID";
  }
}

unsigned int intcode_vm_get_opcode_n_operands(intcode_int opcode) {
  switch (opcode) {
  case OP_ADD:
    return 3;
  case OP_MUL:
    return 3;
  case OP_IN:
    return 1;
  case OP_OUT:
    return 1;
  case OP_HALT:
    return 0;
  default:
    return 0;
  }
}

unsigned int intcode_vm_decode_and_print(intcode_vm* vm, intcode_int addr) {
  intcode_int opcode = vm->mem[addr] % 100;
  printf("%5lld: %5s(%5lld) ", addr, intcode_vm_get_opcode_str(opcode), vm->mem[addr]);
  for (unsigned int i = 0; i < intcode_vm_get_opcode_n_operands(opcode); i++) {
    printf("%5lld ", vm->mem[addr + 1 + i]);
  }
  printf("\n");
  return 1 + intcode_vm_get_opcode_n_operands(opcode);
}

intcode_int intcode_vm_panic(intcode_vm* vm, const char* reason) {
  intcode_vm_decode_and_print(vm, vm->ip);
  printf("Panic: %s\n", reason);
  exit(1);
}

intcode_int intcode_vm_run(intcode_vm* vm) {
#define FETCH_OPCODE() (vm->mem[vm->ip] % 100)
#define FETCH_MODE() (vm->mem[vm->ip] / 100)
#define FETCH_OPERAND_UNSAFE(offset) (vm->mem[vm->ip + offset])
#define FETCH_OPERAND(offset) (vm->mem_size <= (unsigned int)vm->mem[vm->ip + offset] ? intcode_vm_panic(vm, "bad position") : vm->mem[vm->ip + offset])
#define OPERAND_REF(offset) (vm->mem[FETCH_OPERAND(offset)])
#define OPERAND_VALUE(offset) ((mode & (1 << (offset - 1))) == 0 ? vm->mem[FETCH_OPERAND(offset)] : FETCH_OPERAND_UNSAFE(offset))

  unsigned char running = 1;

  // Fetch-decode-execute loop
  while(running && vm->ip < vm->mem_size) {
    unsigned char mode = \
      ((FETCH_MODE() / 100) << 2) + \
      ((FETCH_MODE() % 100 / 10) << 1) + \
      (FETCH_MODE() % 10);

    #ifdef DEBUG
    intcode_vm_decode_and_print(vm, vm->ip);
    #endif

    switch(FETCH_OPCODE()) {
    case OP_ADD:
      OPERAND_REF(3) = OPERAND_VALUE(1) + OPERAND_VALUE(2);
      #ifdef DEBUG
      printf("= %lld\n", OPERAND_VALUE(1) + OPERAND_VALUE(2));
      #endif
      break;
    case OP_MUL:
      OPERAND_REF(3) = OPERAND_VALUE(1) * OPERAND_VALUE(2);
      #ifdef DEBUG
      printf("= %lld\n", OPERAND_VALUE(1) * OPERAND_VALUE(2));
      #endif
      break;
    case OP_IN:
      scanf("%lld", &OPERAND_REF(1));
      break;
    case OP_OUT:
      printf("%lld\n", OPERAND_VALUE(1));
      break;
    case OP_HALT:
      running = 0;
      return vm->mem[0]; // Return the first value of the memory when halting.
    default:
      running = 0;
      intcode_vm_panic(vm, "wrong opcode");
      break;
    }

    // Advance by opcode size + # of operands
    vm->ip += 1 + intcode_vm_get_opcode_n_operands(FETCH_OPCODE());
  }

  return vm->mem[0];
}
