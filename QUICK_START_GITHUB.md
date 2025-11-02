# Quick Start: Push to GitHub

Your XcceptaPay monorepo is ready to push to GitHub! Here's the fastest way to do it.

## ⚡ Super Quick (2 minutes)

### Option 1: Automated Script (Easiest)

```bash
# Run the automated push script
bash push-to-github.sh
```

This script will:
- ✅ Check for secrets
- ✅ Stage all files
- ✅ Create initial commit
- ✅ Set up remote
- ✅ Push to GitHub

### Option 2: Manual Commands

```bash
# 1. Initialize git (if not already)
git init

# 2. Add all files
git add .

# 3. Check what's staged (verify no secrets!)
git status

# 4. Create initial commit
git commit -m "feat: initial XcceptaPay monorepo - XRPL offline payments stack"

# 5. Create GitHub repo (using GitHub CLI)
gh auth login
gh repo create xcceptapay --private --source=. --remote=origin

# 6. Push to GitHub
git push -u origin main
```

## 🔒 Security Checklist (IMPORTANT!)

Before pushing, verify:

```bash
# Check .env is NOT tracked
git ls-files | grep "\.env$"
# Should return nothing

# Verify .gitignore is working
git check-ignore .env
# Should output: .env

# List what will be pushed
git diff --staged --name-only | grep -E "\.env|seed|key|secret"
# Should return nothing
```

## 📋 What's Being Pushed

Your monorepo includes:

```
✅ api/               - Node.js backend with MongoDB
✅ frontend/          - React + TypeScript dashboard
✅ app/               - Kivy mobile wallet
✅ firmware/          - ESP32 firmware
✅ tools/             - Buyer claim tools
✅ scripts/           - Demo & deployment scripts
✅ docs/              - Architecture & guides
✅ docker-compose.yml - Full stack deployment
✅ README.md          - Complete documentation
✅ .gitignore         - Security (blocks secrets)
✅ LICENSE            - MIT license
✅ CONTRIBUTING.md    - Contribution guide
```

## 🚫 What's NOT Being Pushed (Protected)

```
❌ .env               - Your secrets
❌ node_modules/      - Dependencies
❌ venv/              - Python virtual env
❌ dist/              - Build artifacts
❌ logs/              - Log files
❌ *.seed             - Any seed files
❌ *private*key*      - Any private keys
```

## 🎯 GitHub Repository Setup

### Using GitHub CLI (Recommended)

```bash
# Install GitHub CLI (if not installed)
# Windows: winget install --id GitHub.cli
# Mac: brew install gh
# Linux: See https://github.com/cli/cli#installation

# Login
gh auth login

# Create private repo
gh repo create xcceptapay \
  --private \
  --source=. \
  --remote=origin \
  --description="XRPL Offline Payments - Accept XRP offline, settle online"

# Push
git push -u origin main
```

### Using GitHub Web (Alternative)

1. Go to: https://github.com/new
2. Settings:
   - **Name**: `xcceptapay`
   - **Description**: `XRPL Offline Payments - Accept XRP offline, settle online`
   - **Visibility**: ✅ **Private**
   - ❌ **DO NOT** initialize with README, license, or .gitignore
3. Click **Create repository**
4. Follow on-screen instructions:

```bash
git remote add origin https://github.com/YOUR_USERNAME/xcceptapay.git
git branch -M main
git push -u origin main
```

## ✅ After Pushing

1. **Verify on GitHub**
   - Visit: https://github.com/YOUR_USERNAME/xcceptapay
   - Check: No .env or secrets visible
   - Check: README displays correctly

2. **Add Repository Topics**
   - Go to: Settings → Topics
   - Add: `xrpl`, `blockchain`, `offline-payments`, `paychannels`, `cryptocurrency`

3. **Add Description**
   - Click "Edit" next to repository name
   - Add: "XRPL Offline Payments - Accept XRP offline, settle online. Production-ready with Docker, React dashboard, and ESP32 firmware."

4. **Set Up Team Access** (if working with others)
   - Settings → Collaborators → Add people

## 🔄 Daily Workflow

After initial push, use standard Git workflow:

```bash
# Pull latest changes
git pull

# Make changes to code...

# Stage changes
git add .

# Commit with meaningful message
git commit -m "feat: add webhook notifications"

# Push
git push
```

## 🏷️ Create Release (For Grant Submission)

When ready to submit to XRPL Grants:

```bash
# Create and push tag
git tag -a v1.0.0 -m "XRPL Grants Submission Release"
git push origin v1.0.0
```

Then on GitHub:
1. Go to **Releases** → **Draft a new release**
2. Choose tag: `v1.0.0`
3. Title: `v1.0.0 - XRPL Grants Production Release`
4. Description: Paste milestones and features
5. Attach: Demo video, screenshots
6. **Publish release**

## 🌐 Make Public (When Ready for Submission)

Currently private. To make public for grant submission:

1. Settings → General → Danger Zone
2. **Change repository visibility** → Public
3. Type repository name to confirm
4. Click **I understand, change repository visibility**

## 🆘 Troubleshooting

### "Permission denied" error

```bash
# Set up SSH key
ssh-keygen -t ed25519 -C "your-email@example.com"

# Add to GitHub: Settings → SSH Keys → New SSH Key
# Paste contents of: ~/.ssh/id_ed25519.pub

# Change remote to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/xcceptapay.git
```

### "Authentication failed" (HTTPS)

```bash
# Use Personal Access Token
# GitHub → Settings → Developer settings → Personal access tokens → Generate new token
# Scopes: repo (full control)

# When prompted for password, use the token instead
```

### "Repository not found"

```bash
# Verify remote
git remote -v

# If wrong, update it
git remote set-url origin https://github.com/CORRECT_USERNAME/xcceptapay.git
```

## 📞 Need Help?

- **Detailed Guide**: See [GITHUB_SETUP.md](GITHUB_SETUP.md)
- **GitHub Docs**: https://docs.github.com
- **Git Docs**: https://git-scm.com/doc
- **Support**: support@xacceptapay.com

---

## 🎉 You're Ready!

Your XRPL Offline Payments monorepo is production-ready and secure.

**Run this to push now:**

```bash
bash push-to-github.sh
```

Good luck with your XRPL grant submission! 🚀
