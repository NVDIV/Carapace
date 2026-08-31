"""Command-line entry point for the Carapace interpreter."""

import sys

import argparse

from pathlib import Path

from Carapace.src.lexer import Lexer
from Carapace.src.parser import Parser
from Carapace.src.interpreter import Interpreter
from Carapace.src.semantic_analyzer import SemanticAnalyzer
from Carapace.src import __version__
from Carapace.src.errors import CarapaceError, SourceFileError


def parse_arguments():
    """Parse command-line arguments for the Carapace interpreter."""
    parser = argparse.ArgumentParser(
        prog="carapace",
        description="Carapace Language Interpreter - A turtle graphics DSL.",
        epilog="Example: python main.py examples/square.cara --tokens",
    )

    parser.add_argument(
        "source",
        type=Path,
        help="The .cara source file to execute",
    )
    parser.add_argument(
        "-t",
        "--tokens",
        action="store_true",
        help="Perform lexical analysis and print token stream",
    )
    parser.add_argument(
        "-a",
        "--ast",
        action="store_true",
        help="Parse code and display the Abstract Syntax Tree",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Carapace DSL {__version__}",
    )

    return parser.parse_args()


def load_source(file_path: Path) -> str:
    """Validate and read a UTF-8 Carapace source file."""
    if file_path.suffix != ".cara":
        raise SourceFileError(
            f"Unsupported file extension '{file_path.suffix}'. Use .cara"
        )

    if not file_path.exists():
        raise SourceFileError(f"File '{file_path}' not found")

    if not file_path.is_file():
        raise SourceFileError(f"Source path '{file_path}' is not a file")

    try:
        return file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise SourceFileError(f"Cannot read source file '{file_path}': {exc}") from exc


def dump_tokens(tokens):
    """Print a token stream as a compact human-readable table."""
    print(f"{'TOKEN TYPE':<15} | {'VALUE':<15} | {'LINE':<5}")
    print("-" * 45)
    for token in tokens:
        print(f"{token.type.name:<15} | {str(token.value):<15} | {token.line:<5}")


def dump_ast(nodes, level=0):
    """Recursively print AST nodes using tree-style indentation."""
    for node in nodes:
        indent = "  " * level
        node_name = type(node).__name__

        attributes = {k: v for k, v in vars(node).items() if k != "body"}
        attr_str = f"({attributes})" if attributes else ""

        print(f"{indent}└── {node_name} {attr_str}")

        if hasattr(node, "body"):
            dump_ast(node.body, level + 1)


def main():
    """Run the complete Carapace source-to-execution pipeline."""
    args = parse_arguments()
    file_path = args.source

    try:
        # Source loading
        source_code = load_source(file_path)

        # Lexical analysis
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()

        if args.tokens:
            print("\n--- TOKEN STREAM ---")
            dump_tokens(tokens)
            return

        # Parsing
        parser = Parser(tokens)
        ast_tree = parser.parse()

        if args.ast:
            print("\n--- ABSTRACT SYNTAX TREE ---")
            dump_ast(ast_tree)
            return

        # Semantic analysis
        semantic_result = SemanticAnalyzer(ast_tree).analyze()

        # Execution
        interpreter = Interpreter(ast_tree, semantic_result)
        interpreter.run()
        print("\nExecution finished successfully.")

    except CarapaceError as e:
        print(f"\nCarapace Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nInternal System Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
