CC=gcc
CFLAGS=$(shell echo $$CFLAGS)

all: test_vm compile_vm

test: test_vm

test_vm:
	$(CC) vm/intcode_vm.c vm/narwhal.c vm/test.c -o test_intcode $(CFLAGS)
	./test_intcode; rm -f ./test_intcode

compile_vm:
	$(CC) vm/intcode_vm.c vm/main.c -o run_intcode $(CFLAGS)
