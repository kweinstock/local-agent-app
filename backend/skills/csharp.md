# C# Expert

## Code Style
- Use PascalCase for classes and methods, camelCase for local variables
- Prefer `var` when type is obvious from the right side
- Use expression-bodied members for simple one-liners
- Prefer records for immutable data transfer objects
- Use `string.IsNullOrEmpty` or `string.IsNullOrWhiteSpace` over manual checks

## Patterns
- Always use `async/await` over `.Result` or `.Wait()` — they cause deadlocks
- Use LINQ for collection queries but avoid chaining too many operations
- Prefer `IEnumerable<T>` in method signatures over concrete types
- Use `using` declarations for disposable resources
- Prefer dependency injection over static classes

## Common Mistakes
- `.Result` on async methods causes deadlocks in ASP.NET contexts
- Forgetting `await` returns a Task not the value
- `string` concatenation in loops — use `StringBuilder`
- Not disposing `HttpClient` — use `IHttpClientFactory`
- Catching `Exception` base class — catch specific exceptions

## Tool Usage
- Use search_context to find C# files before editing
- Note the .NET version and namespace structure before suggesting patterns