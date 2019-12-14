CC=gcc
CFLAGS=$(shell echo $$CFLAGS)

all: test

test: test_vm test_compiler

test_vm:
	@$(CC) vm/intcode_vm.c vm/narwhal.c vm/test.c -o test_intcode $(CFLAGS)
	@./test_intcode; rm -f ./test_intcode

compile_vm:
	@$(CC) vm/intcode_vm.c vm/main.c -o run_intcode $(CFLAGS)

test_compiler: compile_vm
	@python -m intlang intlang/tests/1.il /dev/stdout | ./run_intcode /dev/stdin | diff - intlang/tests/1.out
	@python -m intlang intlang/tests/2.il /dev/stdout | ./run_intcode /dev/stdin | diff - intlang/tests/2.out

day1: compile_vm
	@cat in/1.txt | ./run_intcode day1.ic

day2_p1: compile_vm
	@./run_intcode day2_p1.ic

day2_p2: compile_vm
	@./run_intcode day2_p2.ic

day3: compile_vm
	@python -m intlang day3.il /dev/stdout | ./run_intcode /dev/stdin
