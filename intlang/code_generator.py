from itertools import chain
import os


class Address:
    def __init__(self, size):
        self.address = None
        self.size = 0
        self.content = []
        self.resize(size)

    def resize(self, size):
        if self.address is not None:
            raise Exception(
                "This address cannot be resized since it is already assigned.")
        if size > self.size:
            self.content = self.content + \
                list(0 for _ in range(size - self.size))
        else:
            self.content = self.content[:-(self.size - size + 1)]
        self.size = size

    def grow(self, incr):
        self.resize(self.size + incr)

    def shrink(self, decr):
        self.resize(self.size - decr)

    def append(self, content):
        if os.getenv('DEBUG'):
            print(content)
        self.grow(len(content))
        self.content[-len(content):] = content


class Immediate:
    def __init__(self, intcode):
        self.intcode = intcode

    def __repr__(self):
        return f'Immediate({self.intcode})'


class Position:
    def __init__(self, intcode):
        self.intcode = intcode

    def __repr__(self):
        return f'Position({self.intcode})'


class MemorySection:
    def __init__(self):
        self.addresses = []
        self.finalized = False
        self.start = None
        self.end = None

    def obtain(self, size):
        if self.finalized:
            raise Exception(
                "Cannot obtain a new address from this memory section: already finalized.")
        addr = Address(size)
        self.addresses.append(addr)
        return addr

    def finalize(self, base):
        self.start = base
        for addr in self.addresses:
            addr.address = base
            base += addr.size
        self.end = base
        self.finalized = True


class FunctionBuilder:
    def __init__(self, code_generator):
        self.code_generator = code_generator
        self.address = code_generator.text.obtain(0)

    def add(self, *args):
        self.opcode_with_3_operands(1, *args)

    def mul(self, *args):
        self.opcode_with_3_operands(2, *args)

    def in_(self, arg0):
        self.address.append([self.calculate_mode(arg0, None, None) + 3, arg0])

    def out(self, arg0):
        self.address.append([self.calculate_mode(arg0, None, None) + 4, arg0])

    def halt(self):
        self.address.append([99])

    # Added, not in the original spec

    def div(self, *args):
        self.opcode_with_3_operands(50, *args)

    def jge(self, *args):
        self.opcode_with_3_operands(60, *args)

    # Macro

    def push(self, arg0):
        self.add(Immediate(0), 'sp', '$+4')
        self.add(Immediate(0), arg0, 0)
        self.add('sp', Immediate(-1), 'sp')

    def pop(self, arg0=None):
        if arg0 is not None:
            self.read_stack(0, arg0)
        self.add('sp', Immediate(1), 'sp')

    def read_stack(self, arg_no, arg0, from_='sp'):
        if type(arg_no) != int:
            raise Exception("read_stack <arg number> <arg0>")
        self.add(from_, Immediate(arg_no + 1), '$+3')
        self.add(Immediate(0), 0, arg0)

    def write_stack(self, arg_no, arg0, from_='sp'):
        if type(arg_no) != int:
            raise Exception("write_stack <arg number> <arg0>")
        self.add(from_, Immediate(arg_no + 1), '$+4')
        self.add(Immediate(0), arg0, 0)

    def read_arg(self, arg_no, arg0):
        self.read_stack(arg_no, arg0, from_='bp')

    def read_local(self, local_no, arg0):
        self.read_stack(-(local_no + 2), arg0, from_='bp')

    def write_local(self, local_no, arg0):
        self.write_stack(-(local_no + 2), arg0, from_='bp')

    def call(self, arg0):
        self.push(Immediate('$+10'))
        self.jge(Immediate(0), Immediate(0), arg0)
        self.pop()

    def ret(self, arg0):
        if arg0 != 'r0':  # skip ths if the target is r0
            self.add(Immediate(0), arg0, 'r0')
        self.read_stack(0, '$+4')
        self.jge(Immediate(0), Immediate(0), Immediate(0))

    # Utils

    def calculate_mode(self, arg0, arg1, arg2):
        mode = 0
        if type(arg0) == Immediate:
            mode += 100
        if type(arg1) == Immediate:
            mode += 1000
        if type(arg2) == Immediate:
            mode += 10000
        return mode

    def opcode_with_3_operands(self, opcode, arg0, arg1, arg2):
        mode = self.calculate_mode(arg0, arg1, arg2)
        self.address.append([mode + opcode, arg0, arg1, arg2])


class CodeGenerator:
    def __init__(self, heap_size, stack_size, register_size=6):
        self.text = MemorySection()

        # Initialize stack
        self.stack = MemorySection()
        self.jmp_code = self.stack.obtain(4)
        self.stack_start = self.stack.obtain(
            stack_size - register_size - self.jmp_code.size)
        self.registers = list(
            self.stack.obtain(1) for _ in range(register_size)
        )
        self.stack.finalize(base=0)
        # Initialize the stack pointer and base pointer
        self.registers[-1].content = [stack_size - register_size - 1]
        self.registers[-2].content = [stack_size - register_size - 1]

        # Initialize data
        self.data = MemorySection()
        self.section_info = self.data.obtain(4)

        # Initialize heap
        self.heap = MemorySection()
        self.heap.obtain(heap_size)

    def new_function(self):
        return FunctionBuilder(self)

    def set_entrypoint(self, entrypoint):
        self.jmp_code.content = [11160, 0, 0, entrypoint]

    def generate(self):
        # text starts where stack ends
        self.text.finalize(base=self.stack.end)
        # data starts where text ends
        self.data.finalize(base=self.text.end)
        # heap starts where data ends
        self.heap.finalize(base=self.data.end)

        # Fill out the section data
        self.section_info.content = [
            self.stack.start, self.text.start, self.data.start, self.heap.start]

        # Build the memory in a 1d array
        memory = list(chain(*[
            *[addr.content for addr in self.stack.addresses],
            *[addr.content for addr in self.text.addresses],
            *[addr.content for addr in self.data.addresses],
            *[addr.content for addr in self.heap.addresses]
        ]))

        # Finalize all the pointers and registers to an int value
        def translate(loc, value):
            # Unbox lazy values
            # This tags the value for the ops mode, but not needed when compiled.
            if hasattr(value, 'intcode'):
                value = value.intcode

            if type(value) == Address:  # Pointer
                return value.address
            elif type(value) == str and len(value) == 2:  # Registers
                if value[0] == 'r':
                    return self.registers[int(value[1])].address
                elif value == 'sp':
                    return self.registers[-1].address
                elif value == 'bp':
                    return self.registers[-2].address
                else:
                    raise Exception(f"Invalid register {value}")
            elif type(value) == str:  # Offset from the current address
                if value[0:2] == '$+':
                    return loc + int(value[2:])
                else:
                    raise Exception(f"String not allowed {value}")
            else:
                return value
        memory = list(translate(loc, value)
                      for loc, value in enumerate(memory))

        # Stringify all elements
        memory = list(str(x) for x in memory)

        # Return a string of a Intcode-compiled program.
        return ','.join(memory)
