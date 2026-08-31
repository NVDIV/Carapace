"""Runtime environments for Carapace.

Carapace has exactly one global runtime environment and one fresh function
runtime environment for each active call.  Function environments always point
directly to the global environment; caller environments never participate in
name lookup.
"""

from Carapace.src.errors import RuntimeError


class GlobalEnvironment:
    """Stores global variable values and all global function definitions."""

    def __init__(self):
        """Create an empty global variable and function namespace."""
        self.variables = {}
        self.functions = {}

    def set_variable(self, name: str, value):
        """Create or update a variable in global scope."""
        self.variables[name] = value

    def get_variable(self, name: str):
        """Return a global variable value or raise a Carapace runtime error."""
        if name in self.variables:
            return self.variables[name]
        raise RuntimeError(f"Undefined variable: '{name}'")

    def define_function(self, name: str, node):
        """Register a globally visible function definition."""
        self.functions[name] = node

    def get_function(self, name: str):
        """Return a global function definition or raise a runtime error."""
        if name in self.functions:
            return self.functions[name]
        raise RuntimeError(f"Undefined function: '{name}'")


class FunctionEnvironment:
    """Stores parameters and locals for one active function invocation."""

    def __init__(self, parent: GlobalEnvironment):
        """Create a fresh local scope linked directly to the global scope."""
        if not isinstance(parent, GlobalEnvironment):
            raise TypeError("FunctionEnvironment parent must be GlobalEnvironment")
        self.variables = {}
        self.parent = parent

    def set_variable(self, name: str, value):
        """Always assign in the current function-local scope."""
        self.variables[name] = value

    def get_variable(self, name: str):
        """Look up local variables first, then the global environment."""
        if name in self.variables:
            return self.variables[name]
        return self.parent.get_variable(name)
