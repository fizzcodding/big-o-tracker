import sys
import json
from .ast_parser import analyze_source


def main():
    source_code = sys.stdin.read()

    try:
        results = analyze_source(source_code)
    except SyntaxError as e:
        print(json.dumps({
            "error": "SyntaxError",
            "message": str(e)
        }))
        return

    output = [
        {
            "function": r.name,
            "big_o": r.time_complexity,
            "space_complexity": r.space_complexity,
            "loops": r.max_loop_depth,
            "recursion": r.recursive_calls,
        }
        for r in results
    ]

    print(json.dumps(output))


if __name__ == "__main__":
    main()

