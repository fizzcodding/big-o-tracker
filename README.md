📊 Big-O Tracker (v0.1)

Its always trouble finding a great Big-O analasys so I made one a
VS Code extension to estimate time & space complexity of Python code.
Built for competitive programmers, learners, and people who actually care how their code scales.

⚠️ v0.1 – Early version
Results are best-effort heuristics, optimized for CP-style Python code.

Go to your side bar and click the big-o-tracker and open a python file and run analasys and thats it! 


✨ Features

   -  🧠 Detects time complexity (Big-O) per function
   -  💾 Estimates space complexity
   -  🔁 Tracks:
       +  Maximum loop nesting depth
       +  Recursive self-calls
   -  📌 Results shown directly in a VS Code sidebar panel
   -  🐍 Python-only (for now)
   -  ⚡ One-click analysis — no CLI, no extra setup

🖱️ How to Use

   - Open a Python file in VS Code
   - Click the Big-O Tracker icon in the Activity Bar
   - Press Analyze
   - View complexity results per function in the sidebar

🧪 Example
def foo(n):
    for i in range(n):
        for j in range(n):
            print(i, j)

Result in sidebar:
Function: foo
  Time: O(n^2)
  Loops: 2
  Recursion: 0
🧠 How It Works

Uses Python’s AST (Abstract Syntax Tree)

Walks function bodies

Tracks:

Nested loops

Recursive self-calls

Applies heuristic rules to estimate complexity

No runtime execution.
Static analysis only → safe & fast.