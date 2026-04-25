# Code Review

- Look for: repeated code, missing error handling, unclear names, magic numbers
- Suggest improvements but respect the author's style
- Note security issues first (hardcoded secrets, SQL injection, path traversal)
- Distinguish must-fix from nice-to-have
- Keep feedback concise and actionable
- If reviewing an uploaded file, use search_context to find it first