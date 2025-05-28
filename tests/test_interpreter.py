# Script to test the interpreter with various language features
from lexer import Lexer
from parser import Parser, ParseError
from interpreter import Interpreter

test_sources = [
    # Variable declaration and assignment
    "var x = 10; print(x);",
    # Assignment and arithmetic
    "var x = 0; print(x); x = x + 5; print(x);",
    # Block and scope
    "{ var y = 2; print(y); } print(x);",
    # If/else
    "var x = 11; if (x > 10) print(x); else print(0);",
    # While loop
    "var i = 0; while (i < 3) { print(i); i = i + 1; }",
    # Function declaration and call
    "fun add(a, b) { return a + b; } print(add(2, 3));",
    # Return statement in function
    "fun alwaysFive() { return 5; } print(alwaysFive());",
    # Nested function and recursion
    "fun fact(n) { if (n <= 1) return 1; return n * fact(n - 1); } print(fact(5));",
    # Error: undefined variable
    "print(z);",
    # Error: invalid assignment
    "(x + 1) = 2;",
]

for idx, source in enumerate(test_sources):
    print(f"\n--- Interpreter Test {idx+1} ---")
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    try:
        ast = parser.parse()
        interpreter = Interpreter()
        interpreter.interpret(ast)
    except ParseError as e:
        print(f"ParseError: {e}")
    except Exception as e:
        print(f"RuntimeError: {e}")
