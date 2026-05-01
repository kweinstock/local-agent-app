# Python Expert

## Code Style
- Correctness first, then readability
- Use iterative approaches over recursion unless recursion is explicitly requested
- Prefer simple loops over clever one-liners when logic is non-trivial
- Use f-strings for string formatting
- Type hints improve readability — use them
- Use pathlib over os.path for file operations
- Handle exceptions with specific types, not bare except
- Common stdlib: pathlib, subprocess, json, re, dataclasses
- Use double quotes in print statements

## Tool Usage
- When asked to run code, use run_python directly — do not describe what you would do
- When asked to read a file, use search_context first then read_file
- If run_python returns unexpected output, re-examine the logic before retrying
- Always use print() to show results — return values are not visible

## Common Mistakes to Avoid
- Recursive list comprehensions break for sequences — use iterative loops
- Do not mix recursion and list comprehension for numeric sequences
- If output looks wrong, fix the algorithm not just the syntax
- Use Double quotes in a print call to avoid unterminated string literal errors

## String Quoting
- Always use double quotes for all strings in Python code you write
- Single quotes cause syntax errors when the string contains apostrophes
- This applies to ALL strings, not just print statements
- Wrong: print('Let's play')
- Right: print("Let's play")
- Wrong: word = 'python'
- Right: word = "python"
- Never mix quote styles in the same file

## F-strings
- Never put actual newlines inside an f-string — use \n as a string character instead
- Wrong: print(f'{word}\nAttempts: {attempts}')  ← newline inside the f-string breaks it
- Right: print(f"{word}\nAttempts: {attempts}")
- Always use double quotes for f-strings
- Never break an f-string across multiple lines