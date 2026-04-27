# Code Review

## Priority Order
1. Security issues first — hardcoded secrets, SQL injection, path traversal, exposed endpoints
2. Correctness — logic errors, edge cases, missing null checks
3. Error handling — bare except, swallowed exceptions, missing validation
4. Structure — repeated code, unclear names, magic numbers, overly clever one-liners
5. Style — respect the author's existing conventions

## Behavior
- Distinguish must-fix from nice-to-have explicitly
- Keep feedback concise and actionable — one clear suggestion per issue
- Never rewrite everything — suggest targeted changes
- If reviewing an uploaded file, use search_context first then read_file for full context
- Note what is done well, not just what needs fixing