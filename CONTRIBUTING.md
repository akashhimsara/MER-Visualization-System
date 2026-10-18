# Contributing

## Branch Workflow

The project uses the following development flow:

```text
main
  ↑
develop
  ↑
feature branches
```

Current team feature branches:

```text
feature-EVE-Venura
feature/ETS/Mandira
feature/MER/Akash
feature/personalization/Hirusha
```

Team members should work mainly on their assigned feature branch.

When a component is ready for integration:

```text
Feature Branch
      ↓
Pull Request
      ↓
develop
      ↓
Integration Testing
      ↓
main
```

Do not push unfinished development directly to `main`.

For new branches, prefer the naming convention:

```text
feature/<component>/<developer>
```

Example:

```text
feature/MER/Akash
feature/EVE/Venura
feature/ETS/Mandira
feature/personalization/Hirusha
```

---

## Component Boundaries

Each member should mainly modify their assigned research component.

Shared areas such as:

```text
contracts/
apps/
packages/
tests/
```

may affect multiple members and should be changed carefully.

Major shared architecture changes should be discussed with the team before merging.

---

## Shared Contracts

The `contracts/` directory defines the interfaces used between research components.

Do not rename, remove, or change the meaning of shared contract fields without agreement from the affected team members.

Breaking contract changes must use a new contract version.

---

## Repository Hygiene

Do not commit:

- `node_modules/`
- `.venv/`
- `.env` files containing secrets
- raw datasets or large audio collections
- large model checkpoints
- temporary experiment outputs

---

## Commits

Use short, meaningful commit messages.

Examples:

```text
feat: add MER tier 1 emitter
fix: correct transition cooldown logic
test: add recommendation contract tests
docs: update MER research protocol
```

Keep commits focused on one logical change whenever possible.
