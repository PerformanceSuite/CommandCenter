"""
Python AST Parser for Phase 7 Graph Indexer

Extracts symbols (classes, functions, imports) from Python source code using the ast module.
"""

import ast
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.models.graph import DependencyType, SymbolKind


@dataclass
class ParsedSymbol:
    """Parsed symbol from source code"""

    kind: SymbolKind
    name: str
    qualified_name: str
    signature: Optional[str]
    range_start: int
    range_end: int
    exports: bool
    is_async: bool
    is_generator: bool
    docstring: Optional[str] = None


@dataclass
class ParsedDependency:
    """Parsed dependency between symbols"""

    from_symbol: str  # Qualified name
    to_symbol: str  # Qualified name or module path
    type: DependencyType
    line_number: int


@dataclass
class ParsedTodo:
    """Parsed TODO/FIXME comment"""

    kind: str  # TODO, FIXME, XXX, HACK, NOTE
    title: str
    description: Optional[str]
    file_path: str
    line_number: int


class PythonParser:
    """Parse Python source code using AST"""

    def __init__(self):
        self.symbols: List[ParsedSymbol] = []
        self.dependencies: List[ParsedDependency] = []
        self.todos: List[ParsedTodo] = []
        self.module_name: str = ""
        self.file_path: str = ""

    def parse(
        self, source: str, file_path: str
    ) -> Tuple[List[ParsedSymbol], List[ParsedDependency]]:
        """
        Parse Python source code and extract symbols and dependencies.

        Args:
            source: Python source code
            file_path: File path for qualified names (e.g., 'app/services/graph_service.py')

        Returns:
            Tuple of (symbols, dependencies)
        """
        self.symbols = []
        self.dependencies = []
        self.todos = []
        self.file_path = file_path
        self.module_name = self._path_to_module(file_path)

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            # Log parse error but don't fail
            print(f"Syntax error in {file_path}: {e}")
            return [], []

        # Extract TODOs from comments
        self._extract_todos(source, file_path)

        # Walk AST and extract symbols
        self._visit_node(tree, parent_names=[])

        return self.symbols, self.dependencies

    def get_todos(self) -> List[ParsedTodo]:
        """Get extracted TODO/FIXME comments"""
        return self.todos

    def _path_to_module(self, file_path: str) -> str:
        """Convert file path to module name (e.g., 'app/services/foo.py' -> 'app.services.foo')"""
        # Remove .py extension
        if file_path.endswith(".py"):
            file_path = file_path[:-3]

        # Convert slashes to dots
        module = file_path.replace("/", ".").replace("\\", ".")

        # Remove leading dots
        module = module.lstrip(".")

        return module

    def _visit_node(self, node: ast.AST, parent_names: List[str]):
        """Recursively visit AST nodes and extract symbols"""

        if isinstance(node, ast.ClassDef):
            self._extract_class(node, parent_names)
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            self._extract_function(node, parent_names)
        elif isinstance(node, ast.Import):
            self._extract_import(node)
        elif isinstance(node, ast.ImportFrom):
            self._extract_import_from(node)

        # Recursively visit children
        for child in ast.iter_child_nodes(node):
            self._visit_node(child, parent_names)

    def _extract_class(self, node: ast.ClassDef, parent_names: List[str]):
        """Extract class definition"""
        qualified_name = ".".join(parent_names + [node.name]) if parent_names else node.name
        full_qualified_name = f"{self.module_name}.{qualified_name}"

        # Check if class is exported (not private)
        exports = not node.name.startswith("_")

        # Get base classes (filter out None values)
        bases = [name for name in [self._get_node_name(base) for base in node.bases] if name]
        signature = f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"

        # Extract docstring
        docstring = ast.get_docstring(node)

        symbol = ParsedSymbol(
            kind=SymbolKind.CLASS,
            name=node.name,
            qualified_name=full_qualified_name,
            signature=signature,
            range_start=node.lineno,
            range_end=node.end_lineno or node.lineno,
            exports=exports,
            is_async=False,
            is_generator=False,
            docstring=docstring,
        )
        self.symbols.append(symbol)

        # Extract base class dependencies
        for base in node.bases:
            base_name = self._get_node_name(base)
            if base_name and base_name != "object":
                dep = ParsedDependency(
                    from_symbol=full_qualified_name,
                    to_symbol=base_name,
                    type=DependencyType.EXTENDS,
                    line_number=node.lineno,
                )
                self.dependencies.append(dep)

        # Recursively process methods
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._extract_function(child, parent_names + [node.name])

    def _extract_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, parent_names: List[str]
    ):
        """Extract function/method definition"""
        qualified_name = ".".join(parent_names + [node.name]) if parent_names else node.name
        full_qualified_name = f"{self.module_name}.{qualified_name}"

        # Check if function is exported
        exports = not node.name.startswith("_")

        # Build signature
        args_list = []
        for arg in node.args.args:
            arg_name = arg.arg
            # Include type annotation if present
            if arg.annotation:
                arg_type = self._get_node_name(arg.annotation)
                args_list.append(f"{arg_name}: {arg_type}")
            else:
                args_list.append(arg_name)

        # Add *args and **kwargs
        if node.args.vararg:
            args_list.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            args_list.append(f"**{node.args.kwarg.arg}")

        args_str = ", ".join(args_list)

        # Return type annotation
        return_type = ""
        if node.returns:
            return_type = f" -> {self._get_node_name(node.returns)}"

        # Async prefix
        async_prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""

        signature = f"{async_prefix}def {node.name}({args_str}){return_type}"

        # Check if generator (contains yield)
        is_generator = self._is_generator(node)

        # Extract docstring
        docstring = ast.get_docstring(node)

        # Determine symbol kind
        if parent_names:
            # Method of a class
            kind = SymbolKind.FUNCTION  # Could differentiate methods in future
        else:
            # Module-level function
            kind = SymbolKind.FUNCTION

        # Special case for test functions
        if node.name.startswith("test_"):
            kind = SymbolKind.TEST

        symbol = ParsedSymbol(
            kind=kind,
            name=node.name,
            qualified_name=full_qualified_name,
            signature=signature,
            range_start=node.lineno,
            range_end=node.end_lineno or node.lineno,
            exports=exports,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_generator=is_generator,
            docstring=docstring,
        )
        self.symbols.append(symbol)

        # Extract function call dependencies
        self._extract_function_calls(node, full_qualified_name)

    def _extract_import(self, node: ast.Import):
        """Extract import statement"""
        # Create dependency (module-level, not symbol-level for now)
        # Could be enhanced to track which symbols use which imports
        pass

    def _extract_import_from(self, node: ast.ImportFrom):
        """Extract 'from X import Y' statement"""
        # Track import for dependency resolution
        pass

    def _extract_function_calls(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, caller_qname: str
    ):
        """Extract function calls within a function body"""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                callee_name = self._get_node_name(child.func)
                if callee_name:
                    dep = ParsedDependency(
                        from_symbol=caller_qname,
                        to_symbol=callee_name,
                        type=DependencyType.CALL,
                        line_number=child.lineno,
                    )
                    self.dependencies.append(dep)

    def _is_generator(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if function contains yield statement"""
        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    def _get_node_name(self, node: ast.AST) -> Optional[str]:
        """Get name from AST node (handles Name, Attribute, etc.)"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Handle dotted names like 'pkg.module.Class'
            value_name = self._get_node_name(node.value)
            if value_name:
                return f"{value_name}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return None

    def _extract_todos(self, source: str, file_path: str):
        """Extract TODO/FIXME comments from source code"""
        # Regex pattern for TODO comments
        # Matches: # TODO: description or # FIXME: description
        pattern = re.compile(
            r"^\s*#\s*(TODO|FIXME|XXX|HACK|NOTE):\s*(.+?)$", re.MULTILINE | re.IGNORECASE
        )

        for match in pattern.finditer(source):
            kind = match.group(1).upper()
            title = match.group(2).strip()

            # Get line number
            line_number = source[: match.start()].count("\n") + 1

            # Try to extract multi-line description (look for continuation comments)
            description_lines = [title]
            lines = source.split("\n")
            for i in range(line_number, min(line_number + 5, len(lines))):
                line = lines[i].strip()
                if line.startswith("#") and not any(
                    kw in line.upper() for kw in ["TODO", "FIXME", "XXX", "HACK", "NOTE"]
                ):
                    description_lines.append(line.lstrip("#").strip())
                else:
                    break

            description = " ".join(description_lines) if len(description_lines) > 1 else None

            todo = ParsedTodo(
                kind=kind,
                title=title,
                description=description,
                file_path=file_path,
                line_number=line_number,
            )
            self.todos.append(todo)
