import ast
import requests
from typing import List, Optional, Tuple
from .models import FunctionAnalysis

# Pattern detection rules
def detect_patterns_ast(code: str) -> Optional[Tuple[str, str, int, int]]:
    """Detect common complexity patterns using simple AST rules. Returns (time, space, loops, recursions) or None if no pattern matches."""
    try:        
        tree = ast.parse(code)
        visitor = PatternDetector()
        visitor.visit(tree)
        
        # Check patterns in order of specificity
        time_comp, space_comp, loops, recursions = visitor.get_result()
        
        # If we detected something, return it
        if time_comp and time_comp != "O(?)":
            return (time_comp, space_comp, loops, recursions)
        
        return None
    except:
        return None


class PatternDetector(ast.NodeVisitor):
    """Simple pattern detector for common complexity patterns."""
    
    def __init__(self):
        self.recursive_calls_in_same_path = 0
        self.max_recursive_calls_same_path = 0
        self.has_dividing_recursion = False
        self.has_loop = False
        self.has_dividing_recursion_with_loop = False
        self.has_backtracking_pattern = False
        self.has_append_pop = False
        self.has_sort = False
        self.has_while_with_mid = False
        self.loops_count = 0
        self.recursions_count = 0
        self.current_function_name = None
        self.in_loop = False
        
    def visit_FunctionDef(self, node):
        old_name = self.current_function_name
        self.current_function_name = node.name
        self.recursive_calls_in_same_path = 0
        self.generic_visit(node)
        self.current_function_name = old_name
    
    def visit_For(self, node):
        self.has_loop = True
        self.loops_count += 1
        old_in_loop = self.in_loop
        self.in_loop = True
        self.generic_visit(node)
        self.in_loop = old_in_loop
    
    def visit_While(self, node):
        self.has_loop = True
        self.loops_count += 1
        old_in_loop = self.in_loop
        self.in_loop = True
        
        # Check for binary search pattern (while + mid)
        has_mid = False
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == 'mid':
                        has_mid = True
                        break
        
        if has_mid:
            self.has_while_with_mid = True
        
        self.generic_visit(node)
        self.in_loop = old_in_loop
    
    def visit_Call(self, node):
        # Check for .sort()
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'sort':
            self.has_sort = True
        
        # Check for recursion
        if self.current_function_name:
            is_recursive = False
            if isinstance(node.func, ast.Name) and node.func.id == self.current_function_name:
                is_recursive = True
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "self":
                    if node.func.attr == self.current_function_name:
                        is_recursive = True
            
            if is_recursive:
                self.recursions_count += 1
                self.recursive_calls_in_same_path += 1
                self.max_recursive_calls_same_path = max(
                    self.max_recursive_calls_same_path,
                    self.recursive_calls_in_same_path
                )
                
                # Check if dividing (n/2, n//2, etc.)
                for arg in node.args:
                    if isinstance(arg, ast.BinOp):
                        if isinstance(arg.op, (ast.FloorDiv, ast.Div)):
                            self.has_dividing_recursion = True
                            if self.in_loop:
                                self.has_dividing_recursion_with_loop = True
                    elif isinstance(arg, ast.Name):
                        if arg.id in ['mid', 'left', 'right']:
                            self.has_dividing_recursion = True
        
        # Check for append/pop (backtracking pattern)
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ['append', 'pop']:
                self.has_append_pop = True
                self.has_backtracking_pattern = True
        
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        # Check for append/pop assignments
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Attribute):
                if node.value.func.attr in ['append', 'pop']:
                    self.has_append_pop = True
                    self.has_backtracking_pattern = True
        
        self.generic_visit(node)
    
    def get_result(self) -> Tuple[str, str, int, int]:
        """Apply pattern rules to get complexity."""
        time_comp = "O(?)"
        space_comp = "O(1)"
        
        # Rule 1: sort() -> O(n log n)
        if self.has_sort:
            time_comp = "O(n log n)"
            space_comp = "O(1)"
        
        # Rule 2: while + mid -> O(log n)
        elif self.has_while_with_mid:
            time_comp = "O(log n)"
            space_comp = "O(1)"
        
        # Rule 3: 2+ recursive calls in same path, no divide -> O(2^n)
        elif self.max_recursive_calls_same_path >= 2 and not self.has_dividing_recursion:
            time_comp = "O(2^n)"
            space_comp = "O(n)"
        
        # Rule 4: backtracking + append/pop -> O(2^n)
        elif self.has_backtracking_pattern and self.has_append_pop:
            time_comp = "O(2^n)"
            space_comp = "O(n)"
        
        # Rule 5: recursion divides and single path -> O(log n)
        elif self.has_dividing_recursion and self.max_recursive_calls_same_path <= 1:
            time_comp = "O(log n)"
            space_comp = "O(log n)"
        
        # Rule 6: loop + dividing recursion -> O(n log n)
        elif self.has_dividing_recursion_with_loop or (self.has_loop and self.has_dividing_recursion):
            time_comp = "O(n log n)"
            space_comp = "O(log n)"
        
        # Rule 7: simple loop -> O(n)
        elif self.has_loop and self.recursions_count == 0:
            time_comp = "O(n)"
            space_comp = "O(1)"
        
        # Rule 8: simple recursion -> O(n)
        elif self.recursions_count > 0 and not self.has_dividing_recursion:
            time_comp = "O(n)"
            space_comp = "O(n)"
        
        return (time_comp, space_comp, self.loops_count, self.recursions_count)


def get_complexity_from_llm(code: str) -> Optional[Tuple[str, str, int, int]]:
    """Use LLM (puter API) to analyze code when patterns don't match."""
    prompt = """You are a static code analyzer.

INPUT:
The following text is SOURCE CODE. Do NOT explain it. Do NOT summarize it.

TASK:
Analyze the given source code and output ONLY the following fields, in this EXACT format and order:

Time complexity:
Space complexity:
Loops:
Recursions:

RULES (VERY IMPORTANT):
- Output NOTHING else.
- No explanations.
- No paragraphs.
- No extra lines.
- No bullet points.
- No emojis.
- No markdown.
- If something does not exist, write "None".
- Use standard Big-O notation only (e.g. O(n), O(n log n), O(2^n)).
- Count total loops (for, while, nested included).
- Count recursive functions only if the function calls itself.

SOURCE CODE:
<<<CODE_START>>>
""" + code + """
<<<CODE_END>>>"""
    
    # TODO: Implement puter API call
    # For now, return None to indicate LLM is not available
    # When puter API is available, implement HTTP request here
    return None


def parse_llm_response(text: str) -> Tuple[str, str, int, int]:
    """Parse LLM response to extract complexity info."""
    time_comp = "O(?)"
    space_comp = "O(?)"
    loops = 0
    recursions = 0
    
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        lower = line.lower()
        
        if lower.startswith("time complexity"):
            value = line.split(":", 1)[-1].strip()
            if value and value.lower() != "none":
                time_comp = value
        elif lower.startswith("space complexity"):
            value = line.split(":", 1)[-1].strip()
            if value and value.lower() != "none":
                space_comp = value
        elif lower.startswith("loops"):
            value = line.split(":", 1)[-1].strip()
            if value and value.lower() != "none":
                try:
                    loops = int(value)
                except:
                    loops = 0
        elif lower.startswith("recursions"):
            value = line.split(":", 1)[-1].strip()
            if value and value.lower() != "none":
                try:
                    recursions = int(value)
                except:
                    recursions = 0
    
    return (time_comp, space_comp, loops, recursions)


def analyze_source(source: str) -> List[FunctionAnalysis]:
    """Analyze source code: try pattern detection first, fallback to LLM if no pattern matches."""
    # Try pattern detection first
    result = detect_patterns_ast(source)
    
    if result is None:
        # No pattern matched - use LLM
        result = get_complexity_from_llm(source)
    
    if result is None:
        # Both failed - return defaults
        result = ("O(?)", "O(?)", 0, 0)
    
    time_comp, space_comp, loops, recursions = result
    
    return [
        FunctionAnalysis(
            name="<main>",
            time_complexity=time_comp,
            space_complexity=space_comp,
            max_loop_depth=loops,
            recursive_calls=recursions,
        )
    ]