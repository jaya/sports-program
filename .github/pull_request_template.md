<!--
Thanks for contributing! Please fill out the template clearly. Items marked with * are required.

Recommended best practices:
- Use a clear, objective title (e.g., feat: add activities endpoint) — prefer Conventional Commits.
- Smaller PRs are easier to review; split into parts when possible.
- Include evidence (screenshots, logs, queries) and testing steps.
-->

## 📝 PR Summary*
Describe in 1–3 sentences what this PR does.

## 🎯 Context/Motivation*
Why is this change needed? What problem or goal does it address?

## 🔗 Related issues
- Closes #
- Relates to #

## 🧩 Type of change*
- [ ] feat (new feature)
- [ ] fix (bug fix)
- [ ] refactor (refactoring with no behavior change)
- [ ] perf (performance improvement)
- [ ] docs (documentation)
- [ ] test (add/adjust tests)
- [ ] chore/build/ci (infra, dependencies, scripts, CI)

## 📸 Evidence
Include screenshots, payload examples, API responses, relevant logs, or GIFs when applicable.

## ✅ Author Checklist*
- [ ] Clear title and well-defined scope
- [ ] Description and motivation filled in
- [ ] Linked issue(s) when applicable
- [ ] Adequate test coverage (unit and/or integration)
- [ ] Ran `pytest` locally with no failures
- [ ] Ran linters/formatters (e.g., `ruff`, `black`, `isort`) if applicable
- [ ] Documentation updated (README, docstrings, comments) when needed
- [ ] Alembic migrations created/applied when needed
- [ ] Backwards compatibility considered (APIs, schemas, contracts)
- [ ] Security and sensitive data reviewed (e.g., environment variables, secrets)
- [ ] Performance impact assessed (N+1, queries, loops)

## 🧪 How to test*
Clear steps to reproduce and validate:
1. 
2. 
3. 

Useful commands:
```
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
poetry run pytest -q
```

## 📚 Implementation notes
Technical details, design decisions, trade-offs, and alternatives considered.

## 🧯 Breaking changes
Any breaking change? If yes, describe the impact and migration plan.

## 🔒 Security considerations
Sensitive data, permissions, validations, sanitization, rate limiting, etc.

## 👀 Notes for reviewers
Points of attention, the most critical areas of the code, or where to focus the review.
