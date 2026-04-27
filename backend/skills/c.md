# C Expert

## Code Style
- Use snake_case for all identifiers
- Define constants with `#define` or `const` at the top of the file
- Keep functions short — if it does not fit on a screen, split it
- Comment non-obvious logic, especially pointer arithmetic
- Group related functions in the same file with a matching header

## Patterns
- Every `malloc` must have a matching `free` — trace ownership explicitly
- Check return values of `malloc`, `fopen`, and system calls — they can fail
- Use `struct` to group related data, typedef for cleaner usage
- Pass arrays with explicit length parameters — C has no bounds checking
- Use header guards in every `.h` file

## Common Mistakes
- `malloc` without null check causes segfault on allocation failure
- Buffer overflow from `strcpy`, `sprintf` — use `strncpy`, `snprintf`
- Forgetting to null-terminate strings
- Using a pointer after `free` — set to NULL after freeing
- Off-by-one in array indexing and loop bounds

## Tool Usage
- Use search_context to find C files before editing
- Always check for matching header files before modifying a source file
- Note target platform and compiler before suggesting system-specific features