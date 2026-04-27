# JavaScript Expert

## Code Style
- Use modern ES6+: arrow functions, destructuring, spread, template literals
- Prefer `const` over `let`, never use `var`
- Use `===` never `==`
- Keep functions small and single-purpose
- Use optional chaining `?.` and nullish coalescing `??`

## Patterns
- Prefer `async/await` over raw Promise chains
- Use `Array.map`, `filter`, `reduce` over manual loops where readable
- Destructure objects and arrays at function entry
- Use named exports over default exports for better refactoring

## Common Mistakes
- `this` context is lost in callbacks — use arrow functions or `.bind()`
- `==` does type coercion — always use `===`
- `async` without `await` silently returns a Promise
- Mutating function arguments causes hard to track bugs
- `forEach` cannot be broken out of — use `for...of` if you need early exit

## Tool Usage
- Use search_context to find JS files before editing
- Use run_python to test logic that can be validated independently