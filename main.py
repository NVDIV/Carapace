import argparse
import sys
from pathlib import Path

from src.lexer import Lexer
from src.parser import Parser
from src.interpreter import Interpreter
from src.errors import CarapaceError

def parse_arguments():
    """Handles Command Line Interface arguments."""
    parser = argparse.ArgumentParser(
        prog='carapace',
        description='Carapace Language Interpreter - A turtle graphics DSL.',
        epilog='Example: python main.py examples/square.cara --tokens'
    )

    parser.add_argument(
        'source', 
        type=Path, 
        help='The .cara source file to execute'
    )

    parser.add_argument(
        '-t', '--tokens', 
        action='store_true', 
        help='Perform lexical analysis and print token stream'
    )

    parser.add_argument(
        '-a', '--ast', 
        action='store_true', 
        help='Parse code and display the Abstract Syntax Tree'
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version='Carapace DSL 1.0.0'
    )

    return parser.parse_args()

def dump_tokens(tokens):
    """Prints the list of tokens in a formatted table."""
    print(f"{'TOKEN TYPE':<15} | {'VALUE':<15} | {'LINE':<5}")
    print("-" * 45)
    for token in tokens:
        # Using :<N to ensure columns stay aligned
        print(f"{token.type.name:<15} | {str(token.value):<15} | {token.line:<5}")

def dump_ast(nodes, level=0):
    """Recursively prints the AST with visual indentation."""
    for node in nodes:
        indent = "  " * level
        node_name = type(node).__name__
        
        # We extract attributes while excluding 'body' to keep the print clean
        attributes = {k: v for k, v in vars(node).items() if k != 'body'}
        attr_str = f"({attributes})" if attributes else ""
        
        print(f"{indent}└── {node_name} {attr_str}")
        
        # Recursive call for nested blocks (like REPEAT)
        if hasattr(node, 'body'):
            dump_ast(node.body, level + 1)

def main():
    """Main entry point for the Carapace Interpreter."""
    args = parse_arguments()
    file_path = args.source

    # 1. File Validation
    if file_path.suffix != ".cara":
        print(f"Error: Unsupported file extension '{file_path.suffix}'. Use .cara", file=sys.stderr)
        sys.exit(1)

    if not file_path.exists():
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)

    # 2. Source Loading
    try:
        source_code = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # 3. Lexical Analysis
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()

        if args.tokens:
            print("\n--- TOKEN STREAM ---")
            dump_tokens(tokens)
            return

        # 4. Parsing
        parser = Parser(tokens)
        ast_tree = parser.parse()

        if args.ast:
            print("\n--- ABSTRACT SYNTAX TREE ---")
            dump_ast(ast_tree)
            return

        # 5. Execution
        interpreter = Interpreter(ast_tree)
        interpreter.run()
        print("\nExecution finished successfully.")

    except CarapaceError as e:
        # Catching custom errors and printing to stderr
        print(f"\nCarapace Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Catching unexpected system errors
        print(f"\nInternal System Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()