# Test script for the toy language lexer and parser
from lexer import Lexer
from parser import Parser

# Example input string
source = '1 + 2 * (3 - 4) == 5 != 6'

# Lexing
lexer = Lexer(source)
tokens = lexer.scan_tokens()
print('Tokens:')
for token in tokens:
    print(token.__repr__(verbose=True))

# Parsing
parser = Parser(tokens)
ast = parser.parse()

def print_ast(node, indent=0):
    prefix = '  ' * indent
    if node is None:
        print(f"{prefix}None")
    elif hasattr(node, 'operator') and hasattr(node, 'left') and hasattr(node, 'right'):
        print(f"{prefix}Binary({node.operator.lexeme})")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)
    elif hasattr(node, 'operator') and hasattr(node, 'right'):
        print(f"{prefix}Unary({node.operator.lexeme})")
        print_ast(node.right, indent + 1)
    elif hasattr(node, 'value'):
        print(f"{prefix}Literal({node.value})")
    elif hasattr(node, 'expression'):
        print(f"{prefix}Grouping")
        print_ast(node.expression, indent + 1)
    else:
        print(f"{prefix}{type(node).__name__}")

print('\nAST:')
print_ast(ast)
