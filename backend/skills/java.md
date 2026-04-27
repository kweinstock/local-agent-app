# Java Expert

## Code Style
- Use PascalCase for classes, camelCase for methods and variables
- Keep classes focused — single responsibility
- Prefer composition over inheritance
- Use `final` for variables that should not be reassigned
- Avoid raw types — always parameterize generics

## Patterns
- Use streams and lambdas for collection operations
- Prefer `Optional<T>` over returning null
- Use `try-with-resources` for anything that implements `AutoCloseable`
- Use builder pattern for objects with many fields
- Prefer interfaces over abstract classes for type contracts

## Common Mistakes
- `==` compares references not values for objects — use `.equals()`
- Not closing streams and connections — always use try-with-resources
- Catching `Exception` or `Throwable` — catch specific exceptions
- Mutable static state causes threading bugs
- `NullPointerException` — use Optional or null checks defensively

## Tool Usage
- Use search_context to find Java files before editing
- Note the Java version before suggesting features (streams = 8+, records = 16+)