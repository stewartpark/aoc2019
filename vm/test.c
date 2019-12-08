#include "narwhal.h"
#include "intcode_vm.h"

TEST(new_and_destroy) {
  intcode_vm* vm = intcode_vm_new("0,2,100");
  ASSERT_EQ(vm->mem_size, 3);

  ASSERT_EQ(vm->mem[0], 0);
  ASSERT_EQ(vm->mem[1], 2);
  ASSERT_EQ(vm->mem[2], 100);

  intcode_vm_destroy(&vm);
  ASSERT_EQ(vm, NULL);
}

TEST(program_with_no_halt) {
  intcode_vm* vm = intcode_vm_new("1,0,1,0");
  ASSERT_EQ(intcode_vm_run(vm), 1);
  intcode_vm_destroy(&vm);
}

TEST(immediate_mode) {
  intcode_vm* vm = intcode_vm_new("1101,30,40,3,1002,3,50,0,99");
  ASSERT_EQ(intcode_vm_run(vm), 3500);
  intcode_vm_destroy(&vm);
}

TEST(aoc_day2_example) {
  intcode_vm* vm;

  vm = intcode_vm_new("1,9,10,3,2,3,11,0,99,30,40,50");
  ASSERT_EQ(intcode_vm_run(vm), 3500);
  intcode_vm_destroy(&vm);

  vm = intcode_vm_new("1,0,0,0,99");
  ASSERT_EQ(intcode_vm_run(vm), 2);
  intcode_vm_destroy(&vm);

  vm = intcode_vm_new("2,3,0,3,99");
  intcode_vm_run(vm);
  ASSERT_EQ(vm->mem[3], 6);
  intcode_vm_destroy(&vm);

  vm = intcode_vm_new("2,4,4,5,99,0");
  intcode_vm_run(vm);
  ASSERT_EQ(vm->mem[5], 9801);
  intcode_vm_destroy(&vm);

  vm = intcode_vm_new("1,1,1,4,99,5,6,0,99");
  ASSERT_EQ(intcode_vm_run(vm), 30);
  ASSERT_EQ(vm->mem[4], 2);
  intcode_vm_destroy(&vm);
}
