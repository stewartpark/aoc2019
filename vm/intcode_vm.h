#ifndef __INTCODE_VM
#define __INTCODE_VM

typedef signed long long   intcode_int;

typedef struct {
  unsigned int ip;
  unsigned int mem_size;
  intcode_int* mem;
} intcode_vm;

intcode_vm* intcode_vm_new(const char*);
void        intcode_vm_destroy(intcode_vm**);

intcode_int intcode_vm_run(intcode_vm*);

const char *intcode_vm_get_opcode_str(intcode_int);
unsigned int intcode_vm_get_opcode_n_operands(intcode_int);
unsigned int intcode_vm_decode_and_print(intcode_vm*, intcode_int);
intcode_int intcode_vm_panic(intcode_vm*, const char*);

// Opcodes
#define OP_ADD  1
#define OP_MUL  2
#define OP_IN   3
#define OP_OUT  4
#define OP_HALT 99

// Opcodes (added)
#define OP_DIV  50
#define OP_JGE  60

#endif
