# How to Build and Release Docker Images

This guide explains how to create a new release with multi-platform Docker images (AMD64 + ARM64) via GitHub Actions.

---

## 🎯 Overview

When you create a Git tag, GitHub Actions automatically:
- Builds Docker images for **AMD64** (Intel/AMD) and **ARM64** (Apple Silicon)
- Pushes images to GitHub Container Registry (`ghcr.io`)
- Creates versioned tags (`v2.0.0`) and `latest` tag

**Build Time:** ~20-30 minutes (ARM64 emulation is slow)

---

## 📋 Prerequisites

1. **Branch**: Work in `github-build` branch (or merge to `main` first)
2. **Changes committed**: All your changes are committed
3. **Tests passed**: Code is working locally

---

## 🚀 Release Workflow

### Step 1: Update Version

Update version in relevant files:

```bash
# Update version in pyproject.toml
vim aiproxysrv/pyproject.toml
# Change: version = "2.0.0" → "2.1.0"
```

### Step 2: Commit Changes

```bash
git add .
git commit -m "Bump version to v2.1.0"
git push origin github-build
```

### Step 3: Create and Push Tag

```bash
# Create version tag
git tag v2.1.0 -m "Release v2.1.0 - Description of changes"

# Push tag to trigger build
git push origin v2.1.0
```

### Step 4: Monitor Build

Watch the build progress:
```
https://github.com/rwellinger/thwelly_ai_tools/actions
```

**Expected Duration:** 20-30 minutes

The workflow builds:
- `ghcr.io/rwellinger/aiproxysrv-app:v2.1.0` + `:latest`
- `ghcr.io/rwellinger/celery-worker-app:v2.1.0` + `:latest`
- `ghcr.io/rwellinger/aiwebui-app:v2.1.0` + `:latest`

### Step 5: Create GitHub Release (Optional)

Once build succeeds, create a GitHub Release:

**Via GitHub CLI:**
```bash
gh release create v2.1.0 \
  --title "Release v2.1.0" \
  --notes "## What's New
- Feature A
- Feature B
- Bug fix C

## Docker Images
\`\`\`bash
docker pull ghcr.io/rwellinger/aiproxysrv-app:v2.1.0
docker pull ghcr.io/rwellinger/celery-worker-app:v2.1.0
docker pull ghcr.io/rwellinger/aiwebui-app:v2.1.0
\`\`\`
"
```

**Or via GitHub UI:**
1. Go to: https://github.com/rwellinger/thwelly_ai_tools/releases/new
2. Select tag: `v2.1.0`
3. Add title and description
4. Publish release

---

## 🔧 Troubleshooting

### Build Fails

**Check the logs:**
```
https://github.com/rwellinger/thwelly_ai_tools/actions
```

**Common issues:**
- Missing dependencies in Dockerfile
- Secrets not configured (should not be an issue)
- GitHub Actions policy blocking builds

### Delete and Recreate Tag

If you need to rebuild:

```bash
# Delete local tag
git tag -d v2.1.0

# Delete remote tag
git push origin :refs/tags/v2.1.0

# Create new tag and push
git tag v2.1.0 -m "Release v2.1.0"
git push origin v2.1.0
```

### Manual Trigger

You can also trigger the build manually without a tag:

1. Go to: https://github.com/rwellinger/thwelly_ai_tools/actions/workflows/docker-build.yml
2. Click "Run workflow"
3. Select branch
4. Click "Run workflow" button

---

## 📦 Package Management

### View Published Packages

```
https://github.com/rwellinger?tab=packages
```

### Delete Old Versions

To save storage (500 MB free tier):

1. Go to package page
2. Click on version to delete
3. Click "Delete this version"

### Storage Limits

- **Free Tier**: 500 MB package storage
- **Per Release**: ~400-500 MB (all three images combined)
  - aiproxysrv-app: ~150 MB
  - celery-worker-app: ~150 MB
  - aiwebui-app: ~50 MB
- **Recommendation**: Keep only last 1-2 versions or use `latest` tag only

---

## 🧪 Testing the Release

### Pull and Test Locally

```bash
# Pull the new version
docker pull ghcr.io/rwellinger/aiproxysrv-app:v2.1.0
docker pull ghcr.io/rwellinger/celery-worker-app:v2.1.0
docker pull ghcr.io/rwellinger/aiwebui-app:v2.1.0

# Update docker-compose.yml to use new version
# Or use :latest tag (always pulls newest)

cd aiproxysrv
docker compose pull
docker compose up -d

# Check logs
docker compose logs -f
```

### Verify Multi-Platform

```bash
# Check image architecture
docker inspect ghcr.io/rwellinger/aiproxysrv-app:v2.1.0 | grep Architecture
```

Should show both `amd64` and `arm64` in the manifest.

---

## 📝 Version Naming Convention

Follow semantic versioning:

- **Major** (v3.0.0): Breaking changes
- **Minor** (v2.1.0): New features, backwards compatible
- **Patch** (v2.0.1): Bug fixes only

Examples:
- `v2.0.0` - Initial multi-platform release
- `v2.1.0` - Add new API endpoint
- `v2.0.1` - Fix authentication bug

---

## 🔄 Development vs Production

### Development (Local Build)

```bash
cd aiproxysrv
docker compose -f docker-compose.yml -f docker-compose.dev.yml build
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Production (Pull from Registry)

```bash
cd aiproxysrv
docker compose pull
docker compose up -d
```

---

## ⚙️ GitHub Actions Configuration

The workflow is configured in:
```
.github/workflows/docker-build.yml
```

**Triggers:**
- Git tags matching `v*` pattern
- Manual workflow dispatch

**Builds:**
- Multi-platform: `linux/amd64`, `linux/arm64`
- Multi-stage: `app` and `worker` targets (aiproxysrv), `production` target (aiwebui)
- Pushes to: `ghcr.io/rwellinger/*`
- Three separate jobs run in parallel:
  - `build-app` → `aiproxysrv-app`
  - `build-worker` → `celery-worker-app`
  - `build-webui` → `aiwebui-app`

**Secrets:**
- Uses `GITHUB_TOKEN` (automatically provided)
- No additional secrets needed

---

## 🎯 Quick Reference

```bash
# Complete release workflow
git add .
git commit -m "Release changes"
git push origin github-build

# Create and push tag
git tag v2.1.0 -m "Release v2.1.0"
git push origin v2.1.0

# Monitor: https://github.com/rwellinger/thwelly_ai_tools/actions
# Wait ~25 minutes

# Create release: https://github.com/rwellinger/thwelly_ai_tools/releases/new
```

---

## 📊 GitHub Actions Limits (Free Tier)

- ✅ **Build Minutes**: Unlimited for public repos
- ✅ **Concurrent Jobs**: 20
- ⚠️ **Package Storage**: 500 MB (then $0.008/GB/month)
- ✅ **Package Downloads**: Unlimited

**Recommendation:** Delete old versions to stay under 500 MB limit.
