from intlang.parser import Parser
from intlang.compiler import Compiler
import sys
import os


with open(sys.argv[1]) as f_in, open(sys.argv[2], 'w') as f_out:
    parser = Parser()
    ast = parser.parse(f_in.read())
    compiler = Compiler(
        stack_size=int(os.getenv('STACK_SIZE', 2 * 1024)),
        heap_size=int(os.getenv('HEAP_SIZE', 4 * 1024))
    )
    code = compiler.compile(ast)
    f_out.write(code)
    if os.getenv('DEBUG'):
        cg = compiler.code_generator
        print(f'stack: {cg.stack.start} - {cg.stack.end}')
        print(f' text: {cg.text.start} - {cg.text.end}')
        print(f' data: {cg.data.start} - {cg.data.end}')
        print(f' heap: {cg.heap.start} - {cg.heap.end}')
        print(f'total: {len(code)} bytes, {cg.heap.end} intcodes.')
