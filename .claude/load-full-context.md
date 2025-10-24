# Full Project Context Loader

Load this file when you need complete project context:
`@.claude/load-full-context.md`

---

## Complete Documentation Set

@docs/architecture.md
@docs/authentication.md
@docs/deployment.md
@docs/changelog.md

---

## When to Use This

Use this loader when:
- Starting complex refactoring
- Onboarding to unfamiliar parts of codebase
- Debugging issues that span multiple systems
- Planning major architectural changes

## Token Impact

Loading all docs at once adds approximately:
- architecture.md: ~300 tokens
- authentication.md: ~400 tokens
- deployment.md: ~450 tokens
- changelog.md: ~550 tokens
- **Total: ~1,700 tokens**

This brings your baseline from 57% to about 58%.

## Alternative: Load Selectively

For most tasks, load only what you need:
- Auth work: `@docs/authentication.md`
- System design: `@docs/architecture.md`
- Deployment: `@docs/deployment.md`
- History review: `@docs/changelog.md`
