from lexer import Lexer
from parser import Parser
from codegen import CodeGenerator

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python main.py <source-file>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        source = f.read()
    tokens = Lexer(source).scan_tokens()
    ast = Parser(tokens).parse()
    codegen = CodeGenerator()
    llvm_module = codegen.generate(ast)
    print(str(llvm_module))
