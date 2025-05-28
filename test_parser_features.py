# Comprehensive test for the parser's AST nodes and error handling
from lexer import Lexer
from parser import Parser, ParseError

test_sources = [
    # Variable Declaration
    ("var x = 10;", "VarDecl"),
    # Assignment
    ("x = x + 1;", "Assignment"),
    # Print Statement
    ("print x;", "PrintStmt"),
    # Block
    ("{ var y = 2; print y; }", "Block"),
    # If/Else Statement
    ("if (x > 0) print x; else print -x;", "IfStmt"),
    # While Loop
    ("while (x < 5) x = x + 1;", "WhileStmt"),
    # Function Declaration
    ("fun add(a, b) { return a + b; }", "FunctionDecl"),
    # Function Call
    ("add(1, 2);", "Call"),
    # Return Statement (standalone)
    ("fun foo() { return; }", "ReturnStmt"),
    # Nested Statements
    ("fun fact(n) { if (n <= 1) return 1; return n * fact(n - 1); }", "Nested Function/If/Return/Call"),
    # Error: Missing semicolon
    ("var z = 5", "Error: Missing semicolon"),
    # Error: Invalid assignment target
    ("(x + 1) = 2;", "Error: Invalid assignment target"),
    # Error: Unterminated block
    ("{ print 1; ", "Error: Unterminated block"),
]

def print_ast(node, indent=0):
    prefix = '  ' * indent
    if node is None:
        print(f"{prefix}None")
    elif type(node).__name__ == "Variable":
        print(f"{prefix}Variable({node.name.lexeme})")
    elif hasattr(node, 'statements'):
        if hasattr(node, 'body') and isinstance(node.body, list):
            print(f"{prefix}{type(node).__name__}")
            for stmt in node.body:
                print_ast(stmt, indent + 1)
        else:
            print(f"{prefix}{type(node).__name__}")
            for stmt in node.statements:
                print_ast(stmt, indent + 1)
    elif hasattr(node, 'expression'):
        print(f"{prefix}{type(node).__name__}")
        print_ast(node.expression, indent + 1)
    elif hasattr(node, 'initializer'):
        print(f"{prefix}VarDecl: {node.name.lexeme}")
        print_ast(node.initializer, indent + 1)
    elif hasattr(node, 'name') and hasattr(node, 'params') and hasattr(node, 'body'):
        params = ', '.join([p.lexeme for p in node.params])
        print(f"{prefix}FunctionDecl: {node.name.lexeme}({params})")
        print_ast(node.body, indent + 1)
    elif hasattr(node, 'name') and hasattr(node, 'value'):
        print(f"{prefix}Assignment: {node.name.lexeme}")
        print_ast(node.value, indent + 1)
    elif hasattr(node, 'operator') and hasattr(node, 'left') and hasattr(node, 'right'):
        print(f"{prefix}Binary({node.operator.lexeme})")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)
    elif hasattr(node, 'operator') and hasattr(node, 'right'):
        print(f"{prefix}Unary({node.operator.lexeme})")
        print_ast(node.right, indent + 1)
    elif hasattr(node, 'condition') and hasattr(node, 'then_branch'):
        print(f"{prefix}IfStmt")
        print(f"{prefix}  Condition:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  Then:")
        print_ast(node.then_branch, indent + 2)
        if hasattr(node, 'else_branch') and node.else_branch:
            print(f"{prefix}  Else:")
            print_ast(node.else_branch, indent + 2)
    elif hasattr(node, 'condition') and hasattr(node, 'body'):
        print(f"{prefix}WhileStmt")
        print(f"{prefix}  Condition:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)
    elif hasattr(node, 'callee') and hasattr(node, 'arguments'):
        print(f"{prefix}Call")
        print(f"{prefix}  Callee:")
        print_ast(node.callee, indent + 2)
        print(f"{prefix}  Arguments:")
        for arg in node.arguments:
            print_ast(arg, indent + 2)
    elif hasattr(node, 'value') and hasattr(node, 'keyword'):
        print(f"{prefix}ReturnStmt")
        if node.value:
            print_ast(node.value, indent + 1)
    elif hasattr(node, 'value'):
        print(f"{prefix}Literal({node.value})")
    elif hasattr(node, 'lexeme'):
        print(f"{prefix}Identifier({node.lexeme})")
    else:
        print(f"{prefix}{type(node).__name__}")

for source, label in test_sources:
    print(f"\n--- Test: {label} ---")
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    try:
        ast = parser.parse()
        print_ast(ast)
    except ParseError as e:
        print(f"ParseError: {e}")
