from dataclasses import dataclass

@dataclass
class FunctionAnalysis:
    name: str
    time_complexity: str
    space_complexity: str
    max_loop_depth: int
    recursive_calls: int

