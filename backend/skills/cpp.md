# C++ Expert

## Code Style
- Use modern C++17/20 features where appropriate
- Prefer `const` correctness throughout — const by default
- Use `nullptr` not `NULL` or `0` for pointers
- Use `auto` when type is verbose or obvious from context
- Name classes PascalCase, functions and variables snake_case

## Patterns
- Use RAII — resources should be owned by objects with destructors
- Prefer smart pointers (`unique_ptr`, `shared_ptr`) over raw `new/delete`
- Use references over pointers when null is not a valid state
- Prefer `std::array` over C arrays, `std::vector` over manual heap arrays
- Use range-based for loops over index loops where possible

## Common Mistakes
- Raw `new` without matching `delete` causes memory leaks — use smart pointers
- Dangling references to stack variables returned from functions
- Copying large objects unintentionally — pass by const reference
- Undefined behavior from signed integer overflow
- Using `std::endl` in tight loops — prefer `\n` as `endl` flushes the buffer

## Tool Usage
- Use search_context to find C++ files before editing
- Note which C++ standard is being used before suggesting features
- Check for existing memory management patterns before suggesting changes