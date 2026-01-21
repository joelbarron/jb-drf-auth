# Release Guide — jb-drf-auth

This document describes the **complete release process** for `jb-drf-auth`, including
local validation, commits, tags, and publishing to **TestPyPI (staging)** and
**PyPI (production)** using **GitHub Actions** and **Trusted Publishing (OIDC)**.

This file is intended to be the **single source of truth** for releases.
Follow these steps **exactly** every time.

---

## Base rules

- **TestPyPI** releases are triggered by **git tags**: `vX.Y.Z-rcN`
- **PyPI (production)** releases are triggered by **GitHub Releases**
- The version in `pyproject.toml` **must always change**
- Pre-release versions must follow **PEP 440**: `X.Y.ZrcN` (no dash)

---

## Local validation (REQUIRED)

Run these commands locally (inside a virtual environment) **before any release**:

```bash
sh test_before_publish.sh
```

If any step fails, **DO NOT RELEASE**.

---

# 🚧 TestPyPI Release (pre-release / staging)

Use this flow to validate:
- package build
- metadata and README rendering
- installation via `pip`

---

## Step 1 — Set pre-release version

Edit `pyproject.toml`:

```toml
version = "0.1.0rc1"
```

Rules:
- Use `rc1`, `rc2`, etc.
- Do **not** use `-rc1` in the version field

---

## Step 2 — Commit version change

```bash
git add pyproject.toml
git commit -m "chore: prepare 0.1.0rc1"
```

---

## Step 3 — Push commit

```bash
git push
```

---

## Step 4 — Create RC tag (triggers TestPyPI workflow)

```bash
git tag v0.1.0-rc1
```

---

## Step 5 — Push tag

```bash
git push --tags
```

This triggers **only** the TestPyPI GitHub Actions workflow.

---

## Step 6 — Verify GitHub Actions

In GitHub:
- Repository → **Actions**
- Workflow: **Publish to TestPyPI**
- Ensure all steps are green

---

## Step 7 — Verify on TestPyPI

Open:

https://test.pypi.org/project/jb-drf-auth/

Confirm:
- version exists
- README renders correctly
- metadata looks correct

---

## Step 8 — Install from TestPyPI

Use a clean environment:

```bash
pip install -i https://test.pypi.org/simple/   --extra-index-url https://pypi.org/simple   jb-drf-auth==0.1.0rc1
```

Optional sanity check:

```bash
python -c "import jb_drf_auth; print('ok')"
```

---

## Step 9 — Additional TestPyPI iterations (if needed)

Repeat the same steps with:
- `0.1.0rc2` → tag `v0.1.0-rc2`
- `0.1.0rc3` → tag `v0.1.0-rc3`

---

# 🚀 PyPI Production Release

Only perform this after **TestPyPI validation succeeds**.

---

## Step 1 — Set final version

Edit `pyproject.toml`:

```toml
version = "0.1.0"
```

---

## Step 2 — Commit final version

```bash
git add pyproject.toml
git commit -m "chore: release 0.1.0"
```

---

## Step 3 — Push commit

```bash
git push
```

---

## Step 4 — Create GitHub Release (triggers PyPI publish)

In GitHub:
1. Repository → **Releases**
2. **Draft a new release**
3. Tag: `v0.1.0`
4. Publish the release

This triggers **only** the PyPI publishing workflow.

---

## Step 5 — Verify on PyPI

Open:

https://pypi.org/project/jb-drf-auth/

Confirm version `0.1.0` exists.

---

## Step 6 — Install from PyPI

```bash
pip install -U jb-drf-auth==0.1.0
```

---

## Important notes

### Versions are immutable
Once a version is published to TestPyPI or PyPI, it **cannot be overwritten**.
Fixes require a new version.

### Tag vs version field
- Git tag (TestPyPI): `vX.Y.Z-rcN`
- Version field (`pyproject.toml`): `X.Y.ZrcN`

### Workflow isolation
- Tags trigger **TestPyPI** only
- GitHub Releases trigger **PyPI** only
- They never overlap

---

## Cost

All release infrastructure is free:
- GitHub Actions (public repositories)
- TestPyPI
- PyPI
- Trusted Publishing

---

## Mental model

> **TestPyPI = staging**  
> **PyPI = production**  
> **Tags test, Releases publish**
