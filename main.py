import sys
from pathlib import Path

from src.lexer import Lexer
from src.parser import Parser
from src.interpreter import Interpreter
from src.errors import CarapaceError

def main():
    # FILE LOADING
    
    # file_path = Path("examples/square.cara")
    file_path = Path("examples/star.cara")

    # Check file extension
    if file_path.suffix != ".cara":
        print(f"Error: Unsupported file extension '{file_path.suffix}'. Expected '.cara'.")
        sys.exit(1)

    # Check if file exists
    if not file_path.exists():
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    # Load code from file
    with open(file_path, 'r', encoding='utf-8') as file:
        source_code = file.read()

    try:
        # Lexical Analysis
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()

        # Parsing (Tokens -> AST Tree)
        parser = Parser(tokens)
        ast_tree = parser.parse()

        # Execution
        interpreter = Interpreter(ast_tree)
        interpreter.run()

        print("Execution finished successfully.")

    except CarapaceError as e:
        print(f"Carapace Error: {e}")

if __name__ == "__main__":
    main()