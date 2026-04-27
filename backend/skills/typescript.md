# TypeScript Expert

## Code Style
- Always define explicit types — avoid `any`, use `unknown` if type is truly unknown
- Prefer `interface` for object shapes, `type` for unions and aliases
- Use `readonly` for data that should not be mutated
- Prefer `const` over `let`, never use `var`
- Use optional chaining `?.` and nullish coalescing `??` over manual null checks

## Patterns
- Async functions always return `Promise<T>` — type them explicitly
- Use discriminated unions over boolean flags for state
- Prefer `Array<T>` generics over loose `any[]`
- Use `enum` sparingly — string literal unions are usually cleaner
- Keep types close to where they are used

## Common Mistakes
- `undefined` and `null` are different — handle both explicitly
- `async` without `await` returns a Promise, not a value
- Type assertions (`as T`) hide bugs — use type guards instead
- Do not widen types to fix errors — fix the type mismatch properly

## Tool Usage
- Use search_context to find TypeScript files before editing
- When writing new code match the existing import style (ESM vs CommonJS)