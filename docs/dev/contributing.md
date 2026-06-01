# Contributing to MedVista

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Workflow

### 1. Set Up Your Environment

Follow [Development Setup](./setup.md) to get the project running locally.

### 2. Create a Branch

```bash
git checkout -b feat/my-feature     # New feature
git checkout -b fix/my-bugfix       # Bug fix
git checkout -b docs/my-docs        # Documentation
```

### 3. Make Changes

- Follow the coding standards below
- Keep commits focused and atomic
- Write clear commit messages

### 4. Test Your Changes

```bash
# Backend
cd backend && python -m pytest tests/ -v

# Frontend
cd frontend && pnpm build && vue-tsc --noEmit
```

### 5. Submit a Pull Request

- Write a clear PR description
- Reference related issues
- Include screenshots for UI changes
- Ensure all CI checks pass

## Coding Standards

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add PET-CT fusion support
fix: correct SUV calculation for short-lived isotopes
refactor: extract volume loading into composable
docs: update API reference for /ai endpoints
test: add unit tests for useFusion composable
chore: update dependencies
perf: lazy-load Cornerstone3D modules
```

### TypeScript / Vue

- Use `<script setup lang="ts">` for all Vue components
- Define props and emits explicitly with TypeScript
- Use `ref()` and `reactive()` for state
- Composables return an object with named exports
- No `any` types — use `unknown` and narrow

### Python

- Follow PEP 8
- Type hints on all function signatures
- Docstrings for public functions
- FastAPI dependency injection for services
- Async/await for I/O operations

### CSS / Tailwind

- Use Tailwind utility classes
- No inline styles except for dynamic values
- Component-scoped styles when needed
- Dark mode support via `dark:` prefix

## Architecture Guidelines

### Adding a Feature

1. **Backend**: Add route in `routers/`, logic in `services/`
2. **Frontend**: Add composable in `composables/`, view in `views/`
3. **State**: Add to Pinia store if shared, composable if feature-local
4. **i18n**: Add keys in both `en.ts` and `zh-CN.ts`
5. **Types**: Add TypeScript interfaces in `types/index.ts`

### Component Guidelines

- One component per file
- Props defined with `defineProps<{...}>()`
- Emits defined with `defineEmits<{...}>()`
- Use `defineModel()` for v-model bindings
- Template at the bottom of the file

### Composable Guidelines

- Name with `use` prefix
- Return a plain object (not a class)
- Use `onUnmounted()` for cleanup
- Keep under 200 lines — extract helpers if larger
- No DOM access — use refs and lifecycle hooks

## Code Review

### What We Look For

- **Correctness** — Does it work as intended?
- **Security** — No injection, XSS, or data leaks?
- **Performance** — No unnecessary re-renders or API calls?
- **Readability** — Would a new contributor understand this?
- **Testing** — Are critical paths covered?

### Review Checklist

- [ ] No hardcoded secrets
- [ ] Error handling at API boundaries
- [ ] TypeScript types are correct
- [ ] i18n keys added for user-facing text
- [ ] No console.log in production code
- [ ] Build passes (`pnpm build`)
- [ ] Type check passes (`vue-tsc --noEmit`)

## Reporting Issues

When filing an issue, include:

1. **Description** — What happened vs. what you expected
2. **Steps to reproduce** — Minimal sequence to trigger the bug
3. **Environment** — Browser, OS, Node version
4. **Screenshots** — If the issue is visual
5. **Console output** — Any error messages

## Feature Requests

Open an issue with:

1. **Use case** — Why this feature is needed
2. **Proposed solution** — How you think it should work
3. **Alternatives considered** — Other approaches you thought about
4. **Medical context** — If applicable, how this improves clinical workflow

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
