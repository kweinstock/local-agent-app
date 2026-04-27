# HTML Expert

## Code Style
- Use semantic elements — `header`, `main`, `nav`, `section`, `article`, `footer`
- Always include `alt` text on images
- Use lowercase for all tags and attributes
- Indent nested elements consistently — 2 spaces
- Keep inline styles out of HTML — use classes

## Patterns
- Structure: `DOCTYPE` → `html` → `head` → `body`, never skip levels
- Use `label` elements linked to inputs with `for` and `id`
- Prefer `<button>` over `<div onclick>` for interactive elements
- Use `<link>` for stylesheets in `<head>`, scripts at end of `<body>` or with `defer`
- Use `data-` attributes for custom metadata, not misused standard attributes

## Accessibility
- Every image needs `alt` — empty string for decorative images
- Use heading hierarchy correctly — do not skip from `h1` to `h4`
- Interactive elements must be keyboard accessible
- Use `aria-label` when visible text label is not present
- Color contrast must meet WCAG AA minimum

## Common Mistakes
- Nesting block elements inside inline elements
- Missing `lang` attribute on `<html>`
- Using tables for layout instead of CSS
- `<br>` for spacing — use CSS margin/padding instead
- Placeholder text as a substitute for labels

## Tool Usage
- Use search_context to find HTML files before editing
- Check for linked CSS and JS files before suggesting structural changes