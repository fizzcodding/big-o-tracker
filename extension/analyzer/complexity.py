def estimate_time_complexity(loop_depth: int, recursive_calls: int) -> str:
    if recursive_calls >= 2:
        return "O(2^n)"
    if recursive_calls == 1:
        return "O(n)"

    if loop_depth == 0:
        return "O(1)"
    if loop_depth == 1:
        return "O(n)"
    if loop_depth == 2:
        return "O(n^2)"

    return f"O(n^{loop_depth})"


def estimate_space_complexity(recursive_calls: int, max_loop_depth: int) -> str:
    if recursive_calls >= 1:
        if recursive_calls >= 2:
            return "O(n)"
        return "O(n)"
    
    return "O(1)"

