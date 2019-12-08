CC=gcc
CFLAGS=$(shell echo $$CFLAGS)

all: test_vm compile_vm

test: test_vm

test_vm:
	@$(CC) vm/intcode_vm.c vm/narwhal.c vm/test.c -o test_intcode $(CFLAGS)
	@./test_intcode; rm -f ./test_intcode

compile_vm:
	@$(CC) vm/intcode_vm.c vm/main.c -o run_intcode $(CFLAGS)

day1: compile_vm
	@cat in/1.txt | ./run_intcode day1.ic

day2_p1: compile_vm
	@./run_intcode day2_p1.ic

day2_p2: compile_vm
	@./run_intcode day2_p2.ic
