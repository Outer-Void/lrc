# Repository Snapshot

## 1) Metadata
- Repository name: lrc
- Organization / owner: unknown
- Default branch (if detectable): unknown
- HEAD commit hash (if available): 8566d26f7441c9cd0fc8d818ca6abea0acf0f548
- Snapshot timestamp (UTC): 2026-01-21T08:00:43Z
- Total file count (excluding directories): 55
- Description: Local Repo Compiler that turns declarative .lrc schema files into production-ready repositories.

## 2) Repository Tree
├── .github/
│   └── workflows/
│       ├── lrc-build.yml [text]
│       ├── sign-and-release.yaml [text]
│       └── sign-and-release.yml [text]
├── docs/
│   ├── assets/
│   │   └── lrc-logo-green.png [binary]
│   ├── dat-integration.md [text]
│   ├── getting-started.md [text]
│   └── troubleshooting.md [text]
├── examples/
│   ├── dat_integration.lrc [text]
│   ├── forgekit_schema_full.lrc [text]
│   ├── schema_dev_example.lrc [text]
│   ├── schema_entprse_example.lrc [text]
│   ├── schema_example.lrc [text]
│   └── schema_org_example.lrc [text]
├── src/
│   └── lrc/
│       ├── cli/
│       │   ├── __init__.py [text]
│       │   └── main.py [text]
│       ├── compiler/
│       │   └── __init__.py [text]
│       ├── generator/
│       │   └── __init__.py [text]
│       ├── parser/
│       │   └── __init__.py [text]
│       ├── templates/
│       │   ├── node-cli/
│       │   │   ├── bin/
│       │   │   │   └── cli.js [text]
│       │   │   ├── README.md [text]
│       │   │   └── package.json [text]
│       │   ├── python-cli/
│       │   │   ├── src/
│       │   │   │   ├── __init__.py [text]
│       │   │   │   └── main.py [text]
│       │   │   ├── README.md [text]
│       │   │   └── pyproject.toml [text]
│       │   ├── rust-cli/
│       │   │   ├── src/
│       │   │   │   └── main.rs [text]
│       │   │   ├── Cargo.toml [text]
│       │   │   └── README.md [text]
│       │   └── __init__.py [text]
│       ├── __init__.py [text]
│       ├── __main__.py [text]
│       ├── audit.py [text]
│       ├── bootstrap.py [text]
│       ├── compiler.py [text]
│       ├── core.py [text]
│       ├── generator.py [text]
│       ├── integration.py [text]
│       ├── main.py [text]
│       └── parser.py [text]
├── tests/
│   ├── data/
│   │   └── simple.lrc [text]
│   ├── test_cli.py [text]
│   ├── test_cli_audit.py [text]
│   ├── test_dat_integration.py [text]
│   ├── test_integration.py [text]
│   ├── test_parser.py [text]
│   └── test_parser_trust.py [text]
├── .gitignore [text]
├── LICENSE [text]
├── README.md [text]
├── install_deps.sh [text]
├── jadis_publickey.asc [text]
├── lrc [text]
├── pyproject.toml [text]
├── requirements.txt [text]
└── trusted_templates.json [text]

## 3) FULL FILE CONTENTS (MANDATORY)

FILE: .github/workflows/lrc-build.yml
Kind: text
Size: 721
Last modified: 2026-01-21T07:58:23Z

CONTENT:
name: LRC Build

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.11", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]
      - name: Lint
        run: |
          black --check src tests
          mypy src/lrc
      - name: Tests
        run: |
          pytest --cov=src/lrc --cov-report=term-missing


FILE: .github/workflows/sign-and-release.yaml
Kind: text
Size: 14011
Last modified: 2026-01-21T07:58:23Z

CONTENT:
name: Sign and Release

on:
  # Automatic trigger on version tags
  push:
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+'        # Major.Minor.Patch (v1.0.0)
      - 'v[0-9]+.[0-9]+.[0-9]+-rc.[0-9]+'  # Release candidates (v1.0.0-rc.1)
      - 'v[0-9]+.[0-9]+.[0-9]+-beta.[0-9]+' # Beta releases (v1.0.0-beta.1)
      - 'v[0-9]+.[0-9]+.[0-9]+-alpha.[0-9]+' # Alpha releases (v1.0.0-alpha.1)
  
  # Manual trigger for creating signed tags and releases
  workflow_dispatch:
    inputs:
      ref:
        description: 'Ref to tag (branch, commit SHA, or existing tag)'
        required: false
        default: 'main'
      tag_name:
        description: 'Tag name (must follow semver: v1.0.0, v2.1.0-rc.1)'
        required: true
        default: 'v1.0.0'
      tag_message:
        description: 'Tag annotation message'
        required: false
        default: 'Signed release'
      make_release:
        description: 'Create GitHub Release?'
        required: false
        default: true
        type: boolean
      generate_changelog:
        description: 'Generate changelog for release?'
        required: false
        default: true
        type: boolean
      prerelease:
        description: 'Mark as prerelease?'
        required: false
        default: false
        type: boolean

# Required permissions for release operations
permissions:
  contents: write
  id-token: write  # For enhanced security

env:
  PYTHON_VERSION: '3.9'
  NODE_VERSION: '18'

jobs:
  # ------------------------------------------------------------------
  # A) Automated release when tag is pushed
  # ------------------------------------------------------------------
  release-on-tag:
    name: Release on Tag Push
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/')
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Verify tag format
        run: |
          TAG_NAME="${{ github.ref_name }}"
          if [[ ! $TAG_NAME =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-(alpha|beta|rc)\.[0-9]+)?$ ]]; then
            echo "❌ Invalid tag format: $TAG_NAME"
            echo "📋 Must follow: vMAJOR.MINOR.PATCH or vMAJOR.MINOR.PATCH-(alpha|beta|rc).NUMBER"
            exit 1
          fi
          echo "✅ Valid tag: $TAG_NAME"

      - name: Checkout repository (with full history and tags)
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Setup Git identity
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"

      - name: Import GPG key for verification
        uses: crazy-max/ghaction-import-gpg@v6
        with:
          gpg_private_key: ${{ secrets.GPG_PRIVATE_KEY }}
          passphrase: ${{ secrets.GPG_PASSPHRASE }}
          git_user_signingkey: true
          git_commit_gpgsign: true

      - name: Verify tag signature
        run: |
          TAG_NAME="${{ github.ref_name }}"
          if git verify-tag "$TAG_NAME" 2>/dev/null; then
            echo "✅ Tag $TAG_NAME is properly signed"
          else
            echo "❌ Tag $TAG_NAME is not signed or signature is invalid"
            exit 1
          fi

      - name: Setup Python
        if: hashFiles('pyproject.toml') != ''
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install Python dependencies
        if: hashFiles('pyproject.toml') != ''
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build Python package
        if: hashFiles('pyproject.toml') != ''
        run: |
          python -m build
          # Verify the built packages
          twine check dist/*

      - name: Setup Node.js
        if: hashFiles('package.json') != ''
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Build Node.js package
        if: hashFiles('package.json') != ''
        run: |
          npm ci
          npm run build --if-present
          npm test --if-present

      - name: Generate changelog
        id: changelog
        uses: orhun/git-cliff-action@v2
        with:
          config: cliff.toml
          args: --verbose --tag ${{ github.ref_name }}
        env:
          OUTPUT: CHANGES.md

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ github.ref_name }}
          name: Release ${{ github.ref_name }}
          body_path: CHANGES.md
          draft: false
          prerelease: ${{ contains(github.ref_name, 'alpha') || contains(github.ref_name, 'beta') || contains(github.ref_name, 'rc') }}
          files: |
            dist/**
            *.whl
            *.tar.gz
            *.zip
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Upload release assets
        if: hashFiles('dist/*') != ''
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ steps.create_release.outputs.upload_url }}
          asset_path: ./dist/
          asset_name: ${{ github.ref_name }}-assets.zip
          asset_content_type: application/zip

      - name: Notify success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: success
          channel: '#releases'
          text: "🎉 Release ${{ github.ref_name }} published successfully!"
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

  # ------------------------------------------------------------------
  # B) Manual workflow for creating signed tags and releases
  # ------------------------------------------------------------------
  create-signed-tag:
    name: Create Signed Tag
    if: github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.prerelease && 'staging' || 'production' }}

    steps:
      - name: Validate inputs
        run: |
          TAG_NAME="${{ github.event.inputs.tag_name }}"
          if [[ ! $TAG_NAME =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-(alpha|beta|rc)\.[0-9]+)?$ ]]; then
            echo "❌ Invalid tag format: $TAG_NAME"
            echo "📋 Must follow semantic versioning: vMAJOR.MINOR.PATCH or vMAJOR.MINOR.PATCH-(alpha|beta|rc).NUMBER"
            exit 1
          fi
          echo "✅ Valid tag format: $TAG_NAME"

      - name: Checkout repository (with full history)
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ github.event.inputs.ref }}
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Setup Git identity
        run: |
          git config --global user.name "${{ secrets.GIT_USER_NAME || 'github-actions[bot]' }}"
          git config --global user.email "${{ secrets.GIT_USER_EMAIL || 'github-actions[bot]@users.noreply.github.com' }}"

      - name: Import GPG key for signing
        uses: crazy-max/ghaction-import-gpg@v6
        with:
          gpg_private_key: ${{ secrets.GPG_PRIVATE_KEY }}
          passphrase: ${{ secrets.GPG_PASSPHRASE }}
          git_user_signingkey: true
          git_commit_gpgsign: true

      - name: Verify current commit
        run: |
          echo "Current commit: $(git rev-parse HEAD)"
          echo "Current branch: $(git branch --show-current)"

      - name: Create signed tag
        id: create_tag
        run: |
          TAG_NAME="${{ github.event.inputs.tag_name }}"
          TAG_MESSAGE="${{ github.event.inputs.tag_message }}"
          
          # Check if tag already exists
          if git rev-parse -q --verify "refs/tags/${TAG_NAME}" >/dev/null; then
            echo "❌ Tag $TAG_NAME already exists"
            echo "💡 Delete existing tag or use a different name"
            exit 1
          fi
          
          # Create annotated, GPG-signed tag
          git tag -s "${TAG_NAME}" -m "${TAG_MESSAGE}"
          
          # Verify the tag was created and signed
          if git verify-tag "${TAG_NAME}"; then
            echo "✅ Successfully created and signed tag: ${TAG_NAME}"
            echo "tag_name=${TAG_NAME}" >> $GITHUB_OUTPUT
          else
            echo "❌ Failed to verify tag signature"
            exit 1
          fi

      - name: Push signed tag
        run: |
          TAG_NAME="${{ github.event.inputs.tag_name }}"
          git push origin "${TAG_NAME}"
          echo "📤 Pushed tag ${TAG_NAME} to remote"

      - name: Setup Python
        if: hashFiles('pyproject.toml') != '' && github.event.inputs.make_release == true
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Build Python package
        if: hashFiles('pyproject.toml') != '' && github.event.inputs.make_release == true
        run: |
          python -m pip install --upgrade pip
          pip install build twine
          python -m build
          twine check dist/*

      - name: Setup Node.js
        if: hashFiles('package.json') != '' && github.event.inputs.make_release == true
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Build Node.js package
        if: hashFiles('package.json') != '' && github.event.inputs.make_release == true
        run: |
          npm ci
          npm run build --if-present
          npm test --if-present

      - name: Generate changelog
        if: github.event.inputs.make_release == true && github.event.inputs.generate_changelog == true
        uses: orhun/git-cliff-action@v2
        with:
          config: cliff.toml
          args: --verbose --tag ${{ github.event.inputs.tag_name }}
        env:
          OUTPUT: CHANGES.md

      - name: Create GitHub Release
        if: github.event.inputs.make_release == true
        id: create_release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ github.event.inputs.tag_name }}
          name: Release ${{ github.event.inputs.tag_name }}
          body_path: CHANGES.md
          draft: false
          prerelease: ${{ github.event.inputs.prerelease }}
          files: |
            dist/**
            *.whl
            *.tar.gz
            *.zip
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Upload release assets
        if: github.event.inputs.make_release == true && hashFiles('dist/*') != ''
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ steps.create_release.outputs.upload_url }}
          asset_path: ./dist/
          asset_name: ${{ github.event.inputs.tag_name }}-assets.zip
          asset_content_type: application/zip

      - name: Notify success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: success
          channel: '#releases'
          text: "🎉 ${{ github.event.inputs.tag_name }} created and released successfully!"
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

  # ------------------------------------------------------------------
  # C) Security scanning for releases
  # ------------------------------------------------------------------
  security-scan:
    name: Security Scan
    needs: [release-on-tag, create-signed-tag]
    if: always() && (needs.release-on-tag.result == 'success' || needs.create-signed-tag.result == 'success')
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
          
      - name: Upload Trivy scan results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
          
      - name: Dependency review
        uses: actions/dependency-review-action@v4

  # ------------------------------------------------------------------
  # D) Post-release cleanup and notifications
  # ------------------------------------------------------------------
  post-release:
    name: Post-Release
    needs: [release-on-tag, create-signed-tag]
    if: always()
    runs-on: ubuntu-latest
    
    steps:
      - name: Release summary
        if: always()
        run: |
          echo "🏷️ Release Summary"
          echo "================="
          echo "Workflow: ${{ github.workflow }}"
          echo "Event: ${{ github.event_name }}"
          echo "Tag: ${{ github.ref_name || github.event.inputs.tag_name }}"
          echo "Result: ${{ needs.release-on-tag.result || needs.create-signed-tag.result }}"
          echo "URL: https://github.com/${{ github.repository }}/releases/tag/${{ github.ref_name || github.event.inputs.tag_name }}"
          
      - name: Update release badge
        if: success()
        uses: schneegans/dynamic-badges-action@v1.7.0
        with:
          auth: ${{ secrets.GIST_SECRET }}
          gistID: ${{ secrets.BADGES_GIST_ID }}
          filename: release.json
          label: Release
          message: ${{ github.ref_name || github.event.inputs.tag_name }}
          color: green
          namedLogo: github

      - name: Notify failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: failure
          channel: '#alerts'
          text: "❌ Release failed for ${{ github.ref_name || github.event.inputs.tag_name }}"
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}


FILE: .github/workflows/sign-and-release.yml
Kind: text
Size: 1330
Last modified: 2026-01-21T07:58:23Z

CONTENT:
name: Sign and Release

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      tag:
        description: 'SemVer tag to sign (e.g. v1.0.0-alpha.1)'
        required: true

jobs:
  sign-and-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Import signing key
        uses: crazy-max/ghaction-import-gpg@v6
        with:
          gpg_private_key: ${{ secrets.GPG_PRIVATE_KEY }}
          passphrase: ${{ secrets.GPG_PASSPHRASE }}
          git_user_signingkey: true
          git_commit_gpgsign: true
      - name: Verify tag signature
        run: |
          if [[ "${GITHUB_REF}" == refs/tags/* ]]; then
            git verify-tag "${GITHUB_REF_NAME}"
          else
            git tag -s "${{ github.event.inputs.tag }}" -m "Signed release"
          fi
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Build package
        run: |
          python -m pip install --upgrade pip
          pip install build twine
          python -m build
          twine check dist/*
      - name: Publish release
        uses: softprops/action-gh-release@v2
        with:
          files: dist/*
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}


FILE: .gitignore
Kind: text
Size: 4920
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# LRC - Local Repo Compile
# Cross-platform .gitignore for Python project development

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class
*.so

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
.pytest_cache/
.coverage
cover/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
#Pipfile.lock

# PEP 582; used by e.g. github.com/David-OConnor/pyflow
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Windows
# Windows thumbnail cache files
Thumbs.db
ehthumbs.db

# Folder config file
[Dd]esktop.ini

# Recycle Bin used on file shares
$RECYCLE.BIN/

# Windows Installer files
*.cab
*.msi
*.msix
*.msm
*.msp

# Windows shortcuts
*.lnk

# macOS
*.DS_Store
.AppleDouble
.LSOverride

# Icon must end with two \r
Icon

# Thumbnails
._*

# Files that might appear in the root of a volume
.DocumentRevisions-V100
.fseventsd
.Spotlight-V100
.TemporaryItems
.Trashes
.VolumeIcon.icns
.com.apple.timemachine.donotpresent

# Directories potentially created on remote AFP share
.AppleDB
.AppleDesktop
Network Trash Folder
Temporary Items
.apdisk

# Android/Termux
.termux/

# LRC specific
# Generated output directories (prevent accidentally committing generated projects)
lrc_output/
*_output/
generated_*/

# Test output
test_output/
tmp/
temp/

# LRC cache and state
.lrc_cache/
.lrc_state.json

# Schema test files (optional - if you want to ignore test schema files)
test_*.lrc

# Local configuration
local_config.py
config.local.*
.secrets.*

# Logs
*.log
logs/

# Profiling data
.prof

# Package manager specific
# Poetry
poetry.lock

# PDMP
pdm.lock

# Pipenv
Pipfile.lock

# PyUP
safety.txt

# Mypy
.mypy_cache/

# Benchmarking
benchmarks/output/

# Documentation builds
docs/_build/
docs/_static/
docs/_templates/

# Sphinx
docs/source/generated/

# MkDocs
site/

# Jupyter
.jupyter/

# VS Code
.vscode/settings.json
.vscode/launch.json
.vscode/tasks.json

# PyCharm
.idea/workspace.xml
.idea/tasks.xml
.idea/dictionaries
.idea/vcs.xml
.idea/jsLibraryMappings.xml
.idea/dataSources.ids
.idea/sqlDataSources.xml
.idea/dynamic.xml
.idea/uiDesigner.xml
.idea/inspectionProfiles/

# Eclipse
.pydevproject
.project
.metadata
tmp/
*.tmp
*.bak
*.swp
*~.nib
local.properties
.classpath
.settings/
.loadpath

# Emacs
*~
\#*\#
/.emacs.desktop
/.emacs.desktop.lock
*.elc
auto-save/
tramp
.\#*

# Vim
[._]*.s[a-w][a-z]
[._]s[a-w][a-z]
*.un~
Session.vim
.netrwhist
*~

# Visual Studio Code
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json
*.code-workspace

# Local History for Visual Studio Code
.history/

# Project-specific patterns
# Add any project-specific patterns here

# LRC template cache (if implemented in future)
.template_cache/

# Temporary files
*.tmp
*.temp
.cache/

# Package releases (should be in dist/ but just in case)
*.tar.gz
*.whl

# OS X
.AppleDouble
.LSOverride

# Linux
*~

# KDE
.directory

# Temporary files
*~
*.swp
*.swo

# Package files
*.7z
*.dmg
*.gz
*.iso
*.jar
*.rar
*.tar
*.zip

# Backup files
*.bak
*.backup

# LRC development
# Ignore test projects created during development
test_project_*/
demo_*/
example_output/

# Coverage reports
.coverage
.coverage.*
htmlcov/

# Performance profiling
.prof
.line_profiler

# Complexidade
complexity.txt

# Bandit security tool
.bandit

# Safety
.safety

# pre-commit
.pre-commit-config.yaml

# Docker
.dockerignore

# Vagrant
.vagrant/

# Kubernetes
*-config.yaml
*-secret.yaml

# Terraform
.terraform/
*.tfstate
*.tfstate.backup
*.tfvars

# Ansible
*.retry

# Molecule
.molecule/
.cache


FILE: LICENSE
Kind: text
Size: 1063
Last modified: 2026-01-21T07:58:23Z

CONTENT:
MIT License

Copyright (c) 2025 ~JADIS

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


FILE: README.md
Kind: text
Size: 6655
Last modified: 2026-01-21T07:58:23Z

CONTENT:
<p align="center">
  <img src="./docs/assets/lrc-logo-green.png" alt="LRC — Local Repo Compile" width="600">
</p>

# ⚙️ LRC — Local Repo Compiler

**LRC** (Local Repo Compiler) turns declarative `.lrc` schema files into complete, production-ready repositories. Version **v1.0.0-alpha.1** introduces a modular architecture, DAT audit integration, and enterprise security features such as template trust policies and GPG validation for imported schemas.

---

## ✨ Highlights

- ✅ Modular runtime (`parser`, `compiler`, `generator`, `cli`) under `src/lrc`
- ✅ Robust schema language with heredocs, variable expansion, and nested directives
- ✅ Trusted template policy via `trusted_templates.json`
- ✅ Optional DAT post-build auditing via `--audit`
- ✅ Cross-platform bootstrap for Linux, macOS, Windows, WSL, and Termux
- ✅ Python **3.9 → 3.13** compatibility with automated linting, typing, and tests

---

## 🚀 Quick Start

### Install
```bash
# Clone & bootstrap dependencies
git clone https://github.com/Justadudeinspace/lrc.git
cd lrc
chmod +x install_deps.sh
./install_deps.sh

# Optional: install the CLI into ~/.local/bin (or platform equivalent)
python -m lrc --bootstrap
```

### Compile a schema
```bash
# Generate a repo from a schema file
lrc schema_example.lrc -o ./generated

# Preview actions without touching disk
lrc schema_example.lrc --dry-run

# Force overwrites and run DAT audit afterwards
lrc schema_example.lrc -o ./generated --force --audit
```

> **Tip:** `lrc --platform-info` prints environment diagnostics useful for troubleshooting cross-platform quirks.

---

## 🧩 Schema Language Essentials

### Metadata & variables
```text
# Project: Demo Service
# Description: REST API scaffold
# Version: 1.0.0

@set AUTHOR=Acme
@set DESCRIPTION=Internal tooling
```

Use `${VARIABLE}` anywhere in paths, filenames, or file contents.

### File expressions
```text
src/              # create directories recursively
README.md         # empty file
config.json -> {"debug": false}               # inline file
script.py <<PY                                # heredoc file
#!/usr/bin/env python3
print("Hello ${AUTHOR}")
PY
```

### Directives
| Directive | Description |
|-----------|-------------|
| `@set KEY=VALUE` | Define variables in the parser scope |
| `@ignore pattern` | Skip actions whose paths match `fnmatch` patterns |
| `@template name` | Render a trusted template (validated via `trusted_templates.json`) |
| `@chmod path mode` | Apply a POSIX mode (e.g. `0o755`) |
| `@include file` | Include another `.lrc` file (GPG signature validated when present) |
| `@copy src dest` | Copy an existing file into the build output |
| `@symlink target link` | Create symbolic links |

> Place `trusted_templates.json` beside your schema (or in `~/.config/lrc/`) to extend the allow-list. Attempting to use untrusted templates raises a `ParseError` with contextual hints.

---

## 🔐 Security & Trust

### Template trust policy
LRC reads `trusted_templates.json` from:
1. The schema directory or `.lrc/` subdirectory
2. `~/.config/lrc/trusted_templates.json`
3. The repository default (see `trusted_templates.json` in the project root)

Only templates listed in the allow-list may be rendered. Attempting to use an untrusted template aborts the build with a red, contextual error message.

### GPG-validated includes
When an included schema has a sibling signature file (`.asc` or `.sig`), LRC verifies the signature with `gpg --verify`. Set `LRC_REQUIRE_SIGNED_INCLUDES=1` to require signatures for every `@include`. Invalid or missing signatures raise descriptive `ParseError`s that highlight the offending line in the source schema.

---

## 🧰 CLI Reference
```
lrc SCHEMA [OPTIONS]

Options:
  -o, --output PATH    Override output directory
  --base-dir PATH      Base directory for resolving includes
  --dry-run            Preview actions without writing to disk
  --force              Overwrite existing files
  --audit              Run the DAT audit pipeline after a successful build
  -v, --verbose        Emit verbose logs and platform info
  --bootstrap          Install the CLI into the user PATH
  --platform-info      Dump environment diagnostics
  --version            Print version information
```

`--audit` reads `~/.config/lrc/dat_integration.json`:
```json
{
  "enabled": true,
  "command": ["dat", "audit", "--report", "${BUILD_DIR}"],
  "env": {"DAT_ENV": "production"}
}
```
If the file is absent, auditing is skipped with an informative message.

---

## 🔄 LRC → DAT Workflow Example
1. Author your schema (see [`examples/dat_integration.lrc`](./examples/dat_integration.lrc)).
2. Configure DAT integration in `~/.config/lrc/dat_integration.json`.
3. Compile the schema with `lrc examples/dat_integration.lrc -o ./build --audit`.
4. Inspect DAT output logged immediately after a successful build.

DAT command failures are surfaced with warnings while keeping the repository intact.

---

## 🧪 Quality Tooling

- `pytest` test suite covering parser, compiler, and CLI behaviours
- `mypy` static typing, `black` formatting, and coverage reporting via CI (`.github/workflows/lrc-build.yml`)
- Works on CPython 3.9, 3.10, 3.11, 3.12, and 3.13

Run locally:
```bash
pip install -e .[dev]
pytest
mypy src/lrc
black --check src tests
```

---

## 🆘 Troubleshooting

| Symptom | Resolution |
|---------|------------|
| `GPG executable not available` | Install `gpg` or unset `LRC_REQUIRE_SIGNED_INCLUDES`. |
| Template rejected as untrusted | Add the template to `trusted_templates.json` in the schema directory or config path. |
| DAT audit skipped | Ensure `~/.config/lrc/dat_integration.json` exists and `enabled` is `true`. |
| PATH not updated after `--bootstrap` | Re-run your shell or source the printed profile file. |

Use `lrc --platform-info` when reporting issues to include environment details.

---

## 🧽 Schema Lint Checklist

- [ ] Metadata (`# Project`, `# Description`, `# Version`) defined at the top
- [ ] Variables declared before use with `@set`
- [ ] Templates approved via `trusted_templates.json`
- [ ] Includes accompanied by `.asc` signatures when required
- [ ] Avoid trailing whitespace — indentation controls directory nesting

---

## 📚 Further Reading

- [`docs/getting-started.md`](./docs/getting-started.md) — step-by-step tutorial
- [`docs/dat-integration.md`](./docs/dat-integration.md) — configuring the DAT bridge
- [`docs/troubleshooting.md`](./docs/troubleshooting.md) — extended FAQ
- [`examples/`](./examples) — ready-to-run schemas for diverse stacks

---

© 2024 LRC contributors. Licensed under the MIT License.


FILE: docs/assets/lrc-logo-green.png
Kind: binary
Size: 1209752
Last modified: 2026-01-21T07:58:23Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 1209752
detected type: binary

FILE: docs/dat-integration.md
Kind: text
Size: 1174
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# DAT Integration Guide

LRC can trigger the DAT auditing pipeline immediately after a successful repository build. This guide explains the configuration surface.

## 1. Configure DAT

Create `~/.config/lrc/dat_integration.json`:

```json
{
  "enabled": true,
  "command": ["dat", "audit", "--report", "${BUILD_DIR}"],
  "env": {
    "DAT_API_TOKEN": "example-token"
  }
}
```

- `enabled`: toggles the audit step
- `command`: a string or array executed after the build. `${BUILD_DIR}` is replaced with the output directory.
- `env`: optional environment variables added to the subprocess.

## 2. Run the compiler

```bash
lrc examples/dat_integration.lrc -o ./build/dat --audit
```

The CLI prints `[AUDIT]` messages summarising DAT output. Failures surface as warnings without deleting the generated repository.

## 3. Troubleshooting

| Symptom | Resolution |
|---------|------------|
| `DAT command not found` | Ensure the binary referenced by `command` exists on `PATH`. |
| Exit code non-zero | Review the logged stdout/stderr. LRC continues but reports the failure. |
| Config parse error | Validate the JSON in `dat_integration.json` (comments are not supported). |


FILE: docs/getting-started.md
Kind: text
Size: 956
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# Getting Started with LRC

This quick guide walks through compiling a repository from a declarative `.lrc` schema using the v1.0.0-alpha.1 toolchain.

## 1. Prepare your environment

```bash
python -m pip install --upgrade pip
pip install -e .[dev]
```

## 2. Author a schema

Create `quickstart.lrc`:

```text
# Project: Quickstart Service
# Description: Demo API scaffold

@set AUTHOR=Quick Start Team
src/
  __init__.py
  main.py <<PY
  from pathlib import Path

  def main() -> None:
      print("Hello from LRC!")

  if __name__ == "__main__":
      main()
PY
README.md -> # Quickstart Service
```

## 3. Compile

```bash
lrc quickstart.lrc -o ./build/quickstart
```

Use `--dry-run` to preview actions and `--audit` to run the DAT pipeline after a successful build.

## 4. Explore

```bash
tree build/quickstart
python build/quickstart/src/main.py
```

You're ready to extend the schema with directives such as `@template`, `@copy`, and `@include`.


FILE: docs/troubleshooting.md
Kind: text
Size: 885
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# Troubleshooting

## Parser errors
- **`Template 'foo' is not trusted`** – add `"foo"` to `trusted_templates.json` in the schema directory or `~/.config/lrc/`.
- **`GPG executable not available for signature verification`** – install `gpg` or unset `LRC_REQUIRE_SIGNED_INCLUDES`.
- **`Included file not found`** – includes are resolved relative to `--base-dir` (defaults to the schema directory).

## DAT integration
- Check that `dat_integration.json` is valid JSON.
- Commands may be a string (`"dat audit"`) or array (`["dat", "audit"]`).
- LRC replaces `${BUILD_DIR}` tokens with the absolute build path.

## Bootstrap
- When running `lrc --bootstrap`, the installer appends to common shell rc files (`.bashrc`, `.zshrc`, `.profile`). Restart your shell afterwards.

## Getting help
Run `lrc --platform-info` and capture the output together with the failing schema snippet.


FILE: examples/dat_integration.lrc
Kind: text
Size: 587
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# Project: LRC + DAT Demo
# Description: Example pipeline demonstrating DAT auditing
# Version: 1.0.0-alpha.1

@set AUTHOR=Enterprise Team
@set PKG=dat-demo

src/
  __init__.py
  main.py <<PY
  """Entry point for DAT integration smoke test."""

  def main() -> None:
      print("DAT audit ready")

  if __name__ == "__main__":
      main()
PY

README.md <<MD
# LRC + DAT Demo

This project illustrates how to run the DAT audit pipeline after LRC finishes building.

* Configure `~/.config/lrc/dat_integration.json`
* Execute `lrc examples/dat_integration.lrc -o ./build/dat --audit`
MD


FILE: examples/forgekit_schema_full.lrc
Kind: text
Size: 40051
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# =========================================================
#  FORGEKIT — Built by LRC (Local Repo Compile)
#  A developer's forge that generates its own source.
#  Hidden message: "Everything you build builds you."
#  Author: ${AUTHOR}
#  Year: ${YEAR}
#  License: ${LICENSE}
#  Schema-Version: 1.1
#  Generator: LRC v0.2.2
#  Compatible-With: Python 3.8+
# =========================================================

# ==================== METADATA & VARIABLES ====================
# Project: forgekit
# Description: Portable developer forge toolkit for schema-driven repo creation
# Version: 0.2.0
# License: MIT

@set AUTHOR=~JADIS | Justadudeinspace
@set EMAIL=theoutervoid@outlook.com
@set PKG=forgekit
@set DESC=Portable developer forge toolkit for schema-driven repo creation
@set YEAR=2025
@set LICENSE=MIT
@set PYTHON_VERSION=3.8
@set PROJECT_URL=https://github.com/Justadudeinspace/forgekit
@set SECRET_MSG=Everything you build builds you.
@set CLI_NAME=forgekit
@set FORGE_VERSION=0.2.0

# Ignore common noise
@ignore node_modules .venv __pycache__ .DS_Store *.tmp build dist *.egg-info .mypy_cache .pytest_cache

# Demonstrate template usage (e.g., python-cli)
@template python-cli

# (Optional) include shared changelog content
@include ../partials/CHANGELOG.lrc

# ==================== PROJECT SKELETON ====================
/src
/docs
/tests
/scripts
/assets
/examples
/bin

# ==================== SOURCE CODE ====================
/src
  __init__.py <<PY
"""${PKG} — ${DESC}"""

__version__ = "${FORGE_VERSION}"
__author__ = "${AUTHOR}"
__email__ = "${EMAIL}"

from .cli import main
from .forge import forge, render_template, parse_simple_schema, realize
from .utils import read_text, write_text, stringify_tree, validate_schema_file

__all__ = [
    "main", 
    "forge", 
    "render_template", 
    "parse_simple_schema", 
    "realize",
    "read_text", 
    "write_text", 
    "stringify_tree",
    "validate_schema_file"
]
PY

  cli.py <<PY
#!/usr/bin/env python3
"""${PKG} — ${DESC}"""

import argparse
import sys
from pathlib import Path
from .__init__ import __version__
from .forge import forge
from .utils import stringify_tree, validate_schema_file

def main(argv=None):
    parser = argparse.ArgumentParser(prog="${CLI_NAME}", description="${DESC}")
    parser.add_argument("schema", nargs="?", help="Schema file to compile")
    parser.add_argument("-o", "--out", help="Output directory (default: ./<Project> or ./${PKG}_output)")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Preview actions; do not write")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logs")
    parser.add_argument("--version", action="version", version=f"${PKG} {__version__}")
    parser.add_argument("--platform-info", action="store_true", help="Show platform details")
    
    args = parser.parse_args(argv)

    if args.platform_info:
        import platform
        import os
        print(f"Platform: {platform.platform()}")
        print(f"Python: {platform.python_version()}")
        print(f"CWD: {Path.cwd()}")
        print(f"Env: TERM={os.environ.get('TERM', '')}")
        return 0

    if not args.schema:
        parser.print_help()
        print(f"\nExamples:")
        print(f"  {CLI_NAME} examples/quickstart.lrc")
        print(f"  {CLI_NAME} schema.lrc -o ./myproject --dry-run")
        return 2

    schema_path = Path(args.schema)
    
    # Validate schema file
    if not validate_schema_file(schema_path):
        return 1

    result = forge(
        schema_path=schema_path,
        out_dir=Path(args.out) if args.out else None,
        dry_run=args.dry_run,
        force=args.force,
        verbose=args.verbose,
    )

    if args.verbose and result.get("tree"):
        print("\n📁 Generated Structure:")
        print(stringify_tree(result["tree"]))

    if result.get("success"):
        print(f"✅ Forge complete → {result['out_dir']}")
        if not args.dry_run:
            print(f"📦 Created {result['files_created']} files, {result['dirs_created']} directories")
        return 0
    else:
        print(f"❌ Forge failed: {result.get('error', 'Unknown error')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
PY
  @chmod src/cli.py +x

  forge.py <<PY
"""Forge core: parses simple LRC-like schema fragments at runtime."""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import os
import re

def render_template(text: str, vars: Dict[str, str]) -> str:
    """Render template variables in text."""
    if not text:
        return text
    
    def replace_var(match):
        var_name = match.group(1)
        return vars.get(var_name, match.group(0))
    
    pattern = r'\\$\\{([^}]+)\\}'
    return re.sub(pattern, replace_var, text)

def parse_simple_schema(text: str, vars: Dict[str, str]) -> List[Tuple[str, Optional[str]]]:
    """
    Minimal parser for lines like:
      path.ext -> CONTENT
      path.ext (empty)
      dir/     (dir)
      heredoc:
        file.txt <<TAG
        ...lines...
        TAG
        
    Returns list of (path, content) where content=None means directory marker.
    """
    lines = text.splitlines()
    i = 0
    result = []
    
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        i += 1
        
        # Skip empty lines and comments
        if not s or s.startswith("#"):
            continue
            
        # Handle heredoc syntax
        if "<<" in s and "->" not in s:
            try:
                left, tag = [p.strip() for p in s.split("<<", 1)]
                path = render_template(left, vars)
                tag = tag.strip() or "EOF"
                buf = []
                
                # Collect heredoc content
                while i < len(lines) and lines[i].strip() != tag:
                    buf.append(lines[i])
                    i += 1
                    
                # Skip the closing tag line
                if i < len(lines):
                    i += 1
                    
                content = "\\n".join(buf)
                result.append((path, content))
                continue
                
            except (ValueError, IndexError):
                # Fallback: treat as regular file
                path = render_template(s, vars)
                result.append((path, ""))
                continue
        
        # Directory marker
        if s.endswith("/") and "->" not in s:
            path = render_template(s[:-1], vars)
            result.append((path + "/", None))
            continue
            
        # Inline file content
        if "->" in s:
            try:
                left, right = [p.strip() for p in s.split("->", 1)]
                path = render_template(left, vars)
                content = render_template(right, vars)
                result.append((path, content))
                continue
            except (ValueError, IndexError):
                # Fallback: treat as regular file
                path = render_template(s, vars)
                result.append((path, ""))
                continue
        
        # Plain file (empty content)
        path = render_template(s, vars)
        result.append((path, ""))
        
    return result

def realize(plan: List[Tuple[str, Optional[str]]], out_dir: Path, dry: bool = False, force: bool = False) -> Dict[str, Any]:
    """Realize the parsed plan into actual filesystem operations."""
    created_dirs = []
    created_files = []
    errors = []
    
    for path, content in plan:
        try:
            target = out_dir / path
            
            # Handle directories
            if content is None or path.endswith("/"):
                if dry:
                    print(f"[DRY] mkdir -p {target}")
                else:
                    target.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(target))
                
            # Handle files
            else:
                if target.exists() and not force:
                    print(f"[SKIP] {target} exists (use --force)")
                    continue
                    
                if dry:
                    print(f"[DRY] write {target} ({len(content)} bytes)")
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding="utf-8")
                created_files.append(str(target))
                
        except Exception as e:
            error_msg = f"Failed to create {path}: {e}"
            errors.append(error_msg)
            print(f"[ERROR] {error_msg}")
    
    return {
        "dirs_created": created_dirs,
        "files_created": created_files,
        "errors": errors,
        "success": len(errors) == 0
    }

def forge(schema_path: Path, out_dir: Optional[Path] = None, dry_run: bool = False, 
          force: bool = False, verbose: bool = False) -> Dict[str, Any]:
    """Main forge function to compile schema into filesystem structure."""
    try:
        # Read and validate schema
        text = schema_path.read_text(encoding="utf-8")
        
        # Basic variable set
        vars = {
            "PROJECT": "${PKG}",
            "AUTHOR": "${AUTHOR}",
            "EMAIL": "${EMAIL}",
            "DESC": "${DESC}",
            "VERSION": "${FORGE_VERSION}",
            "YEAR": "${YEAR}",
            "LICENSE": "${LICENSE}",
            "CLI_NAME": "${CLI_NAME}",
            "SECRET_MSG": "${SECRET_MSG}",
        }
        
        # Parse schema
        plan = parse_simple_schema(text, vars)
        
        # Determine output directory
        if out_dir is None:
            out_dir = Path.cwd() / "${PKG}_output"
        
        if verbose:
            print(f"[forge] Output directory: {out_dir}")
            print(f"[forge] Plan items: {len(plan)}")
            print(f"[forge] Dry run: {dry_run}")
            print(f"[forge] Force: {force}")
        
        # Realize the plan
        result = realize(plan, out_dir, dry=dry_run, force=force)
        
        # Build tree structure for display
        tree = {}
        for path in result["dirs_created"]:
            tree[path] = "dir"
        for path in result["files_created"]:
            tree[path] = "file"
        
        return {
            "out_dir": str(out_dir),
            "tree": tree,
            "files_created": len(result["files_created"]),
            "dirs_created": len(result["dirs_created"]),
            "errors": result["errors"],
            "success": result["success"]
        }
        
    except Exception as e:
        return {
            "out_dir": str(out_dir) if out_dir else "unknown",
            "tree": {},
            "files_created": 0,
            "dirs_created": 0,
            "errors": [str(e)],
            "success": False
        }
PY

  utils.py <<PY
"""Utilities for I/O, validation, and pretty-printing."""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import os

def read_text(path: Path) -> str:
    """Read text from file with proper error handling."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise IOError(f"Cannot read file {path}: {e}")

def write_text(path: Path, content: str) -> None:
    """Write text to file with proper directory creation."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except Exception as e:
        raise IOError(f"Cannot write file {path}: {e}")

def stringify_tree(tree: Dict[str, str]) -> str:
    """Convert tree structure to readable string."""
    if not tree:
        return "(empty)"
    
    items = sorted(tree.items(), key=lambda kv: kv[0])
    lines = []
    
    for path, kind in items:
        indent_level = path.count("/") - 1
        indent = "  " * max(0, indent_level)
        
        if kind == "dir":
            icon = "📁"
            name = Path(path).name + "/"
        else:
            icon = "📄"
            name = Path(path).name
            
        lines.append(f"{indent}{icon} {name}")
    
    return "\\n".join(lines)

def validate_schema_file(schema_path: Path) -> bool:
    """Validate that schema file exists and is readable."""
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False
        
    if not schema_path.is_file():
        print(f"❌ Schema path is not a file: {schema_path}")
        return False
        
    try:
        # Quick read test
        schema_path.read_text(encoding="utf-8")
        return True
    except Exception as e:
        print(f"❌ Cannot read schema file: {e}")
        return False

def get_file_size(path: Path) -> int:
    """Get file size in bytes."""
    try:
        return path.stat().st_size
    except:
        return 0

def format_file_size(bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"
PY

# ==================== DOCUMENTATION ====================
/docs
  README.md <<MD
<p align="center">
  <img src="../assets/logo.svg" width="120" />
</p>

<h1 align="center">FORGEKIT</h1>
<p align="center"><em>${DESC}</em></p>

<div align="center">

![License](https://img.shields.io/badge/license-${LICENSE}-blue.svg)
![Python](https://img.shields.io/badge/python-${PYTHON_VERSION}+-green.svg)
![Version](https://img.shields.io/badge/version-${FORGE_VERSION}-orange.svg)

</div>

## 🚀 Features

- **Schema → Repo** compilation in one command
- **Simple syntax** with variables, heredocs, and directives
- **Cross-platform** support (Linux/macOS/Windows/WSL2/Termux)
- **Extensible core** with template rendering and filesystem operations
- **Comprehensive tooling** with tests, docs, and build scripts

## 📦 Installation

### Development Setup
\`\`\`bash
# Clone and setup
git clone ${PROJECT_URL}
cd forgekit

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\\\Scripts\\\\activate

# Install in development mode
pip install -e .

# Or use the provided script
./scripts/install-dev.sh
\`\`\`

### System Installation
\`\`\`bash
# Install via pip (when published)
pip install forgekit
\`\`\`

## 🛠️ Usage

### Basic Compilation
\`\`\`bash
# Generate project from schema
${CLI_NAME} examples/quickstart.lrc

# Custom output directory
${CLI_NAME} schema.lrc -o ./myproject

# Preview without writing (dry run)
${CLI_NAME} schema.lrc --dry-run -v

# Force overwrite existing files
${CLI_NAME} schema.lrc --force
\`\`\`

### Schema Syntax
\`\`\`bash
# Comments and metadata
# Project: My Project
# Description: My description

# Variables (used in templates)
@set AUTHOR=Your Name

# Directories
/src
/docs/

# Files with inline content
README.md -> # My Project

# Files with heredoc content
script.py <<PY
#!/usr/bin/env python3
print("Hello World")
PY

# Empty files
config.json
\`\`\`

### CLI Reference
\`\`\`bash
${CLI_NAME} --help           # Show help
${CLI_NAME} --version        # Show version
${CLI_NAME} --platform-info  # Show system information
\`\`\`

## 🧪 Development

\`\`\`bash
# Run tests
./scripts/test.sh

# Build package
./scripts/build.sh

# Type checking
python -m mypy src/ tests/

# Code formatting
python -m black src/ tests/
\`\`\`

## 📁 Project Structure

\`\`\`
forgekit/
├── src/           # Source code
│   ├── __init__.py
│   ├── cli.py     # Command-line interface
│   ├── forge.py   # Core compilation logic
│   └── utils.py   # Utility functions
├── tests/         # Test suite
├── docs/          # Documentation
├── scripts/       # Development scripts
├── assets/        # Static assets
├── examples/      # Example schemas
└── bin/           # Binary helpers (reserved)
\`\`\`

## 🔧 API Reference

### Core Functions

\`\`\`python
from forgekit import forge, render_template

# Compile schema to filesystem
result = forge(
    schema_path="my_schema.lrc",
    out_dir="./output",
    dry_run=False,
    force=False,
    verbose=True
)

# Render templates with variables
text = render_template("Hello ${NAME}", {"NAME": "World"})
\`\`\`

### Utilities
\`\`\`python
from forgekit import read_text, write_text, stringify_tree

# File operations
content = read_text(Path("file.txt"))
write_text(Path("output.txt"), "content")

# Tree visualization
tree = {"src/": "dir", "src/main.py": "file"}
print(stringify_tree(tree))
\`\`\`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: \`git checkout -b feature/new-feature\`
3. Commit changes: \`git commit -am 'Add new feature'\`
4. Push to branch: \`git push origin feature/new-feature\`
5. Submit a pull request

## 📄 License

This project is licensed under the ${LICENSE} License - see the [LICENSE](../LICENSE) file for details.

## 🎯 Easter Egg

Open [EASTER_EGG.md](./EASTER_EGG.md) to discover the hidden message.

> "*${SECRET_MSG}*"
MD

  EASTER_EGG.md <<MD
# 🪞 Developer Easter Egg — The Self-Forging Forge

> "*${SECRET_MSG}*"

## The Reflection

You built **ForgeKit** from a single schema using **LRC** (Local Repo Compile). 
Now **ForgeKit** can generate its own demo projects, scripts, and documentation.

The compiler is the lesson. The forge that builds itself teaches the deepest truth:

> *Every tool you create changes you as a creator.*
> *Every system you design reflects your understanding.*
> *Every abstraction you build shapes how you think.*

## The Cycle

1. **LRC** compiles schemas into projects
2. **ForgeKit** is born from such a schema  
3. **ForgeKit** can now compile its own schemas
4. The cycle continues...

## The Message

This isn't just about code generation. It's about:

- **Meta-creation**: Tools that create tools
- **Self-reference**: Systems that describe themselves
- **Recursive improvement**: Each generation building upon the last

You're not just building software—you're building the *capacity to build*.

> *"We become what we behold. We shape our tools and then our tools shape us."* — Marshall McLuhan

*Continue the cycle. Build something that builds you better.*
MD

  API_REFERENCE.md <<MD
# API Reference

## Command Line Interface

### Basic Usage
\`\`\`bash
${CLI_NAME} schema.lrc                 # Compile schema
${CLI_NAME} schema.lrc -o ./output     # Custom output directory
${CLI_NAME} schema.lrc --dry-run -v    # Preview with verbose output
${CLI_NAME} --help                     # Show help
${CLI_NAME} --version                  # Show version
${CLI_NAME} --platform-info            # Show system information
\`\`\`

### Options
- \`schema\`: Path to schema file (required)
- \`-o, --out\`: Output directory (default: ./${PKG}_output)
- \`-n, --dry-run\`: Preview actions without writing
- \`-f, --force\`: Overwrite existing files
- \`-v, --verbose\`: Verbose output
- \`--version\`: Show version information
- \`--platform-info\`: Show platform details

## Python API

### Core Functions

\`\`\`python
def forge(
    schema_path: Path,
    out_dir: Optional[Path] = None,
    dry_run: bool = False,
    force: bool = False,
    verbose: bool = False
) -> Dict[str, Any]
\`\`\`
Compiles a schema file into filesystem structure.

**Returns:**
\`\`\`python
{
    "out_dir": str,           # Output directory path
    "tree": Dict[str, str],   # Generated structure
    "files_created": int,     # Number of files created
    "dirs_created": int,      # Number of directories created  
    "errors": List[str],      # List of error messages
    "success": bool          # Whether operation succeeded
}
\`\`\`

\`\`\`python
def render_template(text: str, vars: Dict[str, str]) -> str
\`\`\`
Renders template variables in text.

\`\`\`python
def parse_simple_schema(text: str, vars: Dict[str, str]) -> List[Tuple[str, Optional[str]]]
\`\`\`
Parses schema text into file/directory plan.

\`\`\`python
def realize(plan: List[Tuple[str, Optional[str]]], out_dir: Path, dry: bool = False, force: bool = False) -> Dict[str, Any]
\`\`\`
Executes filesystem operations from plan.

### Utility Functions

\`\`\`python
def read_text(path: Path) -> str
def write_text(path: Path, content: str) -> None
def stringify_tree(tree: Dict[str, str]) -> str
def validate_schema_file(schema_path: Path) -> bool
def get_file_size(path: Path) -> int
def format_file_size(bytes: int) -> str
\`\`\`

## Schema Syntax

### Basic Elements
- **Comments**: Lines starting with \`#\`
- **Variables**: \`@set NAME=value\`
- **Directories**: Path ending with \`/\`
- **Files**: Path without trailing slash

### Content Types
- **Empty files**: Just the filename
- **Inline content**: \`file -> content\`
- **Heredoc content**: \`file <<TAG\\n...content...\\nTAG\`

### Example Schema
\`\`\`bash
# Project: Example
# Description: Example schema

@set AUTHOR=Developer

/src/
  main.py -> print("Hello ${AUTHOR}")
  config.json <<JSON
  {
    "name": "example",
    "version": "1.0.0"
  }
  JSON
  empty.txt

/docs/
  README.md
\`\`\`
MD

# ==================== TESTS ====================
/tests
  __init__.py

  test_cli.py <<PY
"""Test CLI functionality."""

import subprocess
import sys
from pathlib import Path

def run_cli(*args, cwd=None):
    """Run CLI command and return result."""
    return subprocess.run(
        [sys.executable, "-m", "src.cli", *args],
        capture_output=True, 
        text=True, 
        cwd=cwd
    )

def test_help():
    """Test help command."""
    r = run_cli("--help", cwd=Path(__file__).parent.parent)
    assert r.returncode == 0
    assert "usage" in r.stdout.lower()
    assert "${CLI_NAME}" in r.stdout

def test_version():
    """Test version command."""
    r = run_cli("--version", cwd=Path(__file__).parent.parent)
    assert r.returncode == 0
    assert "${PKG}" in r.stdout
    assert "${FORGE_VERSION}" in r.stdout

def test_platform_info():
    """Test platform info command."""
    r = run_cli("--platform-info", cwd=Path(__file__).parent.parent)
    assert r.returncode == 0
    assert "Platform" in r.stdout

def test_no_schema():
    """Test behavior when no schema is provided."""
    r = run_cli(cwd=Path(__file__).parent.parent)
    assert r.returncode == 2
    assert "usage" in r.stdout.lower()
PY

  test_forge.py <<PY
"""Test forge core functionality."""

import pytest
from pathlib import Path
from src.forge import render_template, parse_simple_schema, realize
from src.utils import stringify_tree, validate_schema_file

def test_render_template():
    """Test template rendering."""
    # Basic variable substitution
    s = render_template("Hello ${NAME}", {"NAME": "World"})
    assert s == "Hello World"
    
    # Unknown variables remain unchanged
    s = render_template("Hello ${UNKNOWN}", {"NAME": "World"})
    assert s == "Hello ${UNKNOWN}"
    
    # Empty template
    s = render_template("", {"NAME": "World"})
    assert s == ""
    
    # None values
    s = render_template("Test ${VAR}", {"VAR": None})
    assert "None" in s

def test_parse_simple_schema_basic():
    """Test basic schema parsing."""
    text = \"\"\"
# Comment line
a.txt -> hi
subdir/
b.txt
\"\"\"
    plan = parse_simple_schema(text, {})
    
    # Should parse all elements
    assert len(plan) == 3
    assert ("a.txt", "hi") in plan
    assert ("subdir/", None) in plan
    assert ("b.txt", "") in plan

def test_parse_simple_schema_heredoc():
    """Test heredoc parsing."""
    text = \"\"\"
config.json <<JSON
{
  "name": "test",
  "value": 42
}
JSON
empty.txt
\"\"\"
    plan = parse_simple_schema(text, {})
    
    assert len(plan) == 2
    assert any("config.json" in path and "name" in content for path, content in plan if content)
    assert any("empty.txt" in path and content == "" for path, content in plan)

def test_parse_simple_schema_with_vars():
    """Test schema parsing with variables."""
    text = \"\"\"
@set NAME=TestUser
file.txt -> Hello ${NAME}
\"\"\"
    vars = {"NAME": "TestUser"}
    plan = parse_simple_schema(text, vars)
    
    assert len(plan) == 1
    path, content = plan[0]
    assert path == "file.txt"
    assert content == "Hello TestUser"

def test_realize_dry_run(tmp_path):
    """Test dry run realization."""
    plan = [
        ("test_dir/", None),
        ("test_dir/file.txt", "content"),
    ]
    
    result = realize(plan, tmp_path, dry=True)
    
    # Should not create actual files in dry run
    assert not (tmp_path / "test_dir").exists()
    assert not (tmp_path / "test_dir" / "file.txt").exists()
    assert result["success"] is True

def test_realize_actual_files(tmp_path):
    """Test actual filesystem realization."""
    plan = [
        ("subdir/", None),
        ("subdir/file.txt", "file content"),
        ("empty.txt", ""),
    ]
    
    result = realize(plan, tmp_path, dry=False, force=True)
    
    # Should create actual files
    assert (tmp_path / "subdir").exists()
    assert (tmp_path / "subdir" / "file.txt").exists()
    assert (tmp_path / "empty.txt").exists()
    
    # Verify content
    assert (tmp_path / "subdir" / "file.txt").read_text() == "file content"
    assert (tmp_path / "empty.txt").read_text() == ""
    
    assert result["success"] is True
    assert len(result["files_created"]) == 2
    assert len(result["dirs_created"]) == 1

def test_stringify_tree():
    """Test tree stringification."""
    tree = {
        "src/": "dir",
        "src/main.py": "file", 
        "docs/": "dir",
        "README.md": "file"
    }
    
    result = stringify_tree(tree)
    
    assert "src/" in result
    assert "main.py" in result
    assert "docs/" in result
    assert "README.md" in result
    assert "📁" in result  # dir icon
    assert "📄" in result  # file icon

def test_validate_schema_file(tmp_path):
    """Test schema file validation."""
    # Valid file
    valid_file = tmp_path / "valid.lrc"
    valid_file.write_text("# Test schema")
    
    assert validate_schema_file(valid_file) is True
    
    # Non-existent file
    fake_file = tmp_path / "nonexistent.lrc"
    assert validate_schema_file(fake_file) is False
    
    # Directory instead of file
    assert validate_schema_file(tmp_path) is False
PY

  conftest.py <<PY
"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path

@pytest.fixture
def sample_schema_content():
    """Provide sample schema content for testing."""
    return \"\"\"
# Test Schema
# Description: For testing purposes

@set TEST_VAR=test_value

/src/
  main.py -> print("Hello ${TEST_VAR}")
  utils/
    helper.py

/docs/
  README.md <<MD
# Test Project
This is a test.
MD
\"\"\"

@pytest.fixture
def temp_schema_file(tmp_path, sample_schema_content):
    """Create a temporary schema file for testing."""
    schema_file = tmp_path / "test_schema.lrc"
    schema_file.write_text(sample_schema_content)
    return schema_file
PY

# ==================== SCRIPTS ====================
/scripts
  pre_build.sh <<SH
#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Pre-build hook: verifying environment..."
echo "Python version:"
python3 --version || echo "Python not found!"

echo "Current directory:"
pwd

echo "Environment check complete."
SH
  @chmod scripts/pre_build.sh +x

  post_build.sh <<SH
#!/usr/bin/env bash
set -euo pipefail

echo "✨ Post-build hook: summarizing artifacts..."
echo "Generated files:"
find . -maxdepth 3 -type f -name "*.py" -o -name "*.md" -o -name "*.txt" -o -name "*.sh" | sort

echo "Directory structure:"
find . -maxdepth 3 -type d | sort

echo "Build summary complete."
SH
  @chmod scripts/post_build.sh +x

  install-dev.sh <<SH
#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Setting up ${PKG} development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install package in development mode
echo "Installing ${PKG} in development mode..."
pip install -e .

# Install development dependencies
echo "Installing development dependencies..."
pip install pytest pytest-cov mypy black build

echo "✅ Development environment ready!"
echo ""
echo "💡 Next steps:"
echo "   source .venv/bin/activate"
echo "   ${CLI_NAME} --help"
echo "   ./scripts/test.sh"
SH
  @chmod scripts/install-dev.sh +x

  test.sh <<SH
#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Running tests for ${PKG}..."

# Run tests with coverage
echo "Running pytest with coverage..."
python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Type checking
echo ""
echo "📝 Running type checks..."
python -m mypy src/ tests/ || echo "Type checking completed with warnings"

# Code formatting check
echo ""
echo "🎨 Checking code formatting..."
python -m black --check src/ tests/ || echo "Format check completed"

echo ""
echo "✅ Test suite completed!"
SH
  @chmod scripts/test.sh +x

  build.sh <<SH
#!/usr/bin/env bash
set -euo pipefail

echo "🔨 Building ${PKG}..."

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info

# Run pre-build hook
if [ -f "scripts/pre_build.sh" ]; then
    ./scripts/pre_build.sh
fi

# Build package
echo "Building package..."
python -m build

# Run post-build hook  
if [ -f "scripts/post_build.sh" ]; then
    ./scripts/post_build.sh
fi

echo "✅ Build complete! Distribution files in dist/"
echo ""
echo "📦 Generated packages:"
ls -la dist/
SH
  @chmod scripts/build.sh +x

# ==================== ASSETS ====================
/assets
  logo.svg <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect width="128" height="128" fill="#0b132b" rx="8"/>
  <path d="M20 100 L64 20 L108 100 Z" fill="#5bc0be" stroke="#3a506b" stroke-width="2"/>
  <circle cx="64" cy="64" r="10" fill="#ffffff"/>
  <circle cx="64" cy="64" r="6" fill="#5bc0be"/>
  <text x="64" y="118" text-anchor="middle" fill="#eeeeee" font-family="Arial, sans-serif" font-size="12" font-weight="bold">FORGEKIT</text>
</svg>
SVG

  banner.txt <<TXT
╔══════════════════════════════════════════════════════════════╗
║                     F O R G E K I T                          ║
║         Portable Developer Forge Toolkit v${FORGE_VERSION}         ║
║                 "Everything you build builds you."           ║
╚══════════════════════════════════════════════════════════════╝
TXT

# ==================== EXAMPLES ====================
/examples
  quickstart.lrc <<LRC
# Quickstart Example
# Description: Minimal example to test ForgeKit

@set PROJECT_NAME=QuickstartProject
@set AUTHOR=ForgeKitUser

/output/
  README.md -> # ${PROJECT_NAME}
  Welcome to ${PROJECT_NAME} by ${AUTHOR}

  main.py <<PY
#!/usr/bin/env python3
print("Hello from ${PROJECT_NAME}!")
print("Created by ${AUTHOR}")
PY

  config/
    settings.json <<JSON
{
  "project": "${PROJECT_NAME}",
  "author": "${AUTHOR}",
  "generated_by": "ForgeKit"
}
JSON
LRC

  demo_project.lrc <<LRC
# Demo Project
# Description: Comprehensive example showing all features

@set PROJECT=DemoProject
@set VERSION=1.0.0
@set AUTHOR=ForgeKit Demo

/demo/
  /src/
    __init__.py
    main.py -> print("Hello from ${PROJECT} v${VERSION}")
    
    /utils/
      helpers.py <<PY
"""Utility functions for ${PROJECT}."""

def greet(name):
    return f"Hello, {name}!"

def calculate(a, b):
    return a + b
PY

  /docs/
    README.md <<MD
# ${PROJECT}

Welcome to ${PROJECT} version ${VERSION}.

## Features
- Generated by ForgeKit
- Complete project structure
- Example source code

## Author
${AUTHOR}
MD

    API.md -> # API Documentation

  /tests/
    test_main.py
    test_utils.py

  .gitignore -> __pycache__/
  requirements.txt
  setup.cfg
LRC

# ==================== BINARIES ====================
/bin
  # Reserved for compiled helpers or shims
  placeholder.txt -> This directory is reserved for binary helpers and shims.

# ==================== PROJECT FILES ====================
.gitignore <<GIT
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environment
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Testing
.coverage
.pytest_cache/
.mypy_cache/
htmlcov/

# ForgeKit output
*_output/
generated_*/

# Logs
*.log
logs/
GIT

LICENSE <<TXT
${LICENSE} License

Copyright (c) ${YEAR} ${AUTHOR}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
TXT

pyproject.toml <<TOML
[project]
name = "${PKG}"
version = "${FORGE_VERSION}"
description = "${DESC}"
readme = "README.md"
requires-python = ">=${PYTHON_VERSION}"
authors = [
    { name = "${AUTHOR}", email = "${EMAIL}" }
]
keywords = ["scaffolding", "generator", "forge", "schema", "lrc", "cli"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Code Generators",
    "Topic :: Software Development :: Build Tools",
]

dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
    "black>=23.0.0",
    "build>=0.10.0",
]

docs = [
    "mkdocs>=1.4.0",
    "mkdocs-material>=9.0.0",
]

[project.urls]
Homepage = "${PROJECT_URL}"
Repository = "${PROJECT_URL}"
Documentation = "${PROJECT_URL}#readme"
"Bug Reports" = "${PROJECT_URL}/issues"
"Changelog" = "${PROJECT_URL}/blob/main/CHANGELOG.md"

[project.scripts]
${CLI_NAME} = "src.cli:main"

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py38']
include = '\\.pyi?$'

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "--verbose --strict-markers --strict-config"
testpaths = ["tests"]
pythonpath = ["src"]
TOML

README.md <<MD
# ${PKG} — Generated by LRC

> *${SECRET_MSG}*

This repository was generated from a single schema using **LRC (Local Repo Compile)**.

## 🚀 Quick Start

\`\`\`bash
# Setup development environment
./scripts/install-dev.sh

# Run tests
./scripts/test.sh

# Build package
./scripts/build.sh

# Use the CLI
${CLI_NAME} --help
\`\`\`

## 📖 Documentation

See the [docs/](./docs/) directory for comprehensive documentation:

- [README.md](./docs/README.md) - Main documentation
- [API Reference](./docs/API_REFERENCE.md) - API documentation  
- [Easter Egg](./docs/EASTER_EGG.md) - Hidden message and philosophy

## 🧪 Examples

Check out the [examples/](./examples/) directory for sample schemas:

- [quickstart.lrc](./examples/quickstart.lrc) - Minimal example
- [demo_project.lrc](./examples/demo_project.lrc) - Comprehensive example

## 🔧 What is This?

A compact, developer-focused forge that demonstrates:

- **Schema-driven development** - Generate projects from declarative schemas
- **Self-referential design** - The tool that can generate itself
- **Comprehensive tooling** - Tests, docs, scripts, and packaging
- **Cross-platform compatibility** - Works everywhere Python runs

## 📄 License

${LICENSE} License - see [LICENSE](./LICENSE) file for details.

---

*Generated by LRC v0.2.2 — The tool that builds tools.*
MD

CHANGELOG.md <<MD
# Changelog

All notable changes to ${PKG} will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - ${YEAR}-01-01

### Added
- Enhanced CLI with better error handling and validation
- Improved template rendering with regex-based variable substitution
- Comprehensive test suite with pytest fixtures
- Better documentation with API reference and examples
- Utility functions for file operations and tree visualization
- Development scripts for testing, building, and installation
- Example schemas for quickstart and demo projects

### Changed
- Updated to LRC v0.2.2 schema format
- Improved error handling and validation throughout
- Enhanced cross-platform compatibility
- Better code organization and type hints

### Fixed
- Heredoc parsing edge cases
- Variable substitution in nested contexts
- File path handling on different platforms

## [0.1.0] - ${YEAR}-01-01

### Added
- Initial release of ${PKG}
- Basic CLI interface
- Core forge functionality with schema parsing
- Simple template rendering
- Basic project structure generation
- Minimal test suite
- Documentation and examples

---

*Generated by LRC — Local Repo Compile*
MD

# ==================== SECURITY & MANIFEST (DEMO) ====================
SECURITY.md <<MD
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities to ${EMAIL}.

This is a code generation tool. While it doesn't handle sensitive data by default, 
please exercise caution when:

1. Generating code with user-provided templates
2. Using the tool in automated build pipelines
3. Processing schemas from untrusted sources

## Best Practices

- Validate schema files before processing
- Use dry-run mode to preview changes
- Review generated code before execution
- Keep the tool updated to the latest version
MD

# ==================== FOOTER ====================
.lrc_manifest.json <<JSON
{
  "project": "${PKG}",
  "version": "${FORGE_VERSION}",
  "generator": "LRC",
  "generator_version": "0.2.2",
  "schema_version": "1.1",
  "author": "${AUTHOR}",
  "timestamp": "${YEAR}-01-01T00:00:00Z",
  "files_generated": 28,
  "directories_created": 12,
  "secret_message": "${SECRET_MSG}",
  "compatibility": {
    "python": ">=3.8",
    "platforms": ["linux", "macos", "windows", "wsl2", "android-termux"]
  }
}
JSON

@footer <<TXT
✅ Project '${PKG}' built successfully!
📁 Output: ./${PKG}_output/
📦 Version: ${FORGE_VERSION}
🧠 Generated by LRC v0.2.2 — Local Repo Compile
💬 Secret: "${SECRET_MSG}"
🚀 Ready to forge your own creations!
TXT


FILE: examples/schema_dev_example.lrc
Kind: text
Size: 14740
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# examples/schema_dev_example.lrc
# Solo Developer Project Template
# Project: my-dev-project
# Description: Lightweight, focused project template for solo developers
# Version: 1.0.0
# Schema-Version: 1.1
# Generator: LRC v0.2.2
# Focus: Productivity, minimal setup, rapid development

# ==================== SOLO DEVELOPER VARIABLES ====================
@set AUTHOR=Developer Name
@set EMAIL=developer@example.com
@set PROJECT_NAME=my-dev-project
@set DESCRIPTION=A focused project for solo development
@set YEAR=2025
@set LICENSE=MIT
@set PYTHON_VERSION=3.9
@set DEV_ENV=local
@set CODE_STYLE=black

# ==================== MINIMAL IGNORE PATTERNS ====================
@ignore __pycache__ .venv .DS_Store *.tmp

# ==================== QUICK START TEMPLATE ====================
@template python-cli

# ==================== LEAN PROJECT STRUCTURE ====================
/src
/tests
/scripts
/docs

# ==================== FOCUSED SOURCE CODE ====================
/src
  __init__.py -> """${PROJECT_NAME} - ${DESCRIPTION}"""
  
  main.py <<PY
#!/usr/bin/env python3
"""
${PROJECT_NAME} - Solo Developer Project

A clean, minimal codebase for rapid development.
"""

import click

@click.group()
def cli():
    """${PROJECT_NAME} - Developer CLI"""
    pass

@cli.command()
def dev():
    """Start development mode"""
    print("🚀 Development mode started!")
    print(f"Working on: {PROJECT_NAME}")
    print("Happy coding! 🎯")

@cli.command()
def test():
    """Run quick tests"""
    print("🧪 Running tests...")
    # Add your test logic here

@cli.command()
def deploy():
    """Quick deployment"""
    print("📦 Deploying...")
    # Add deployment logic here

if __name__ == "__main__":
    cli()
PY
  @chmod src/main.py +x

  utils.py <<PY
"""Utility functions for ${PROJECT_NAME}"""

import os
from pathlib import Path

def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent

def setup_development_env():
    """Setup development environment"""
    root = get_project_root()
    (root / "data").mkdir(exist_ok=True)
    (root / "logs").mkdir(exist_ok=True)
    print("✅ Development environment ready")

def quick_debug(data):
    """Quick debugging utility"""
    print(f"🔍 DEBUG: {type(data)} - {data}")
PY

  config.py <<PY
"""Simple configuration for solo development"""

import os
from typing import Dict, Any

class DevConfig:
    """Development configuration"""
    
    # Development settings
    DEBUG = True
    TESTING = False
    
    # Project settings
    PROJECT_NAME = "${PROJECT_NAME}"
    VERSION = "1.0.0"
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    
    @classmethod
    def get_settings(cls) -> Dict[str, Any]:
        """Get all settings as dict"""
        return {k: v for k, v in cls.__dict__.items() 
                if not k.startswith('_') and not callable(v)}
PY

# ==================== ESSENTIAL TESTING ====================
/tests
  __init__.py
  
  test_basics.py <<PY
"""Essential tests for solo development"""

from src.main import cli
from src.utils import get_project_root, setup_development_env
from click.testing import CliRunner

def test_cli_commands():
    """Test basic CLI functionality"""
    runner = CliRunner()
    
    # Test dev command
    result = runner.invoke(cli, ['dev'])
    assert result.exit_code == 0
    assert "Development mode" in result.output
    
    # Test help
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0

def test_utils():
    """Test utility functions"""
    root = get_project_root()
    assert root.exists()
    assert root.name == "${PROJECT_NAME}"
PY

  test_config.py <<PY
"""Test configuration"""

from src.config import DevConfig

def test_config_settings():
    """Test configuration settings"""
    settings = DevConfig.get_settings()
    
    assert settings['DEBUG'] is True
    assert settings['PROJECT_NAME'] == "${PROJECT_NAME}"
    assert 'BASE_DIR' in settings
PY

# ==================== PRODUCTIVITY SCRIPTS ====================
/scripts
  dev.sh <<SH
#!/usr/bin/env bash
# Solo Developer Productivity Script

echo "🎯 ${PROJECT_NAME} - Developer Setup"
echo "======================================"

# Quick environment check
echo "🔍 Environment Check:"
python --version || echo "⚠️  Python not found"
git --version || echo "⚠️  Git not found"

# Setup virtual environment if needed
if [ ! -d ".venv" ]; then
    echo "🐍 Creating virtual environment..."
    python -m venv .venv
fi

echo "🔧 Activating environment..."
source .venv/bin/activate

echo "📦 Installing dependencies..."
pip install -e .

echo "✅ Ready to code!"
echo ""
echo "💡 Quick Commands:"
echo "   ${PROJECT_NAME} dev     # Start development"
echo "   ${PROJECT_NAME} test    # Run tests"
echo "   ${PROJECT_NAME} deploy  # Quick deploy"
echo "   ./scripts/code.sh       # Code quality"
SH
  @chmod scripts/dev.sh +x

  code.sh <<SH
#!/usr/bin/env bash
# Solo Developer Code Quality Script

echo "🎨 Code Quality Check"
echo "====================="

# Format code
echo "📝 Formatting code..."
python -m black src/ tests/

# Quick lint
echo "🔍 Basic linting..."
python -m flake8 src/ --max-complexity=10

# Type checking (optional)
echo "📋 Type checking..."
python -m mypy src/ --ignore-missing-imports || echo "⚠️  Type checking skipped"

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

echo "✅ Code quality check complete!"
SH
  @chmod scripts/code.sh +x

  deploy.sh <<SH
#!/usr/bin/env bash
# Solo Developer Deployment Script

echo "🚀 Quick Deployment"
echo "==================="

ENVIRONMENT=${1:-staging}

echo "Deploying to: $ENVIRONMENT"

# Run tests first
echo "🧪 Pre-deployment check..."
python -m pytest tests/ -x

# Simple deployment logic
case $ENVIRONMENT in
    staging)
        echo "📦 Deploying to staging..."
        # Add your staging deployment commands
        ;;
    production)
        echo "🎯 Deploying to production..."
        # Add your production deployment commands
        ;;
    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

echo "✅ Deployment to $ENVIRONMENT completed!"
SH
  @chmod scripts/deploy.sh +x

# ==================== MINIMAL DOCUMENTATION ====================
/docs
  README.md <<MD
# ${PROJECT_NAME}

> **Solo Developer Edition**

${DESCRIPTION}

## 🎯 Quick Start

\`\`\`bash
# Generate project
lrc schema_dev_example.lrc -o ./${PROJECT_NAME}
cd ${PROJECT_NAME}

# Setup and run
./scripts/dev.sh
${PROJECT_NAME} dev
\`\`\`

## 🚀 Developer Workflow

### Daily Development
\`\`\`bash
# Start coding session
${PROJECT_NAME} dev

# Run code quality checks
./scripts/code.sh

# Quick deployment
./scripts/deploy.sh staging
\`\`\`

### Project Structure
\`\`\`
${PROJECT_NAME}/
├── src/           # Source code
│   ├── main.py    # CLI entry point
│   ├── utils.py   # Developer utilities
│   └── config.py  # Simple configuration
├── tests/         # Essential tests
├── scripts/       # Productivity scripts
└── docs/          # Minimal documentation
\`\`\`

## 🔧 Core Features

- **Click CLI** for easy command management
- **Simple configuration** without complexity
- **Developer utilities** for common tasks
- **Essential testing** that matters
- **Productivity scripts** for daily workflow

## 🛠️ Customization

Edit these files to match your needs:
- \`src/main.py\` - Add your CLI commands
- \`src/utils.py\` - Add your helper functions
- \`src/config.py\` - Configure your settings
- \`scripts/\` - Modify deployment and quality scripts

## 📦 Deployment

### Staging
\`\`\`bash
./scripts/deploy.sh staging
\`\`\`

### Production
\`\`\`bash
./scripts/deploy.sh production
\`\`\`

## 🎪 Solo Developer Tips

1. **Keep it simple** - Focus on what matters
2. **Automate repetitive tasks** - Use the scripts
3. **Test the important stuff** - Don't over-test
4. **Document as you go** - But don't over-document
5. **Deploy often** - Small, frequent deployments

## 📄 License

${LICENSE} License - see [LICENSE](../LICENSE) for details.

---

*Built for developers who ship 🚀*
MD

  DEV_TIPS.md <<MD
# Solo Developer Tips

## 🎯 Productivity Workflow

### Morning Setup
\`\`\`bash
./scripts/dev.sh
${PROJECT_NAME} dev
\`\`\`

### Before Commits
\`\`\`bash
./scripts/code.sh
\`\`\`

### End of Day
\`\`\`bash
./scripts/deploy.sh staging
git add .
git commit -m "feat: daily progress"
git push
\`\`\`

## 🔧 Useful Commands

### Development
\`\`\`bash
# Start development session
${PROJECT_NAME} dev

# Run specific tests
python -m pytest tests/test_basics.py -v

# Debug a function
python -c "from src.utils import quick_debug; quick_debug('test')"
\`\`\`

### Project Management
\`\`\`bash
# Check project health
python -c "from src.config import DevConfig; print(DevConfig.get_settings())"

# Setup development environment
python -c "from src.utils import setup_development_env; setup_development_env()"
\`\`\`

## 🚀 Quick Customization

### Add New CLI Command
\`\`\`python
@cli.command()
def new_feature():
    \"\"\"Describe your new feature\"\"\"
    print("Implement your feature here")
\`\`\`

### Add Utility Function
\`\`\`python
def your_helper_function():
    \"\"\"Add your helper function here\"\"\"
    return "your logic"
\`\`\`
MD

# ==================== PROJECT CONFIGURATION ====================
.gitignore <<GIT
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environment
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Development
data/
logs/
*.log
GIT

LICENSE <<TXT
${LICENSE} License

Copyright (c) ${YEAR} ${AUTHOR}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
TXT

pyproject.toml <<TOML
[project]
name = "${PROJECT_NAME}"
version = "1.0.0"
description = "${DESCRIPTION}"
readme = "README.md"
requires-python = ">=${PYTHON_VERSION}"
authors = [
    { name = "${AUTHOR}", email = "${EMAIL}" }
]
keywords = ["developer", "productivity", "cli", "tools"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "click>=8.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
]

[project.scripts]
${PROJECT_NAME} = "src.main:cli"

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py39']

[tool.mypy]
python_version = "3.9"
warn_return_any = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
addopts = "--verbose"
TOML

# ==================== QUICK START GUIDE ====================
QUICKSTART.md <<MD
# 🚀 Quick Start Guide

## 1. Generate Project
\`\`\`bash
lrc schema_dev_example.lrc -o ./my-project
cd my-project
\`\`\`

## 2. First-Time Setup
\`\`\`bash
./scripts/dev.sh
\`\`\`

## 3. Start Developing
\`\`\`bash
${PROJECT_NAME} dev
\`\`\`

## 4. Daily Workflow
\`\`\`bash
# Make changes to src/
./scripts/code.sh
./scripts/deploy.sh staging
\`\`\`

## 🎯 What You Get

✅ **Clean project structure**  
✅ **CLI with useful commands**  
✅ **Productivity scripts**  
✅ **Essential testing**  
✅ **Minimal documentation**  
✅ **Deployment ready**  

## 🔧 First Customizations

1. Edit \`src/main.py\` - Add your CLI commands
2. Edit \`src/utils.py\` - Add helper functions  
3. Edit \`src/config.py\` - Configure settings
4. Run \`./scripts/code.sh\` to format

## 🚀 Ship It!

When ready to deploy:
\`\`\`bash
./scripts/deploy.sh production
\`\`\`

---

*Happy coding! Remember: Ship often, iterate fast 🚀*
MD

README.md <<MD
# ${PROJECT_NAME}

${DESCRIPTION}

## 🎯 For Solo Developers

This template is optimized for individual developers who want to:
- **Start fast** with minimal setup
- **Stay focused** with clean structure  
- **Ship quickly** with productivity tools
- **Iterate rapidly** with essential testing

## ⚡ Ultra-Quick Start

\`\`\`bash
# Generate and run
lrc schema_dev_example.lrc -o ./${PROJECT_NAME}
cd ${PROJECT_NAME}
./scripts/dev.sh
${PROJECT_NAME} dev
\`\`\`

## 📁 Lean Structure

\`\`\`
${PROJECT_NAME}/
├── src/           # Your code here
├── tests/         # Tests that matter
├── scripts/       # Productivity tools
└── docs/          # Just enough docs
\`\`\`

## 🔧 Built For Productivity

- **Click CLI** - Easy command management
- **Utility functions** - Common dev tasks
- **Quality scripts** - Code formatting & checks
- **Deployment scripts** - Staging & production

## 🚀 Next Steps

1. Read \`QUICKSTART.md\` for immediate setup
2. Check \`DEV_TIPS.md\` for workflow advice
3. Customize the code in \`src/\`
4. Start shipping!

## 📄 License

${LICENSE} - See [LICENSE](LICENSE) for details.

---

*Built for developers who actually ship code 🎯*
MD

# ==================== END OF SOLO DEVELOPER SCHEMA ====================
# This schema is optimized for solo developers who want to ship fast
# Generate with: lrc schema_dev_example.lrc -o ./my-project
# Start coding immediately with: ./scripts/dev.sh

# Focus on what matters: writing code and shipping features! 🚀


FILE: examples/schema_entprse_example.lrc
Kind: text
Size: 68518
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# examples/schema_entprse_example.lrc
# Enterprise-Ready Project Template
# Project: enterprise-project-template
# Description: Enterprise-grade project template with comprehensive tooling, security, and DevOps practices
# Version: 2.0.0
# Schema-Version: 1.1
# Generator: LRC v0.2.2
# Compatible-With: Python 3.8+

# ==================== ENTERPRISE METADATA & VARIABLES ====================
# Core project metadata
@set AUTHOR=Enterprise Development Team
@set EMAIL=devops@company.com
@set PROJECT_NAME=enterprise-project-template
@set DESCRIPTION=Enterprise-grade project template with comprehensive tooling, security, and DevOps practices
@set YEAR=2025
@set LICENSE=Apache-2.0
@set PYTHON_VERSION=3.8
@set PROJECT_URL=https://github.com/company/enterprise-project-template
@set SUPPORT_EMAIL=support@company.com
@set TEAM_NAME=Platform Engineering

# Security & Compliance
@set SECURITY_CONTACT=security@company.com
@set COMPLIANCE_FRAMEWORK=SOC2
@set DATA_CLASSIFICATION=Internal

# Deployment & Infrastructure
@set DOCKER_NAMESPACE=company
@set K8S_NAMESPACE=platform
@set ENVIRONMENT=development
@set REGION=us-east-1

# ==================== ENTERPRISE IGNORE PATTERNS ====================
# Comprehensive ignore patterns for enterprise environments
@ignore node_modules .venv __pycache__ .DS_Store *.tmp build dist *.egg-info .mypy_cache .pytest_cache
@ignore .coverage htmlcov .benchmarks .vscode .idea *.swp *.swo
@ignore local_settings.py *.local.* .env.local secrets.txt
@ignore *.log logs/ audit/ backups/ temp/ tmp/
@ignore .terraform terraform.tfstate* *.tfvars
@ignore docker-compose.override.yml

# ==================== ENTERPRISE TEMPLATES ====================
# Apply enterprise-ready template with enhanced structure
@template python-cli

# ==================== ENTERPRISE PROJECT STRUCTURE ====================
# Comprehensive enterprise directory structure
/src
/docs
/tests
/scripts
/assets
/examples
/config
/deploy
/helm
/terraform
/docker
/monitoring
/security
/compliance
/.github

# ==================== SOURCE CODE (ENTERPRISE GRADE) ====================
/src
  # Package initialization with enterprise metadata
  __init__.py <<PY
"""${PROJECT_NAME} - ${DESCRIPTION}

Enterprise-Grade Python Package

Features:
- Comprehensive type hints
- Async/await support
- Structured logging
- Configuration management
- Security best practices
- Monitoring integration
"""

__version__ = "2.0.0"
__author__ = "${AUTHOR}"
__email__ = "${SUPPORT_EMAIL}"
__team__ = "${TEAM_NAME}"

import logging
from typing import Optional

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from .cli import main
from .core import EnterpriseService, ConfigManager
from .utils import security, monitoring, validation
from .api import routes, middleware, handlers

__all__ = [
    "main",
    "EnterpriseService",
    "ConfigManager", 
    "security",
    "monitoring",
    "validation",
    "routes",
    "middleware",
    "handlers",
    "logger"
]
PY

  # Enterprise CLI with comprehensive options
  cli.py <<PY
#!/usr/bin/env python3
"""${PROJECT_NAME} - Enterprise CLI Interface"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from .__init__ import __version__, logger
from .core import EnterpriseService, ConfigManager
from .utils.monitoring import MetricsCollector

class EnterpriseCLI:
    \"\"\"Enterprise-grade CLI with comprehensive features.\"\"\"

    def __init__(self):
        self.parser = self._create_parser()
        self.metrics = MetricsCollector()

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="${PROJECT_NAME}",
            description="${DESCRIPTION}",
            epilog=f"Support: {SUPPORT_EMAIL} | Team: {TEAM_NAME}"
        )

        # Core commands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Start command
        start_parser = subparsers.add_parser("start", help="Start the service")
        start_parser.add_argument("--config", "-c", default="config/production.yaml", 
                                help="Configuration file path")
        start_parser.add_argument("--port", "-p", type=int, default=8000,
                                help="Service port")
        start_parser.add_argument("--workers", "-w", type=int, default=4,
                                help="Number of worker processes")

        # Test command
        test_parser = subparsers.add_parser("test", help="Run test suite")
        test_parser.add_argument("--coverage", action="store_true",
                               help="Generate coverage report")
        test_parser.add_argument("--verbose", "-v", action="store_true",
                               help="Verbose output")

        # Security scan command
        security_parser = subparsers.add_parser("security", help="Security scanning")
        security_parser.add_argument("--scan-type", choices=["sast", "dast", "dependency"],
                                   default="sast", help="Type of security scan")

        # Common arguments
        parser.add_argument("--version", action="version", 
                          version=f"%(prog)s {__version__}")
        parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                          default="INFO", help="Logging level")
        parser.add_argument("--environment", "-e", 
                          choices=["development", "staging", "production"],
                          default="development", help="Runtime environment")

        return parser

    async def run(self, args: Optional[list] = None) -> int:
        \"\"\"Execute CLI command.\"\"\"
        parsed_args = self.parser.parse_args(args)

        # Configure logging
        logging.getLogger().setLevel(getattr(logging, parsed_args.log_level))

        try:
            if parsed_args.command == "start":
                return await self._handle_start(parsed_args)
            elif parsed_args.command == "test":
                return self._handle_test(parsed_args)
            elif parsed_args.command == "security":
                return await self._handle_security(parsed_args)
            else:
                self.parser.print_help()
                return 0

        except Exception as e:
            logger.error(f"Command failed: {e}", exc_info=True)
            return 1

    async def _handle_start(self, args) -> int:
        \"\"\"Handle service startup.\"\"\"
        logger.info(f"Starting {PROJECT_NAME} v{__version__}")
        logger.info(f"Environment: {args.environment}")
        logger.info(f"Config: {args.config}")

        config = ConfigManager.load(args.config)
        service = EnterpriseService(config)
        
        await self.metrics.increment("service.start")
        await service.start()
        return 0

    def _handle_test(self, args) -> int:
        \"\"\"Handle test execution.\"\"\"
        import subprocess
        import sys

        test_cmd = [sys.executable, "-m", "pytest", "tests/"]
        if args.verbose:
            test_cmd.append("-v")
        if args.coverage:
            test_cmd.extend(["--cov=src", "--cov-report=html"])

        result = subprocess.run(test_cmd)
        return result.returncode

    async def _handle_security(self, args) -> int:
        \"\"\"Handle security scanning.\"\"\"
        from .utils.security import SecurityScanner
        
        scanner = SecurityScanner()
        report = await scanner.scan(args.scan_type)
        
        if report.vulnerabilities:
            logger.warning(f"Found {len(report.vulnerabilities)} vulnerabilities")
            return 1
        else:
            logger.info("Security scan passed")
            return 0

def main():
    \"\"\"CLI entry point.\"\"\"
    cli = EnterpriseCLI()
    return asyncio.run(cli.run())

if __name__ == "__main__":
    sys.exit(main())
PY
  @chmod src/cli.py +x

  # Core enterprise service
  core.py <<PY
\"\"\"Enterprise core service with advanced features.\"\"\"

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path

from .utils.monitoring import MetricsCollector
from .utils.security import SecurityManager

@dataclass
class ServiceConfig:
    \"\"\"Enterprise service configuration.\"\"\"
    name: str
    version: str
    environment: str
    port: int = 8000
    workers: int = 4
    debug: bool = False
    features: Dict[str, bool] = None

    def __post_init__(self):
        if self.features is None:
            self.features = {
                "monitoring": True,
                "security": True,
                "caching": True,
                "rate_limiting": True
            }

class ConfigManager:
    \"\"\"Enterprise configuration management.\"\"\"

    @staticmethod
    def load(config_path: Path) -> ServiceConfig:
        \"\"\"Load configuration from YAML file.\"\"\"
        # Implementation would load from YAML/JSON/Env
        return ServiceConfig(
            name="${PROJECT_NAME}",
            version="2.0.0",
            environment="${ENVIRONMENT}",
            port=8000,
            workers=4
        )

class EnterpriseService:
    \"\"\"Main enterprise service class.\"\"\"

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.metrics = MetricsCollector()
        self.security = SecurityManager()
        self.is_running = False

    async def start(self):
        \"\"\"Start the enterprise service.\"\"\"
        self.logger.info(f"Starting {self.config.name} v{self.config.version}")
        
        # Initialize components
        await self._initialize_components()
        
        self.is_running = True
        self.logger.info("Service started successfully")
        
        # Keep service running
        while self.is_running:
            await asyncio.sleep(1)

    async def stop(self):
        \"\"\"Stop the enterprise service gracefully.\"\"\"
        self.logger.info("Stopping service...")
        self.is_running = False
        await self._cleanup_components()
        self.logger.info("Service stopped")

    async def _initialize_components(self):
        \"\"\"Initialize all service components.\"\"\"
        if self.config.features.get("monitoring"):
            await self.metrics.start()
            
        if self.config.features.get("security"):
            await self.security.initialize()

    async def _cleanup_components(self):
        \"\"\"Cleanup service components.\"\"\"
        if self.config.features.get("monitoring"):
            await self.metrics.stop()

    async def health_check(self) -> Dict[str, Any]:
        \"\"\"Perform comprehensive health check.\"\"\"
        return {
            "status": "healthy" if self.is_running else "unhealthy",
            "version": self.config.version,
            "environment": self.config.environment,
            "components": {
                "monitoring": await self.metrics.is_healthy(),
                "security": await self.security.is_healthy()
            }
        }
PY

  # API layer
  api/__init__.py
  api/routes.py <<PY
\"\"\"Enterprise API routes with security and monitoring.\"\"\"

from typing import Dict, Any
import logging
from fastapi import APIRouter, Depends, HTTPException, Request

from ..utils.security import require_auth, rate_limit
from ..utils.monitoring import track_metrics

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
@track_metrics("health_check")
async def health_check(request: Request) -> Dict[str, Any]:
    \"\"\"Comprehensive health check endpoint.\"\"\"
    return {
        "status": "healthy",
        "service": "${PROJECT_NAME}",
        "version": "2.0.0",
        "environment": "${ENVIRONMENT}"
    }

@router.get("/metrics")
@require_auth
async def get_metrics(request: Request) -> Dict[str, Any]:
    \"\"\"Metrics endpoint (authenticated).\"\"\"
    # Return service metrics
    return {"metrics": "collected_data"}

@router.post("/data")
@require_auth
@rate_limit(requests=100, window=60)
async def process_data(request: Request, data: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"Process data with authentication and rate limiting.\"\"\"
    logger.info(f"Processing data: {data.get('type', 'unknown')}")
    return {"status": "processed", "id": "12345"}
PY

  api/middleware.py <<PY
\"\"\"Enterprise API middleware.\"\"\"

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    \"\"\"Add security headers to all responses.\"\"\"
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    \"\"\"Log all requests and responses.\"\"\"
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Duration: {process_time:.3f}s"
        )
        
        return response
PY

  # Utility modules
  utils/__init__.py
  utils/security.py <<PY
\"\"\"Enterprise security utilities.\"\"\"

import hashlib
import hmac
import secrets
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    \"\"\"Comprehensive security management.\"\"\"
    
    def __init__(self):
        self.secret_key = secrets.token_urlsafe(32)
        
    async def initialize(self):
        \"\"\"Initialize security components.\"\"\"
        logger.info("Security manager initialized")
        
    async def is_healthy(self) -> bool:
        \"\"\"Check security subsystem health.\"\"\"
        return True
        
    def generate_token(self, data: Dict[str, Any]) -> str:
        \"\"\"Generate secure token.\"\"\"
        message = str(data).encode()
        return hmac.new(
            self.secret_key.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        
    def verify_token(self, token: str, data: Dict[str, Any]) -> bool:
        \"\"\"Verify token validity.\"\"\"
        expected = self.generate_token(data)
        return hmac.compare_digest(token, expected)

class SecurityScanner:
    \"\"\"Security vulnerability scanner.\"\"\"
    
    async def scan(self, scan_type: str) -> 'SecurityReport':
        \"\"\"Perform security scan.\"\"\"
        logger.info(f"Performing {scan_type} security scan")
        return SecurityReport(scan_type)

class SecurityReport:
    \"\"\"Security scan report.\"\"\"
    
    def __init__(self, scan_type: str):
        self.scan_type = scan_type
        self.vulnerabilities = []
        
    def add_vulnerability(self, severity: str, description: str):
        \"\"\"Add vulnerability to report.\"\"\"
        self.vulnerabilities.append({
            "severity": severity,
            "description": description
        })

# Security decorators
def require_auth(func):
    \"\"\"Decorator to require authentication.\"\"\"
    async def wrapper(*args, **kwargs):
        # Authentication logic would go here
        return await func(*args, **kwargs)
    return wrapper

def rate_limit(requests: int, window: int):
    \"\"\"Decorator for rate limiting.\"\"\"
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Rate limiting logic would go here
            return await func(*args, **kwargs)
        return wrapper
    return decorator
PY

  utils/monitoring.py <<PY
\"\"\"Enterprise monitoring and metrics utilities.\"\"\"

import time
from typing import Dict, Any
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class MetricsCollector:
    \"\"\"Collect and manage application metrics.\"\"\"
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.is_collecting = False
        
    async def start(self):
        \"\"\"Start metrics collection.\"\"\"
        self.is_collecting = True
        logger.info("Metrics collection started")
        
    async def stop(self):
        \"\"\"Stop metrics collection.\"\"\"
        self.is_collecting = False
        logger.info("Metrics collection stopped")
        
    async def increment(self, metric: str, value: int = 1):
        \"\"\"Increment a counter metric.\"\"\"
        if self.is_collecting:
            self.metrics[metric] = self.metrics.get(metric, 0) + value
            
    async def is_healthy(self) -> bool:
        \"\"\"Check monitoring subsystem health.\"\"\"
        return self.is_collecting

def track_metrics(operation: str):
    \"\"\"Decorator to track operation metrics.\"\"\"
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log metrics
                logger.info(
                    f"Operation {operation} completed in {duration:.3f}s"
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Operation {operation} failed after {duration:.3f}s: {e}"
                )
                raise
        return wrapper
    return decorator
PY

  utils/validation.py <<PY
\"\"\"Enterprise data validation utilities.\"\"\"

from typing import Any, Dict, List, Optional
import re

class DataValidator:
    \"\"\"Comprehensive data validation.\"\"\"
    
    @staticmethod
    def validate_email(email: str) -> bool:
        \"\"\"Validate email format.\"\"\"
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        \"\"\"Validate phone number format.\"\"\"
        pattern = r'^\\+?[1-9]\\d{1,14}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        \"\"\"Validate data against JSON schema.\"\"\"
        # Basic implementation - would use jsonschema in production
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in data:
                return False
        return True
PY

# ==================== ENTERPRISE DOCUMENTATION ====================
/docs
  README.md <<MD
# ${PROJECT_NAME}

${DESCRIPTION}

![License](https://img.shields.io/badge/license-${LICENSE}-blue.svg)
![Python](https://img.shields.io/badge/python-${PYTHON_VERSION}+-green.svg)
![Enterprise](https://img.shields.io/badge/level-Enterprise-orange.svg)

## 🏢 Enterprise Features

- **Security First**: Built-in security scanning, authentication, and compliance
- **Monitoring Ready**: Comprehensive metrics, logging, and health checks
- **DevOps Integration**: Docker, Kubernetes, Terraform, and CI/CD ready
- **Type Safety**: Full type hints and mypy compliance
- **Async Ready**: Full async/await support throughout
- **Configuration Management**: Environment-aware configuration
- **API First**: RESTful API with OpenAPI documentation

## 🚀 Quick Start

### Prerequisites
- Python ${PYTHON_VERSION}+
- Docker & Kubernetes (for deployment)
- Terraform (for infrastructure)

### Development Setup
\`\`\`bash
# Clone and setup
git clone ${PROJECT_URL}
cd ${PROJECT_NAME}

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Install with development dependencies
pip install -e ".[dev]"

# Run security scan
${PROJECT_NAME} security --scan-type sast

# Run tests
${PROJECT_NAME} test --coverage --verbose

# Start development server
${PROJECT_NAME} start --environment development
\`\`\`

### Production Deployment
\`\`\`bash
# Build Docker image
docker build -t ${DOCKER_NAMESPACE}/${PROJECT_NAME} .

# Deploy to Kubernetes
kubectl apply -f deploy/kubernetes/

# Infrastructure provisioning
terraform apply -var environment=production
\`\`\`

## 📁 Project Architecture

\`\`\`
${PROJECT_NAME}/
├── src/                 # Source code
│   ├── api/            # API layer (FastAPI)
│   ├── core/           # Business logic
│   └── utils/          # Utilities (security, monitoring, validation)
├── tests/              # Comprehensive test suite
├── deploy/             # Deployment configurations
│   ├── kubernetes/     # K8s manifests
│   └── docker/         # Docker configurations
├── terraform/          # Infrastructure as Code
├── monitoring/         # Monitoring configurations
├── security/           # Security policies & scans
├── compliance/         # Compliance documentation
└── .github/            # CI/CD workflows
\`\`\`

## 🔧 Configuration

### Environment Variables
\`\`\`bash
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export SECRET_KEY=your-secret-key
export DATABASE_URL=postgresql://user:pass@host/db
\`\`\`

### Configuration Files
- \`config/development.yaml\` - Development settings
- \`config/production.yaml\` - Production settings
- \`config/security.yaml\` - Security configurations

## 🧪 Testing & Quality

\`\`\`bash
# Run full test suite
./scripts/test.sh

# Security scanning
./scripts/security-scan.sh

# Code quality checks
./scripts/quality-check.sh

# Performance benchmarking
./scripts/benchmark.sh
\`\`\`

## 📊 Monitoring & Observability

- **Metrics**: Prometheus endpoints at `/metrics`
- **Logging**: Structured JSON logging
- **Tracing**: Distributed tracing support
- **Health Checks**: Comprehensive health endpoints

## 🔒 Security

### Security Features
- Authentication & Authorization
- Rate Limiting
- Security Headers
- Vulnerability Scanning
- Secret Management
- Compliance Reporting

### Security Commands
\`\`\`bash
# SAST Scan
${PROJECT_NAME} security --scan-type sast

# Dependency Scan
${PROJECT_NAME} security --scan-type dependency

# Generate Security Report
./scripts/security-report.sh
\`\`\`

## 🤝 Contributing

1. Follow [Conventional Commits](https://www.conventionalcommits.org/)
2. Update tests and documentation
3. Run security scans before submitting
4. Ensure all checks pass in CI/CD

## 📞 Support

- **Team**: ${TEAM_NAME}
- **Email**: ${SUPPORT_EMAIL}
- **Security**: ${SECURITY_CONTACT}
- **Documentation**: ${PROJECT_URL}/docs

## 📄 License

${LICENSE} License - See [LICENSE](../LICENSE) for details.

---

*Generated by LRC - Enterprise Template v2.0.0*
MD

  API.md <<MD
# API Documentation

## Base URL
\`https://api.company.com/v1\`

## Authentication
All endpoints require authentication using Bearer tokens.

\`\`\`http
Authorization: Bearer <your-token>
\`\`\`

## Endpoints

### Health Check
\`\`\`http
GET /health
\`\`\`

**Response:**
\`\`\`json
{
  "status": "healthy",
  "service": "${PROJECT_NAME}",
  "version": "2.0.0",
  "environment": "production"
}
\`\`\`

### Metrics
\`\`\`http
GET /metrics
\`\`\`

**Headers:**
\`\`\`http
Authorization: Bearer <token>
\`\`\`

### Process Data
\`\`\`http
POST /data
\`\`\`

**Headers:**
\`\`\`http
Authorization: Bearer <token>
Content-Type: application/json
\`\`\`

**Body:**
\`\`\`json
{
  "type": "user_data",
  "payload": {
    "user_id": "12345",
    "action": "login"
  }
}
\`\`\`

**Rate Limit:** 100 requests per minute

## Error Responses

\`\`\`json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid format"
    }
  }
}
\`\`\`

## SDK Examples

### Python
\`\`\`python
from ${PROJECT_NAME} import EnterpriseClient

client = EnterpriseClient(
    base_url="https://api.company.com/v1",
    api_key="your-api-key"
)

# Health check
health = await client.health()

# Process data
result = await client.process_data({
    "type": "user_data",
    "payload": {"user_id": "12345"}
})
\`\`\`
MD

  SECURITY.md <<MD
# Security Policy

## Supported Versions

| Version | Supported          | Security Updates Until |
| ------- | ------------------ | ---------------------- |
| 2.0.x   | :white_check_mark: | ${YEAR}-12-31          |
| 1.0.x   | :x:                | EOL                    |

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them to our security team:
**Email**: ${SECURITY_CONTACT}

You should receive a response within 24 hours. If for some reason you do not, please follow up via email.

## Security Practices

### Code Security
- All code undergoes SAST (Static Application Security Testing)
- Dependency scanning with Snyk/Dependabot
- Secret detection in CI/CD
- Code review required for all changes

### Infrastructure Security
- Infrastructure as Code with Terraform
- Regular security patching
- Network segmentation
- Least privilege access

### Compliance
- ${COMPLIANCE_FRAMEWORK} compliance
- Regular security audits
- Incident response plan
- Data classification: ${DATA_CLASSIFICATION}

## Security Features

### Built-in Protections
- Authentication & authorization
- Rate limiting
- Input validation
- Security headers
- SQL injection prevention
- XSS protection

### Monitoring
- Security event logging
- Intrusion detection
- Anomaly detection
- Real-time alerts

## Best Practices for Users

1. **Keep dependencies updated**
2. **Use environment variables for secrets**
3. **Regularly rotate API keys**
4. **Monitor access logs**
5. **Follow principle of least privilege**
MD

  # Include enterprise changelog
  @include ../partials/CHANGELOG.lrc

# ==================== ENTERPRISE TESTING ====================
/tests
  __init__.py

  # Unit tests
  test_core.py <<PY
\"\"\"Enterprise core module tests.\"\"\"

import pytest
import asyncio
from src.core import EnterpriseService, ServiceConfig

class TestEnterpriseService:
    \"\"\"Test enterprise service functionality.\"\"\"

    @pytest.fixture
    def service_config(self):
        \"\"\"Provide service configuration for testing.\"\"\"
        return ServiceConfig(
            name="test-service",
            version="1.0.0",
            environment="testing"
        )

    @pytest.fixture
    async def service(self, service_config):
        \"\"\"Provide enterprise service instance.\"\"\"
        service = EnterpriseService(service_config)
        yield service
        await service.stop()

    @pytest.mark.asyncio
    async def test_service_start_stop(self, service):
        \"\"\"Test service startup and shutdown.\"\"\"
        # Start service
        start_task = asyncio.create_task(service.start())
        await asyncio.sleep(0.1)  # Let service start
        
        assert service.is_running
        
        # Stop service
        await service.stop()
        assert not service.is_running

    @pytest.mark.asyncio
    async def test_health_check(self, service):
        \"\"\"Test health check functionality.\"\"\"
        health = await service.health_check()
        
        assert "status" in health
        assert "version" in health
        assert "environment" in health
        assert "components" in health

    def test_config_validation(self, service_config):
        \"\"\"Test configuration validation.\"\"\"
        assert service_config.name == "test-service"
        assert service_config.environment == "testing"
        assert "monitoring" in service_config.features
PY

  test_security.py <<PY
\"\"\"Enterprise security module tests.\"\"\"

import pytest
from src.utils.security import SecurityManager, DataValidator

class TestSecurityManager:
    \"\"\"Test security manager functionality.\"\"\"

    @pytest.fixture
    def security_manager(self):
        \"\"\"Provide security manager instance.\"\"\"
        return SecurityManager()

    def test_token_generation(self, security_manager):
        \"\"\"Test token generation and verification.\"\"\"
        test_data = {"user_id": 123, "role": "admin"}
        
        token = security_manager.generate_token(test_data)
        assert isinstance(token, str)
        assert len(token) == 64  # SHA256 hex digest
        
        # Verify token
        assert security_manager.verify_token(token, test_data)
        
        # Test with different data
        wrong_data = {"user_id": 123, "role": "user"}
        assert not security_manager.verify_token(token, wrong_data)

class TestDataValidator:
    \"\"\"Test data validation functionality.\"\"\"

    def test_email_validation(self):
        \"\"\"Test email address validation.\"\"\"
        assert DataValidator.validate_email("user@example.com")
        assert DataValidator.validate_email("admin@company.co.uk")
        assert not DataValidator.validate_email("invalid-email")
        assert not DataValidator.validate_email("user@.com")

    def test_phone_validation(self):
        \"\"\"Test phone number validation.\"\"\"
        assert DataValidator.validate_phone("+1234567890")
        assert DataValidator.validate_phone("1234567890")
        assert not DataValidator.validate_phone("invalid-phone")
        assert not DataValidator.validate_phone("12-34-56")
PY

  test_api.py <<PY
\"\"\"Enterprise API tests.\"\"\"

import pytest
from fastapi.testclient import TestClient
from src.api.routes import router
from fastapi import FastAPI

class TestAPIEndpoints:
    \"\"\"Test API endpoint functionality.\"\"\"

    @pytest.fixture
    def client(self):
        \"\"\"Provide test client.\"\"\"
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_health_endpoint(self, client):
        \"\"\"Test health check endpoint.\"\"\"
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "${PROJECT_NAME}"
        assert "version" in data

    def test_metrics_endpoint_unauthorized(self, client):
        \"\"\"Test metrics endpoint without auth.\"\"\"
        response = client.get("/metrics")
        assert response.status_code == 403  # Should require auth

    def test_data_endpoint_validation(self, client):
        \"\"\"Test data endpoint input validation.\"\"\"
        response = client.post("/data", json={})
        assert response.status_code in [400, 403]  # Validation or auth error
PY

  # Integration tests
  integration/__init__.py
  integration/test_deployment.py <<PY
\"\"\"Deployment integration tests.\"\"\"

import pytest
import docker
import kubernetes

class TestDeployment:
    \"\"\"Test deployment configurations.\"\"\"

    def test_docker_image_build(self):
        \"\"\"Test Docker image builds successfully.\"\"\"
        client = docker.from_env()
        
        # This would build and test the image in a real scenario
        # For now, just verify we can connect to Docker
        assert client.ping()

    def test_kubernetes_manifests(self):
        \"\"\"Test Kubernetes manifest validity.\"\"\"
        # This would validate K8s manifests in a real scenario
        # For now, just verify the directory structure
        import os
        assert os.path.exists("deploy/kubernetes/")
PY

  # Performance tests
  performance/__init__.py
  performance/test_load.py <<PY
\"\"\"Load and performance tests.\"\"\"

import pytest
import asyncio
from src.core import EnterpriseService, ServiceConfig

class TestPerformance:
    \"\"\"Performance and load testing.\"\"\"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        \"\"\"Test handling concurrent requests.\"\"\"
        config = ServiceConfig(
            name="performance-test",
            version="1.0.0",
            environment="testing"
        )
        
        service = EnterpriseService(config)
        
        # Simulate concurrent health checks
        tasks = [
            service.health_check() 
            for _ in range(100)
        ]
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 100
        assert all("status" in result for result in results)
        
        await service.stop()
PY

  conftest.py <<PY
\"\"\"Enterprise test configuration.\"\"\"

import pytest
import asyncio
import logging
from typing import Generator

# Configure test logging
logging.basicConfig(level=logging.WARNING)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    \"\"\"Create event loop for async tests.\"\"\"
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def setup_test_environment():
    \"\"\"Setup test environment for all tests.\"\"\"
    # Set test environment variables
    import os
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["LOG_LEVEL"] = "WARNING"
    
    yield
    
    # Cleanup
    if "SECRET_KEY" in os.environ:
        del os.environ["SECRET_KEY"]
PY

# ==================== ENTERPRISE SCRIPTS ====================
/scripts
  # Development and deployment scripts
  dev.sh <<SH
#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Enterprise Development Environment"
echo "Project: ${PROJECT_NAME}"
echo "Environment: ${ENVIRONMENT}"

# Check prerequisites
echo "🔍 Checking prerequisites..."
python3 --version || { echo "❌ Python 3 required"; exit 1; }
docker --version || echo "⚠️  Docker not found (optional)"
kubectl version --client || echo "⚠️  kubectl not found (optional)"

# Setup virtual environment
if [ ! -d ".venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv .venv
fi

echo "🔧 Activating virtual environment..."
source .venv/bin/activate

echo "📦 Installing dependencies..."
pip install -e ".[dev]"

echo "✅ Development environment ready!"
echo ""
echo "💡 Next steps:"
echo "   ${PROJECT_NAME} --help"
echo "   ./scripts/test.sh"
echo "   ./scripts/security-scan.sh"
SH
  @chmod scripts/dev.sh +x

  test.sh <<SH
#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Enterprise Test Suite"
echo "========================"

# Run unit tests
echo "📝 Running unit tests..."
python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Run integration tests
echo "🔗 Running integration tests..."
python -m pytest tests/integration/ -v

# Run performance tests
echo "⚡ Running performance tests..."
python -m pytest tests/performance/ -v -m performance

# Generate coverage report
echo "📊 Generating coverage report..."
python -m coverage html

echo "✅ All tests completed!"
SH
  @chmod scripts/test.sh +x

  security-scan.sh <<SH
#!/usr/bin/env bash
set -euo pipefail

echo "🔒 Enterprise Security Scan"
echo "==========================="

# SAST with bandit
echo "🔍 Running SAST (Bandit)..."
python -m bandit -r src/ -f json -o reports/bandit-report.json

# Dependency scanning
echo "📦 Scanning dependencies..."
python -m safety check --json --output reports/safety-report.json

# Secret detection
echo "🕵️  Detecting secrets..."
git secrets --scan || true

# Generate security report
echo "📄 Generating security report..."
{
    echo "# Security Scan Report"
    echo "Generated: $(date)"
    echo ""
    echo "## SAST Results"
    cat reports/bandit-report.json | jq '.metrics._totals | "🔍 \(.CONFIDENCE.HIGH) high, \(.CONFIDENCE.MEDIUM) medium, \(.CONFIDENCE.LOW) low confidence issues"'
    echo ""
    echo "## Dependency Vulnerabilities"
    cat reports/safety-report.json | jq '. | "📦 \(.vulnerabilities | length) vulnerabilities found"'
} > reports/security-report.md

echo "✅ Security scan completed!"
echo "📊 Report: reports/security-report.md"
SH
  @chmod scripts/security-scan.sh +x

  deploy.sh <<SH
#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT=${1:-development}

echo "🚀 Deploying ${PROJECT_NAME} to ${ENVIRONMENT}"
echo "=============================================="

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT"
    exit 1
fi

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t ${DOCKER_NAMESPACE}/${PROJECT_NAME}:latest .

# Run tests
echo "🧪 Running pre-deployment tests..."
./scripts/test.sh

# Security scan
echo "🔒 Running security scan..."
./scripts/security-scan.sh

# Deploy based on environment
echo "📦 Deploying to ${ENVIRONMENT}..."
case $ENVIRONMENT in
    development)
        docker-compose -f deploy/docker-compose.dev.yml up -d
        ;;
    staging)
        kubectl apply -f deploy/kubernetes/staging/
        ;;
    production)
        kubectl apply -f deploy/kubernetes/production/
        ;;
esac

echo "✅ Deployment to ${ENVIRONMENT} completed!"
SH
  @chmod scripts/deploy.sh +x

  quality-check.sh <<SH
#!/usr/bin/env bash
set -euo pipefail

echo "📋 Enterprise Quality Check"
echo "==========================="

# Code formatting
echo "🎨 Checking code formatting..."
python -m black --check src/ tests/ || {
    echo "❌ Code formatting issues found"
    echo "💡 Run: python -m black src/ tests/"
    exit 1
}

# Type checking
echo "📝 Running type checks..."
python -m mypy src/ tests/ || {
    echo "❌ Type checking issues found"
    exit 1
}

# Linting
echo "🔍 Linting code..."
python -m flake8 src/ tests/ || {
    echo "❌ Linting issues found"
    exit 1
}

# Import sorting
echo "📦 Checking import order..."
python -m isort --check-only src/ tests/ || {
    echo "❌ Import order issues found"
    echo "💡 Run: python -m isort src/ tests/"
    exit 1
}

echo "✅ All quality checks passed!"
SH
  @chmod scripts/quality-check.sh +x

# ==================== ENTERPRISE DEPLOYMENT CONFIGURATIONS ====================
/deploy
  # Kubernetes manifests
  /kubernetes
    /production
      deployment.yaml <<YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${PROJECT_NAME}
  namespace: ${K8S_NAMESPACE}
  labels:
    app: ${PROJECT_NAME}
    environment: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ${PROJECT_NAME}
  template:
    metadata:
      labels:
        app: ${PROJECT_NAME}
        version: "2.0.0"
    spec:
      containers:
      - name: ${PROJECT_NAME}
        image: ${DOCKER_NAMESPACE}/${PROJECT_NAME}:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
YAML

      service.yaml <<YAML
apiVersion: v1
kind: Service
metadata:
  name: ${PROJECT_NAME}
  namespace: ${K8S_NAMESPACE}
spec:
  selector:
    app: ${PROJECT_NAME}
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
YAML

    /staging
      deployment.yaml <<YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${PROJECT_NAME}-staging
  namespace: ${K8S_NAMESPACE}
  labels:
    app: ${PROJECT_NAME}
    environment: staging
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ${PROJECT_NAME}
  template:
    metadata:
      labels:
        app: ${PROJECT_NAME}
        version: "2.0.0"
    spec:
      containers:
      - name: ${PROJECT_NAME}
        image: ${DOCKER_NAMESPACE}/${PROJECT_NAME}:staging
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "staging"
        - name: LOG_LEVEL
          value: "DEBUG"
YAML

  # Docker configurations
  /docker
    Dockerfile <<DOCKER
FROM python:${PYTHON_VERSION}-slim

# Security: Run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "-m", "src.cli", "start", "--environment", "production"]
DOCKER

    docker-compose.dev.yml <<YAML
version: '3.8'

services:
  ${PROJECT_NAME}:
    build:
      context: ../..
      dockerfile: deploy/docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    volumes:
      - ../../src:/app/src
      - ../../config:/app/config
    develop:
      watch:
        - action: sync
          path: ./src
          target: /app/src
        - action: rebuild
          path: requirements.txt
YAML

# ==================== ENTERPRISE INFRASTRUCTURE ====================
/terraform
  main.tf <<TF
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

# AWS Provider
provider "aws" {
  region = var.region
}

# ECR Repository
resource "aws_ecr_repository" "app" {
  name = "${PROJECT_NAME}"
  
  image_scanning_configuration {
    scan_on_push = true
  }
}

# EKS Cluster (simplified)
resource "aws_eks_cluster" "main" {
  name     = "${PROJECT_NAME}-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  
  vpc_config {
    subnet_ids = var.subnet_ids
  }
  
  enabled_cluster_log_types = ["api", "audit"]
}

# IAM Role for EKS
resource "aws_iam_role" "eks_cluster" {
  name = "${PROJECT_NAME}-eks-cluster"
  
  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
}

# Variables
variable "region" {
  description = "AWS region"
  type        = string
  default     = "${REGION}"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "${ENVIRONMENT}"
}

variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
}
TF

  outputs.tf <<TF
output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.app.repository_url
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}
TF

# ==================== ENTERPRISE MONITORING ====================
/monitoring
  prometheus.yml <<YAML
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: '${PROJECT_NAME}'
    static_configs:
      - targets: ['${PROJECT_NAME}:8000']
    metrics_path: /metrics
    scrape_interval: 30s
YAML

  grafana-dashboard.json <<JSON
{
  "dashboard": {
    "title": "${PROJECT_NAME} - Enterprise Dashboard",
    "panels": [
      {
        "title": "Service Health",
        "type": "stat",
        "targets": [{
          "expr": "up{job=\"${PROJECT_NAME}\"}",
          "legendFormat": "Instance {{instance}}"
        }]
      }
    ]
  }
}
JSON

# ==================== ENTERPRISE SECURITY ====================
/security
  policy.yaml <<YAML
# Enterprise Security Policy
version: "1.0"
project: "${PROJECT_NAME}"
framework: "${COMPLIANCE_FRAMEWORK}"

security_requirements:
  authentication:
    - jwt_tokens
    - api_keys
  authorization:
    - role_based_access
    - resource_permissions
  data_protection:
    - encryption_at_rest
    - encryption_in_transit
  monitoring:
    - security_event_logging
    - intrusion_detection

compliance:
  data_classification: "${DATA_CLASSIFICATION}"
  retention_period: "7 years"
  audit_requirements:
    - monthly_security_reviews
    - quarterly_vulnerability_assessments
YAML

# ==================== ENTERPRISE COMPLIANCE ====================
/compliance
  SOC2-checklist.md <<MD
# SOC2 Compliance Checklist

## Security
- [ ] Access controls implemented
- [ ] Authentication mechanisms in place
- [ ] Encryption for data at rest and in transit
- [ ] Regular security training

## Availability
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery procedures
- [ ] Incident response plan

## Confidentiality
- [ ] Data classification: ${DATA_CLASSIFICATION}
- [ ] Access logging enabled
- [ ] Secure data disposal

## Documentation
- [ ] Security policies documented
- [ ] Change management procedures
- [ ] Risk assessment completed
MD

# ==================== ENTERPRISE GITHUB ACTIONS ====================
/.github
  /workflows
    ci-cd.yml <<YAML
name: Enterprise CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: ./scripts/test.sh
    
    - name: Run security scan
      run: ./scripts/security-scan.sh
    
    - name: Run quality checks
      run: ./scripts/quality-check.sh

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: ./scripts/deploy.sh production
      env:
        KUBECONFIG: ${{ secrets.KUBECONFIG }}
        DOCKER_REGISTRY: ${{ secrets.DOCKER_REGISTRY }}
YAML

    security-scan.yml <<YAML
name: Security Scan

on:
  schedule:
    - cron: '0 6 * * 1'  # Weekly on Monday
  push:
    branches: [ main ]

jobs:
  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run SAST
      uses: py-actions/bandit@v2
      with:
        path: src/
    
    - name: Dependency scan
      uses: py-actions/safety@v1
      with:
        path: requirements.txt
    
    - name: Secret scanning
      uses: gitleaks/gitleaks-action@v2
YAML

# ==================== ENTERPRISE CONFIGURATION ====================
/config
  production.yaml <<YAML
# Production Configuration
name: ${PROJECT_NAME}
version: 2.0.0
environment: production

server:
  port: 8000
  workers: 4
  debug: false

features:
  monitoring: true
  security: true
  caching: true
  rate_limiting: true

logging:
  level: INFO
  format: json

security:
  secret_key: ${SECRET_KEY}
  token_expiry: 3600
  rate_limit: 100
YAML

  development.yaml <<YAML
# Development Configuration
name: ${PROJECT_NAME}
version: 2.0.0
environment: development

server:
  port: 8000
  workers: 2
  debug: true

features:
  monitoring: true
  security: true
  caching: false
  rate_limiting: false

logging:
  level: DEBUG
  format: console

security:
  secret_key: dev-secret-key
  token_expiry: 3600
  rate_limit: 1000
YAML

# ==================== ENTERPRISE ASSETS ====================
/assets
  # Placeholder for enterprise assets
  logo.svg <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="60">
  <rect width="100%" height="100%" fill="#1a365d"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" 
        fill="#ffffff" font-family="Arial, sans-serif" font-size="24" font-weight="bold">
    ${PROJECT_NAME}
  </text>
  <text x="50%" y="75%" dominant-baseline="middle" text-anchor="middle"
        fill="#a0aec0" font-family="Arial, sans-serif" font-size="12">
    ENTERPRISE EDITION
  </text>
</svg>
SVG

# ==================== ENTERPRISE PROJECT FILES ====================
.gitignore <<GIT
# Enterprise Git Ignore Patterns

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.mypy_cache/
.pytest_cache/

# Virtual environments
.venv/
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Coverage reports
.coverage
htmlcov/

# Environment files
.env
.env.local
.env.production
.local.env

# Security
secrets.txt
*.key
*.pem
*.crt

# Terraform
.terraform/
terraform.tfstate*
*.tfvars

# Docker
docker-compose.override.yml

# Temporary files
*.tmp
*.temp
.cache/
GIT

LICENSE <<TXT
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

1. Definitions.

   "License" shall mean the terms and conditions for use, reproduction,
   and distribution as defined by Sections 1 through 9 of this document.

   "Licensor" shall mean the copyright owner or entity authorized by
   the copyright owner that is granting the License.

   "Legal Entity" shall mean the union of the acting entity and all
   other entities that control, are controlled by, or are under common
   control with that entity. For the purposes of this definition,
   "control" means (i) the power, direct or indirect, to cause the
   direction or management of such entity, whether by contract or
   otherwise, or (ii) ownership of fifty percent (50%) or more of the
   outstanding shares, or (iii) beneficial ownership of such entity.

   "You" (or "Your") shall mean an individual or Legal Entity
   exercising permissions granted by this License.

   "Source" form shall mean the preferred form for making modifications,
   including but not limited to software source code, documentation
   source, and configuration files.

   "Object" form shall mean any form resulting from mechanical
   transformation or translation of a Source form, including but
   limited to compiled object code, generated documentation,
   and conversions to other media types.

   "Work" shall mean the work of authorship, whether in Source or
   Object form, made available under the License, as indicated by a
   copyright notice that is included in or attached to the work
   (an example is provided in the Appendix below).

   "Derivative Works" shall mean any work, whether in Source or Object form,
   that is based on (or derived from) the Work and for which the editorial
   revisions, annotations, elaborations, or other modifications represent,
   as a whole, an original work of authorship. For the purposes of this License,
   Derivative Works shall not include works that remain separable from,
   or merely link (or bind by name) to the interfaces of, the Work and
   Derivative Works thereof.

   "Contribution" shall mean any work of authorship, including
   the original version of the Work and any modifications or additions
   to that Work or Derivative Works thereof, that is intentionally
   submitted to Licensor for inclusion in the Work by the copyright owner
   or by an individual or Legal Entity authorized to submit on behalf of
   the copyright owner. For the purposes of this definition, "submitted"
   means any form of electronic, verbal, or written communication sent
   to the Licensor or its representatives, including but not limited to
   communication on electronic mailing lists, source code control systems,
   and issue tracking systems that are managed by, or on behalf of, the
   Licensor for the purpose of discussing and improving the Work, but
   excluding communication that is clearly marked or otherwise designated
   in writing by the copyright owner as "Not a Contribution."

   "Contributor" shall mean Licensor and any individual or Legal Entity
   on behalf of whom a Contribution has been received by Licensor and
   subsequently incorporated within the Work.

2. Grant of Copyright License. Subject to the terms and conditions of
   this License, each Contributor hereby grants to You a perpetual,
   worldwide, non-exclusive, no-charge, royalty-free, irrevocable
   copyright license to reproduce, prepare Derivative Works of,
   publicly display, publicly perform, sublicense, and distribute the
   Work and such Derivative Works in Source or Object form.

3. Grant of Patent License. Subject to the terms and conditions of
   this License, each Contributor hereby grants to You a perpetual,
   worldwide, non-exclusive, no-charge, royalty-free, irrevocable
   (except as stated in this section) patent license to make, have made,
   use, offer to sell, sell, import, and otherwise transfer the Work,
   where such license applies only to those patent claims licensable
   by such Contributor that are necessarily infringed by their
   Contribution(s) alone or by combination of their Contribution(s)
   with the Work to which such Contribution(s) was submitted. If You
   institute patent litigation against any entity (including a
   cross-claim or counterclaim in a lawsuit) alleging that the Work
   or a Contribution incorporated within the Work constitutes direct
   or contributory patent infringement, then any patent licenses
   granted to You under this License for that Work shall terminate
   as of the date such litigation is filed.

4. Redistribution. You may reproduce and distribute copies of the
   Work or Derivative Works thereof in any medium, with or without
   modifications, and in Source or Object form, provided that You
   meet the following conditions:

   (a) You must give any other recipients of the Work or
       Derivative Works a copy of this License; and

   (b) You must cause any modified files to carry prominent notices
       stating that You changed the files; and

   (c) You must retain, in the Source form of any Derivative Works
       that You distribute, all copyright, patent, trademark, and
       attribution notices from the Source form of the Work,
       excluding those notices that do not pertain to any part of
       the Derivative Works; and

   (d) If the Work includes a "NOTICE" text file as part of its
       distribution, then any Derivative Works that You distribute must
       include a readable copy of the attribution notices contained
       within such NOTICE file, excluding those notices that do not
       pertain to any part of the Derivative Works, in at least one
       of the following places: within a NOTICE text file distributed
       as part of the Derivative Works; within the Source form or
       documentation, if provided along with the Derivative Works; or,
       within a display generated by the Derivative Works, if and
       wherever such third-party notices normally appear. The contents
       of the NOTICE file are for informational purposes only and
       do not modify the License. You may add Your own attribution
       notices within Derivative Works that You distribute, alongside
       or as an addendum to the NOTICE text from the Work, provided
       that such additional attribution notices cannot be construed
       as modifying the License.

   You may add Your own copyright statement to Your modifications and
   may provide additional or different license terms and conditions
   for use, reproduction, or distribution of Your modifications, or
   for any such Derivative Works as a whole, provided Your use,
   reproduction, and distribution of the Work otherwise complies with
   the conditions stated in this License.

5. Submission of Contributions. Unless You explicitly state otherwise,
   any Contribution intentionally submitted for inclusion in the Work
   by You to the Licensor shall be under the terms and conditions of
   this License, without any additional terms or conditions.
   Notwithstanding the above, nothing herein shall supersede or modify
   the terms of any separate license agreement you may have executed
   with Licensor regarding such Contributions.

6. Trademarks. This License does not grant permission to use the trade
   names, trademarks, service marks, or product names of the Licensor,
   except as required for reasonable and customary use in describing the
   origin of the Work and reproducing the content of the NOTICE file.

7. Disclaimer of Warranty. Unless required by applicable law or
   agreed to in writing, Licensor provides the Work (and each
   Contributor provides its Contributions) on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
   implied, including, without limitation, any warranties or conditions
   of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
   PARTICULAR PURPOSE. You are solely responsible for determining the
   appropriateness of using or redistributing the Work and assume any
   risks associated with Your exercise of permissions under this License.

8. Limitation of Liability. In no event and under no legal theory,
   whether in tort (including negligence), contract, or otherwise,
   unless required by applicable law (such as deliberate and grossly
   negligent acts) or agreed to in writing, shall any Contributor be
   liable to You for damages, including any direct, indirect, special,
   incidental, or consequential damages of any character arising as a
   result of this License or out of the use or inability to use the
   Work (including but not limited to damages for loss of goodwill,
   work stoppage, computer failure or malfunction, or any and all
   other commercial damages or losses), even if such Contributor
   has been advised of the possibility of such damages.

9. Accepting Warranty or Additional Liability. While redistributing
   the Work or Derivative Works thereof, You may choose to offer,
   and charge a fee for, acceptance of support, warranty, indemnity,
   or other liability obligations and/or rights consistent with this
   License. However, in accepting such obligations, You may act only
   on Your own behalf and on Your sole responsibility, not on behalf
   of any other Contributor, and only if You agree to indemnify,
   defend, and hold each Contributor harmless for any liability
   incurred by, or claims asserted against, such Contributor by reason
   of your accepting any such warranty or additional liability.

END OF TERMS AND CONDITIONS
TXT

pyproject.toml <<TOML
[project]
name = "${PROJECT_NAME}"
version = "2.0.0"
description = "${DESCRIPTION}"
readme = "README.md"
requires-python = ">=${PYTHON_VERSION}"
authors = [
    { name = "${AUTHOR}", email = "${SUPPORT_EMAIL}" }
]
keywords = ["enterprise", "api", "security", "monitoring", "devops", "kubernetes"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Libraries :: Application Frameworks",
    "Topic :: System :: Systems Administration",
    "Framework :: FastAPI",
    "Typing :: Typed",
]

dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.23.0",
    "pydantic>=2.0.0",
    "python-multipart>=0.0.6",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "pyyaml>=6.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "mypy>=1.5.0",
    "flake8>=6.0.0",
    "isort>=5.12.0",
    "bandit>=1.7.5",
    "safety>=2.3.0",
    "pre-commit>=3.3.0",
]
security = [
    "cryptography>=41.0.0",
    "bcrypt>=4.0.0",
]
monitoring = [
    "prometheus-client>=0.17.0",
    "structlog>=23.0.0",
]
docker = [
    "docker>=6.1.0",
]

[project.urls]
Homepage = "${PROJECT_URL}"
Repository = "${PROJECT_URL}"
Documentation = "${PROJECT_URL}/docs"
"Bug Reports" = "${PROJECT_URL}/issues"
"Changelog" = "${PROJECT_URL}/releases"

[project.scripts]
${PROJECT_NAME} = "src.cli:main"

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py38']
include = '\\.pyi?$'

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "--verbose --strict-markers --strict-config"
testpaths = ["tests"]
pythonpath = ["src"]
asyncio_mode = "auto"
markers = [
    "performance: performance tests",
    "integration: integration tests",
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\\\bProtocol\\\\):",
    "@(abc\\\\.)?abstractmethod",
]
TOML

README.md <<MD
# ${PROJECT_NAME}

> **Enterprise-Grade Project Template**

${DESCRIPTION}

## 🏢 Enterprise Features

- **🔒 Security First**: Built-in security scanning, authentication, and compliance
- **📊 Monitoring Ready**: Comprehensive metrics, logging, and health checks  
- **🐳 DevOps Integration**: Docker, Kubernetes, Terraform, and CI/CD ready
- **📝 Type Safety**: Full type hints and mypy compliance
- **⚡ Async Ready**: Full async/await support throughout
- **⚙️ Configuration Management**: Environment-aware configuration
- **🌐 API First**: RESTful API with OpenAPI documentation

## 🚀 Quick Start

### Generate Project
\`\`\`bash
lrc schema_example.lrc -o ./my-enterprise-project
cd my-enterprise-project
\`\`\`

### Development Setup
\`\`\`bash
./scripts/dev.sh
${PROJECT_NAME} --help
\`\`\`

### Run Tests & Security
\`\`\`bash
./scripts/test.sh
./scripts/security-scan.sh
./scripts/quality-check.sh
\`\`\`

## 📁 Enterprise Structure

\`\`\`
${PROJECT_NAME}/
├── src/                 # Source code
│   ├── api/            # FastAPI routes & middleware
│   ├── core/           # Business logic & services
│   └── utils/          # Security, monitoring, validation
├── tests/              # Comprehensive test suite
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests  
│   └── performance/    # Performance tests
├── deploy/             # Deployment configurations
│   ├── kubernetes/     # K8s manifests
│   └── docker/         # Docker configurations
├── terraform/          # Infrastructure as Code
├── monitoring/         # Prometheus & Grafana configs
├── security/           # Security policies & scans
├── compliance/         # Compliance documentation
├── config/             # Environment configurations
├── scripts/            # Enterprise-grade scripts
└── .github/            # CI/CD workflows
\`\`\`

## 🔧 Configuration

### Environment Setup
\`\`\`bash
export ENVIRONMENT=production
export LOG_LEVEL=INFO  
export SECRET_KEY=your-secure-key
\`\`\`

### Configuration Files
- \`config/development.yaml\` - Development settings
- \`config/production.yaml\` - Production settings  
- \`config/security.yaml\` - Security configurations

## 🧪 Quality Assurance

### Testing
\`\`\`bash
# Full test suite
./scripts/test.sh

# Security scanning  
./scripts/security-scan.sh

# Code quality
./scripts/quality-check.sh
\`\`\`

### CI/CD
- Automated testing on PRs
- Security scanning weekly
- Production deployments from main

## 📊 Monitoring

- **Metrics**: Prometheus endpoints at \`/metrics\`
- **Health**: Comprehensive health checks at \`/health\`  
- **Logging**: Structured JSON logging
- **Tracing**: Distributed tracing support

## 🔒 Security

### Features
- JWT Authentication
- Rate Limiting  
- Security Headers
- Input Validation
- Dependency Scanning
- Secret Detection

### Compliance
- ${COMPLIANCE_FRAMEWORK} compliant
- Data classification: ${DATA_CLASSIFICATION}
- Regular security audits

## 🐳 Deployment

### Docker
\`\`\`bash
docker build -t ${DOCKER_NAMESPACE}/${PROJECT_NAME} .
docker-compose -f deploy/docker-compose.dev.yml up
\`\`\`

### Kubernetes
\`\`\`bash
kubectl apply -f deploy/kubernetes/production/
\`\`\`

### Terraform
\`\`\`bash
terraform init
terraform apply -var environment=production
\`\`\`

## 🤝 Contributing

1. Follow [Conventional Commits](https://www.conventionalcommits.org/)
2. Update tests and documentation
3. Run security scans before submitting
4. Ensure all CI/CD checks pass

## 📞 Support

- **Team**: ${TEAM_NAME}
- **Email**: ${SUPPORT_EMAIL}  
- **Security**: ${SECURITY_CONTACT}
- **Documentation**: ${PROJECT_URL}/docs

## 📄 License

${LICENSE} License - See [LICENSE](LICENSE) for details.

---

*Generated by LRC Enterprise Template v2.0.0 | Built for scale, security, and reliability*
MD

# ==================== ENTERPRISE CHANGELOG ====================
CHANGELOG.md <<MD
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - ${YEAR}-01-01

### Added
- **Enterprise Architecture**: Complete enterprise-grade project structure
- **Security Framework**: Comprehensive security utilities and scanning
- **Monitoring & Observability**: Prometheus metrics, structured logging, health checks
- **DevOps Integration**: Docker, Kubernetes, Terraform configurations
- **API Layer**: FastAPI with authentication, rate limiting, and middleware
- **Testing Suite**: Unit, integration, and performance tests
- **Quality Assurance**: Code formatting, type checking, linting
- **CI/CD Pipeline**: GitHub Actions with security scanning
- **Compliance**: SOC2 checklist and security policies
- **Documentation**: Comprehensive enterprise documentation

### Changed
- Upgraded to LRC schema version 1.1
- Enhanced project structure for enterprise use cases
- Improved security practices and compliance
- Updated to modern Python async patterns

### Security
- Built-in security scanning and vulnerability detection
- Authentication and authorization framework
- Security headers and input validation
- Dependency vulnerability monitoring

## [1.0.0] - ${YEAR}-01-01

### Added
- Initial enterprise template release
- Basic project structure and tooling
- Foundation for enterprise features

---

*Enterprise Template maintained by ${TEAM_NAME}*
MD

# ==================== END OF ENTERPRISE SCHEMA ====================
# This schema demonstrates a comprehensive enterprise-ready project template
# Customize the variables and file contents above, then run:
#   lrc schema_entprse_example.lrc -o ./my-enterprise-project
# to generate your enterprise project!

# For more LRC enterprise examples and documentation, visit:
# https://github.com/Justadudeinspace/lrc


FILE: examples/schema_example.lrc
Kind: text
Size: 12711
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# examples/schema_example.lrc
# Project: my-awesome-project
# Description: A template project demonstrating LRC features
# Version: 1.0.0

# ==================== VARIABLES ====================
# Define variables that can be reused throughout the schema
# Syntax: @set KEY=VALUE
# Reference variables with ${KEY} in file paths and contents

@set AUTHOR=Your Name Here
@set EMAIL=your.email@example.com
@set PROJECT_NAME=my-awesome-project
@set DESCRIPTION=A fantastic project built with LRC
@set YEAR=2025
@set LICENSE=MIT
@set PYTHON_VERSION=3.9

# ==================== IGNORE PATTERNS ====================
# Files/directories to ignore when generating the project
# These won't be created even if referenced in the schema

@ignore node_modules .venv __pycache__ .DS_Store *.tmp build dist

# ==================== TEMPLATES ====================
# Apply a pre-built template (python-cli, node-cli, rust-cli)
# Templates create common project structures automatically

@template python-cli

# ==================== PROJECT STRUCTURE ====================
# Create directory structure
# Lines starting with "/" create directories at the root level
# Lines ending with "/" create directories at current level

/src
/docs
/tests
/scripts
/assets
/examples

# ==================== SOURCE CODE FILES ====================
# Enter the /src directory (indentation defines nesting)
/src
  # Create an empty file
  __init__.py
  
  # Create a file with inline content using "->"
  version.py -> __version__ = "1.0.0"
  
  # Create a file with multi-line content using heredoc "<<"
  main.py <<PY
#!/usr/bin/env python3
"""
${PROJECT_NAME} - ${DESCRIPTION}
"""

def main():
    print("Hello from ${PROJECT_NAME}!")
    print("Created by ${AUTHOR}")

if __name__ == "__main__":
    main()
PY
  
  # Set executable permissions on Unix-like systems
  @chmod src/main.py +x
  
  # Create a subdirectory
  utils/
    __init__.py
    helpers.py <<PY
"""Utility functions for ${PROJECT_NAME}."""

def greet_user(name: str) -> str:
    \"\"\"Return a personalized greeting.\"\"\"
    return f"Hello, {name}! Welcome to ${PROJECT_NAME}."

def calculate_sum(a: float, b: float) -> float:
    \"\"\"Calculate the sum of two numbers.\"\"\"
    return a + b
PY

# ==================== DOCUMENTATION ====================
/docs
  README.md <<MD
# ${PROJECT_NAME}

${DESCRIPTION}

## Features

- Feature 1: Describe what your project does
- Feature 2: List key functionality  
- Feature 3: Highlight unique aspects

## Installation

\`\`\`bash
# Clone the repository
git clone <your-repo-url>
cd ${PROJECT_NAME}

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Install in development mode
pip install -e .
\`\`\`

## Usage

\`\`\`bash
# Run the main application
python src/main.py

# Or use the installed command
${PROJECT_NAME}
\`\`\`

## Development

See the scripts in the \`/scripts\` directory for development tools.

## About This Template

This project was generated using **LRC** (Local Repo Compile), a tool that creates projects from declarative schemas.

### LRC Features Demonstrated:

- **Variables**: Reusable values like \${AUTHOR}, \${PROJECT_NAME}
- **Directives**: Special commands starting with @
- **Heredocs**: Multi-line content blocks
- **File Operations**: Creating files with different methods
- **Permissions**: Setting executable flags
- **Templates**: Pre-built project structures
MD

  # Include content from another file
  @include ../partials/CHANGELOG.lrc

# ==================== TESTING ====================
/tests
  __init__.py
  
  # Test files with example test cases
  test_main.py <<PY
\"\"\"Tests for the main module.\"\"\"

from src.main import main

def test_main_output(capsys):
    \"\"\"Test that main function prints expected output.\"\"\"
    main()
    captured = capsys.readouterr()
    assert "${PROJECT_NAME}" in captured.out

def test_main_import():
    \"\"\"Test that main can be imported.\"\"\"
    from src.main import main
    assert callable(main)
PY

  test_utils.py <<PY
\"\"\"Tests for utility functions.\"\"\"

from src.utils.helpers import greet_user, calculate_sum

def test_greet_user():
    \"\"\"Test the greet_user function.\"\"\"
    result = greet_user("Alice")
    assert "Alice" in result
    assert "${PROJECT_NAME}" in result

def test_calculate_sum():
    \"\"\"Test the calculate_sum function.\"\"\"
    assert calculate_sum(2, 3) == 5
    assert calculate_sum(-1, 1) == 0
    assert calculate_sum(0, 0) == 0
PY

# ==================== SCRIPTS ====================
/scripts
  # Development script with heredoc
  dev.sh <<SH
#!/usr/bin/env bash
# Development script for ${PROJECT_NAME}

echo "🚀 Starting ${PROJECT_NAME} development environment..."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the main script
python src/main.py

echo "✅ Development session complete!"
SH
  
  # Make the script executable
  @chmod scripts/dev.sh +x
  
  test.sh <<SH
#!/usr/bin/env bash
# Test script for ${PROJECT_NAME}

echo "🧪 Running tests for ${PROJECT_NAME}..."

# Run tests
python -m pytest tests/ -v

echo "✅ Tests completed!"
SH
  @chmod scripts/test.sh +x

# ==================== ASSETS ====================
/assets
  # Copy files from external locations
  # @copy <source_path> <destination_path>
  @copy ../assets/logo.png assets/logo.png
  
  # Create asset subdirectories
  icons/
  images/

# ==================== EXAMPLES ====================
/examples
  basic_usage.py <<PY
\"\"\"Basic usage example for ${PROJECT_NAME}.\"\"\"

from src.utils.helpers import greet_user, calculate_sum

def demonstrate_features():
    \"\"\"Show how to use the project's features.\"\"\"
    
    print("${PROJECT_NAME} - Usage Examples")
    print("=" * 40)
    
    # Demonstrate greeting functionality
    greeting = greet_user("World")
    print(f"Greeting: {greeting}")
    
    # Demonstrate calculation functionality
    result = calculate_sum(10, 20)
    print(f"10 + 20 = {result}")
    
    print("\\n🎉 Examples completed!")

if __name__ == "__main__":
    demonstrate_features()
PY

  advanced_usage.py <<PY
\"\"\"Advanced usage example for ${PROJECT_NAME}.\"\"\"

# This file demonstrates more complex usage patterns
# Add your advanced examples here

class AdvancedDemo:
    \"\"\"A class demonstrating advanced features.\"\"\"
    
    def __init__(self, name: str):
        self.name = name
    
    def demonstrate(self):
        \"\"\"Run the advanced demonstration.\"\"\"
        print(f"Advanced demo for {self.name}")
        # Add your advanced logic here

if __name__ == "__main__":
    demo = AdvancedDemo("${PROJECT_NAME}")
    demo.demonstrate()
PY

# ==================== PROJECT CONFIGURATION FILES ====================
# Project metadata and configuration

.gitignore <<GIT
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environment
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
GIT

LICENSE <<TXT
${LICENSE} License

Copyright (c) ${YEAR} ${AUTHOR}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
TXT

pyproject.toml <<TOML
[project]
name = "${PROJECT_NAME}"
version = "1.0.0"
description = "${DESCRIPTION}"
readme = "README.md"
requires-python = ">=${PYTHON_VERSION}"
authors = [
    { name = "${AUTHOR}", email = "${EMAIL}" }
]
keywords = ["template", "demo", "lrc"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
]

dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
]

[project.scripts]
${PROJECT_NAME} = "src.main:main"

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"
TOML

# ==================== LRC LEARNING GUIDE ====================
LEARNING_GUIDE.md <<MD
# LRC Learning Guide

This project demonstrates all major features of **LRC** (Local Repo Compile). Here's how to use each feature:

## 1. Variables

Define reusable values with `@set` and reference them with `\${VARIABLE}`:

\`\`\`bash
# Define variables
@set PROJECT_NAME=my-project
@set AUTHOR=John Doe

# Use variables
README.md -> # \${PROJECT_NAME} by \${AUTHOR}
\`\`\`

## 2. File Creation Methods

### Empty Files
\`\`\`bash
# Creates an empty file
filename.py
\`\`\`

### Inline Content (Single Line)
\`\`\`bash
# Creates a file with one line of content
config.json -> {"key": "value"}
\`\`\`

### Multi-line Content (Heredoc)
\`\`\`bash
# Creates a file with multiple lines
script.py <<PY
#!/usr/bin/env python3
print("Hello World")
print("Multi-line content")
PY
\`\`\`

## 3. Directives

Special commands that start with `@`:

### @set
Define variables for reuse.

### @ignore  
Prevent certain files/directories from being created.

### @template
Apply a pre-built project template.

### @chmod
Set file permissions (Unix-like systems).

### @include
Insert content from another file.

### @copy
Copy files from external locations.

## 4. Directory Structure

- **Absolute paths** (start with `/`): Create at project root
- **Relative paths** (end with `/`): Create in current directory
- **Indentation**: Defines nesting level

## 5. Best Practices

1. **Define variables first** for easy customization
2. **Use descriptive names** for projects and variables
3. **Include comprehensive documentation**
4. **Add tests** for better code quality
5. **Use heredocs** for multi-line content
6. **Set executable permissions** on scripts

## 6. Running LRC

\`\`\`bash
# Generate the project
lrc schema_example.lrc

# Generate with custom output directory
lrc schema_example.lrc -o ./my-project

# Preview without making changes (dry run)
lrc schema_example.lrc --dry-run

# Overwrite existing files
lrc schema_example.lrc --force
\`\`\`

## Next Steps

1. Customize the variables at the top of this file
2. Modify file contents to match your project needs
3. Add your own source code files
4. Run \`lrc schema_example.lrc\` to generate your project
5. Start developing!

Happy coding! 🚀
MD

README.md <<MD
# ${PROJECT_NAME}

This project was generated using **LRC** (Local Repo Compile).

## Quick Start

1. **Customize this schema**:
   - Edit the variables at the top of \`schema_example.lrc\`
   - Modify file contents to match your project needs

2. **Generate your project**:
   \`\`\`bash
   lrc schema_example.lrc
   \`\`\`

3. **Start developing**:
   \`\`\`bash
   cd ${PROJECT_NAME}
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   \`\`\`

## Project Structure

\`\`\`
${PROJECT_NAME}/
├── src/           # Source code
├── tests/         # Test suite
├── docs/          # Documentation  
├── scripts/       # Development scripts
├── assets/        # Static assets
├── examples/      # Usage examples
├── pyproject.toml # Project configuration
├── LICENSE        # License file
└── README.md      # This file
\`\`\`

## Learn LRC

See \`LEARNING_GUIDE.md\` for a comprehensive guide to LRC features and syntax.

## License

${LICENSE} License - see [LICENSE](LICENSE) for details.
MD

# ==================== END OF SCHEMA ====================
# This schema demonstrates a complete, working project template
# Customize the variables and file contents above, then run:
#   lrc schema_example.lrc
# to generate your own project!

# For more LRC examples and documentation, visit:
# https://github.com/Justadudeinspace/lrc


FILE: examples/schema_org_example.lrc
Kind: text
Size: 41920
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# examples/schema_org_example.lrc
# Organization Project Template
# Project: org-project-template
# Description: Structured project template for teams and organizations
# Version: 1.0.0
# Schema-Version: 1.1
# Generator: LRC v0.2.2
# Focus: Collaboration, standards, scalability, maintainability

# ==================== ORGANIZATION VARIABLES ====================
@set ORGANIZATION=Your Organization
@set TEAM=Engineering Team
@set MAINTAINER_TEAM=platform-engineering@org.com
@set PROJECT_NAME=org-project-template
@set DESCRIPTION=Structured project template for organizational development
@set YEAR=2025
@set LICENSE=Apache-2.0
@set PYTHON_VERSION=3.9
@set CODE_OWNERS=@org/engineering-team
@set SLACK_CHANNEL=#engineering-projects
@set JIRA_PROJECT=ENG

# ==================== ORGANIZATION STANDARDS ====================
@ignore node_modules .venv __pycache__ .DS_Store *.tmp build dist *.egg-info
@ignore .mypy_cache .pytest_cache .coverage htmlcov
@ignore local_settings.py *.local.* .env.local

# ==================== ORGANIZATION TEMPLATE ====================
@template python-cli

# ==================== ORGANIZATION STRUCTURE ====================
/src
/tests
/docs
/scripts
/config
/deploy
/helm
/terraform
/.github
/compliance
/monitoring

# ==================== ORGANIZATION SOURCE CODE ====================
/src
  __init__.py <<PY
"""${PROJECT_NAME} - ${DESCRIPTION}

Organization: ${ORGANIZATION}
Team: ${TEAM}
"""

__version__ = "1.0.0"
__organization__ = "${ORGANIZATION}"
__team__ = "${TEAM}"

import logging
from typing import Optional

# Organization-standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(team)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger = logging.LoggerAdapter(logger, {'team': '${TEAM}'})

from .cli import main
from .services import CoreService, DataService
from .models import BaseModel, User, Project
from .utils import validation, security, monitoring

__all__ = [
    "main",
    "CoreService", 
    "DataService",
    "BaseModel",
    "User",
    "Project",
    "validation",
    "security", 
    "monitoring",
    "logger"
]
PY

  cli.py <<PY
#!/usr/bin/env python3
"""${PROJECT_NAME} - Organization CLI"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .__init__ import __version__, logger
from .services import CoreService
from .utils.monitoring import MetricsCollector

class OrganizationCLI:
    \"\"\"Organization-standard CLI with team features.\"\"\"

    def __init__(self):
        self.parser = self._create_parser()
        self.metrics = MetricsCollector(team="${TEAM}")

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="${PROJECT_NAME}",
            description="${DESCRIPTION}",
            epilog=f"Organization: {ORGANIZATION} | Team: {TEAM}"
        )

        # Organization-standard subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Development command
        dev_parser = subparsers.add_parser("dev", help="Development operations")
        dev_parser.add_argument("--environment", choices=["local", "staging"],
                              default="local", help="Development environment")

        # Testing command
        test_parser = subparsers.add_parser("test", help="Run test suite")
        test_parser.add_argument("--coverage", action="store_true",
                               help="Generate coverage report")
        test_parser.add_argument("--slow", action="store_true",
                               help="Include slow tests")

        # Deployment command
        deploy_parser = subparsers.add_parser("deploy", help="Deployment operations")
        deploy_parser.add_argument("environment", choices=["staging", "production"],
                                 help="Deployment environment")
        deploy_parser.add_argument("--dry-run", action="store_true",
                                 help="Preview deployment")

        # Common organization arguments
        parser.add_argument("--version", action="version", 
                          version=f"%(prog)s {__version__}")
        parser.add_argument("--log-level", 
                          choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                          default="INFO", help="Logging level")
        parser.add_argument("--team", default="${TEAM}",
                          help="Team name for logging")

        return parser

    def run(self, args: Optional[list] = None) -> int:
        \"\"\"Execute CLI command with organization standards.\"\"\"
        parsed_args = self.parser.parse_args(args)

        # Set team context
        logger.extra['team'] = parsed_args.team

        try:
            if parsed_args.command == "dev":
                return self._handle_dev(parsed_args)
            elif parsed_args.command == "test":
                return self._handle_test(parsed_args)
            elif parsed_args.command == "deploy":
                return self._handle_deploy(parsed_args)
            else:
                self.parser.print_help()
                return 0

        except Exception as e:
            logger.error(f"Command failed: {e}", exc_info=True,
                       extra={'team': parsed_args.team, 'command': parsed_args.command})
            return 1

    def _handle_dev(self, args) -> int:
        \"\"\"Handle development operations.\"\"\"
        logger.info(f"Starting development environment: {args.environment}")
        
        service = CoreService(team="${TEAM}")
        service.initialize_development()
        
        logger.info("Development environment ready")
        return 0

    def _handle_test(self, args) -> int:
        \"\"\"Handle test execution with organization standards.\"\"\"
        import subprocess
        
        test_cmd = ["python", "-m", "pytest", "tests/"]
        
        if args.coverage:
            test_cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
        if not args.slow:
            test_cmd.append("-m", "not slow")
            
        test_cmd.append("--verbose")
        
        result = subprocess.run(test_cmd)
        
        if result.returncode == 0:
            logger.info("All tests passed")
        else:
            logger.error("Tests failed")
            
        return result.returncode

    def _handle_deploy(self, args) -> int:
        \"\"\"Handle deployment with organization procedures.\"\"\"
        logger.info(f"Starting deployment to {args.environment}")
        
        if args.dry_run:
            logger.info("Dry run - no changes will be made")
            return 0
            
        # Organization deployment logic would go here
        logger.info(f"Deployment to {args.environment} completed")
        return 0

def main():
    \"\"\"CLI entry point for organization.\"\"\"
    cli = OrganizationCLI()
    return cli.run()

if __name__ == "__main__":
    sys.exit(main())
PY
  @chmod src/cli.py +x

  services/__init__.py
  services/core.py <<PY
\"\"\"Core services with organization standards.\"\"\"

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..utils.monitoring import MetricsCollector
from ..utils.security import SecurityManager

@dataclass
class ServiceConfig:
    \"\"\"Organization service configuration.\"\"\"
    name: str
    team: str
    environment: str
    version: str = "1.0.0"
    log_level: str = "INFO"
    
    def validate(self):
        \"\"\"Validate configuration against organization standards.\"\"\"
        required_attrs = ['name', 'team', 'environment']
        for attr in required_attrs:
            if not getattr(self, attr):
                raise ValueError(f"Missing required attribute: {attr}")

class CoreService:
    \"\"\"Core service with organization patterns.\"\"\"

    def __init__(self, team: str, environment: str = "development"):
        self.config = ServiceConfig(
            name="${PROJECT_NAME}",
            team=team,
            environment=environment
        )
        self.config.validate()
        
        self.logger = logging.getLogger(__name__)
        self.logger = logging.LoggerAdapter(self.logger, {'team': team})
        self.metrics = MetricsCollector(team=team)
        self.security = SecurityManager()

    def initialize_development(self):
        \"\"\"Initialize development environment.\"\"\"
        self.logger.info("Initializing development environment")
        
        # Setup development-specific configurations
        self._setup_logging()
        self._setup_metrics()
        
        self.logger.info("Development environment initialized")

    def _setup_logging(self):
        \"\"\"Setup organization-standard logging.\"\"\"
        # Organization logging configuration
        pass

    def _setup_metrics(self):
        \"\"\"Setup organization metrics collection.\"\"\"
        self.metrics.initialize()

    def health_check(self) -> Dict[str, Any]:
        \"\"\"Organization-standard health check.\"\"\"
        return {
            "status": "healthy",
            "service": self.config.name,
            "team": self.config.team,
            "environment": self.config.environment,
            "version": self.config.version
        }
PY

  services/data.py <<PY
\"\"\"Data services with organization standards.\"\"\"

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

class DataService:
    \"\"\"Data service following organization patterns.\"\"\"

    def __init__(self, team: str):
        self.team = team
        self.logger = logging.getLogger(__name__)
        self.logger = logging.LoggerAdapter(self.logger, {'team': team})

    def get_team_data(self, filters: Optional[Dict] = None) -> List[Dict]:
        \"\"\"Get team data with organization access patterns.\"\"\"
        self.logger.info(f"Fetching data for team: {self.team}")
        
        # Organization data access logic
        return [
            {
                "id": 1,
                "team": self.team,
                "created_at": datetime.now().isoformat(),
                "data": "sample data"
            }
        ]

    def validate_data_access(self, user_team: str) -> bool:
        \"\"\"Validate data access based on organization policies.\"\"\"
        # Organization access control logic
        allowed_teams = ["${TEAM}", "platform-engineering", "data-team"]
        return user_team in allowed_teams
PY

  models/__init__.py
  models/base.py <<PY
\"\"\"Base models with organization standards.\"\"\"

from typing import Any, Dict
from datetime import datetime
from pydantic import BaseModel as PydanticBaseModel

class BaseModel(PydanticBaseModel):
    \"\"\"Base model with organization standards.\"\"\"
    
    class Config:
        \"\"\"Organization model configuration.\"\"\"
        arbitrary_types_allowed = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        \"\"\"Convert to dictionary with organization standards.\"\"\"
        return self.dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        \"\"\"Create from dictionary with organization standards.\"\"\"
        return cls(**data)
PY

  models/user.py <<PY
\"\"\"User model with organization structure.\"\"\"

from typing import Optional
from datetime import datetime
from .base import BaseModel

class User(BaseModel):
    \"\"\"Organization user model.\"\"\"
    
    id: int
    email: str
    name: str
    team: str
    role: str = "member"
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    def is_team_member(self, team: str) -> bool:
        \"\"\"Check if user belongs to specified team.\"\"\"
        return self.team == team

    def can_access_project(self, project_team: str) -> bool:
        \"\"\"Check if user can access project based on organization rules.\"\"\"
        # Organization access rules
        if self.role == "admin":
            return True
        return self.team == project_team
PY

  utils/__init__.py
  utils/monitoring.py <<PY
\"\"\"Monitoring utilities for organization standards.\"\"\"

import time
from typing import Dict, Any
from functools import wraps

class MetricsCollector:
    \"\"\"Organization metrics collector.\"\"\"

    def __init__(self, team: str):
        self.team = team
        self.metrics: Dict[str, Any] = {}

    def initialize(self):
        \"\"\"Initialize metrics collection.\"\"\"
        self.metrics = {
            "team": self.team,
            "start_time": time.time(),
            "request_count": 0,
            "error_count": 0
        }

    def increment_counter(self, metric: str, value: int = 1):
        \"\"\"Increment counter metric.\"\"\"
        self.metrics[metric] = self.metrics.get(metric, 0) + value

    def record_timing(self, operation: str, duration: float):
        \"\"\"Record timing metric.\"\"\"
        timing_key = f"{operation}_timing"
        self.metrics[timing_key] = duration

def track_operation(operation_name: str):
    \"\"\"Decorator to track operation metrics.\"\"\"
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # In a real implementation, this would send to metrics system
                print(f"[METRICS] {operation_name} completed in {duration:.3f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                print(f"[METRICS] {operation_name} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator
PY

  utils/security.py <<PY
\"\"\"Security utilities for organization standards.\"\"\"

import hashlib
import secrets
from typing import Optional

class SecurityManager:
    \"\"\"Organization security manager.\"\"\"

    def __init__(self):
        self.secret_key = secrets.token_urlsafe(32)

    def hash_data(self, data: str) -> str:
        \"\"\"Hash data using organization standards.\"\"\"
        return hashlib.sha256(data.encode()).hexdigest()

    def validate_access(self, user_team: str, resource_team: str) -> bool:
        \"\"\"Validate access based on organization policies.\"\"\"
        # Organization access control logic
        if user_team == resource_team:
            return True
        # Cross-team access rules
        allowed_cross_teams = {
            "platform-engineering": ["all"],
            "security-team": ["all"]
        }
        return resource_team in allowed_cross_teams.get(user_team, [])
PY

  utils/validation.py <<PY
\"\"\"Validation utilities for organization standards.\"\"\"

import re
from typing import Any, Dict, List

class OrganizationValidator:
    \"\"\"Organization data validator.\"\"\"

    @staticmethod
    def validate_email(email: str) -> bool:
        \"\"\"Validate email against organization standards.\"\"\"
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_team_name(team: str) -> bool:
        \"\"\"Validate team name against organization conventions.\"\"\"
        # Organization team naming conventions
        valid_pattern = r'^[a-z0-9-]+$'
        return bool(re.match(valid_pattern, team)) and len(team) <= 50

    @staticmethod
    def validate_project_data(data: Dict[str, Any]) -> List[str]:
        \"\"\"Validate project data against organization standards.\"\"\"
        errors = []
        
        required_fields = ['name', 'team', 'description']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
                
        if 'team' in data and not OrganizationValidator.validate_team_name(data['team']):
            errors.append("Invalid team name format")
            
        return errors
PY

# ==================== ORGANIZATION TESTING ====================
/tests
  __init__.py

  # Unit tests
  test_services.py <<PY
\"\"\"Tests for organization services.\"\"\"

import pytest
from src.services.core import CoreService, ServiceConfig
from src.services.data import DataService

class TestCoreService:
    \"\"\"Test core service functionality.\"\"\"

    def test_service_initialization(self):
        \"\"\"Test service initialization with organization standards.\"\"\"
        service = CoreService(team="${TEAM}")
        
        assert service.config.team == "${TEAM}"
        assert service.config.name == "${PROJECT_NAME}"
        assert service.config.environment == "development"

    def test_config_validation(self):
        \"\"\"Test configuration validation.\"\"\"
        config = ServiceConfig(
            name="test-service",
            team="${TEAM}",
            environment="testing"
        )
        
        config.validate()  # Should not raise

    def test_config_validation_failure(self):
        \"\"\"Test configuration validation failure.\"\"\"
        config = ServiceConfig(name="", team="", environment="")
        
        with pytest.raises(ValueError):
            config.validate()

class TestDataService:
    \"\"\"Test data service functionality.\"\"\"

    def test_team_data_access(self):
        \"\"\"Test team data access patterns.\"\"\"
        service = DataService(team="${TEAM}")
        data = service.get_team_data()
        
        assert len(data) > 0
        assert data[0]['team'] == "${TEAM}"

    def test_data_access_validation(self):
        \"\"\"Test data access validation.\"\"\"
        service = DataService(team="${TEAM}")
        
        assert service.validate_data_access("${TEAM}") is True
        assert service.validate_data_access("unauthorized-team") is False
PY

  test_models.py <<PY
\"\"\"Tests for organization models.\"\"\"

import pytest
from datetime import datetime
from src.models.user import User

class TestUserModel:
    \"\"\"Test user model functionality.\"\"\"

    def test_user_creation(self):
        \"\"\"Test user creation with organization structure.\"\"\"
        user = User(
            id=1,
            email="user@org.com",
            name="Test User",
            team="${TEAM}",
            created_at=datetime.now()
        )
        
        assert user.email == "user@org.com"
        assert user.team == "${TEAM}"
        assert user.role == "member"
        assert user.is_active is True

    def test_team_membership(self):
        \"\"\"Test team membership checks.\"\"\"
        user = User(
            id=1,
            email="user@org.com", 
            name="Test User",
            team="${TEAM}",
            created_at=datetime.now()
        )
        
        assert user.is_team_member("${TEAM}") is True
        assert user.is_team_member("other-team") is False

    def test_project_access(self):
        \"\"\"Test project access rules.\"\"\"
        user = User(
            id=1,
            email="user@org.com",
            name="Test User", 
            team="${TEAM}",
            role="member",
            created_at=datetime.now()
        )
        
        admin_user = User(
            id=2,
            email="admin@org.com",
            name="Admin User",
            team="platform-engineering", 
            role="admin",
            created_at=datetime.now()
        )
        
        assert user.can_access_project("${TEAM}") is True
        assert user.can_access_project("other-team") is False
        assert admin_user.can_access_project("any-team") is True
PY

  test_utils.py <<PY
\"\"\"Tests for organization utilities.\"\"\"

import pytest
from src.utils.validation import OrganizationValidator
from src.utils.security import SecurityManager

class TestOrganizationValidator:
    \"\"\"Test organization validator.\"\"\"

    def test_email_validation(self):
        \"\"\"Test email validation.\"\"\"
        assert OrganizationValidator.validate_email("user@org.com") is True
        assert OrganizationValidator.validate_email("invalid-email") is False

    def test_team_name_validation(self):
        \"\"\"Test team name validation.\"\"\"
        assert OrganizationValidator.validate_team_name("engineering-team") is True
        assert OrganizationValidator.validate_team_name("Engineering Team") is False
        assert OrganizationValidator.validate_team_name("a" * 51) is False

    def test_project_data_validation(self):
        \"\"\"Test project data validation.\"\"\"
        valid_data = {
            "name": "test-project",
            "team": "engineering-team",
            "description": "A test project"
        }
        
        invalid_data = {
            "name": "",
            "team": "invalid team!",
            "description": ""
        }
        
        assert len(OrganizationValidator.validate_project_data(valid_data)) == 0
        assert len(OrganizationValidator.validate_project_data(invalid_data)) > 0

class TestSecurityManager:
    \"\"\"Test security manager.\"\"\"

    def test_access_validation(self):
        \"\"\"Test access validation.\"\"\"
        security = SecurityManager()
        
        assert security.validate_access("engineering-team", "engineering-team") is True
        assert security.validate_access("engineering-team", "other-team") is False
PY

  # Integration tests
  integration/__init__.py
  integration/test_workflows.py <<PY
\"\"\"Integration tests for organization workflows.\"\"\"

import pytest
from src.services.core import CoreService
from src.services.data import DataService

class TestOrganizationWorkflows:
    \"\"\"Test organization workflows.\"\"\"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_workflow(self):
        \"\"\"Test complete organization workflow.\"\"\"
        # Initialize core service
        core_service = CoreService(team="${TEAM}")
        core_service.initialize_development()
        
        # Initialize data service
        data_service = DataService(team="${TEAM}")
        data = data_service.get_team_data()
        
        # Verify workflow results
        assert core_service.config.team == "${TEAM}"
        assert len(data) > 0
        assert data[0]['team'] == "${TEAM}"
        
        # Health check
        health = core_service.health_check()
        assert health['status'] == 'healthy'
        assert health['team'] == "${TEAM}"
PY

  conftest.py <<PY
\"\"\"Organization test configuration.\"\"\"

import pytest
import logging
from typing import Generator

@pytest.fixture(autouse=True)
def setup_organization_testing():
    \"\"\"Setup organization testing environment.\"\"\"
    # Set organization test environment
    import os
    os.environ["ORGANIZATION"] = "${ORGANIZATION}"
    os.environ["TEAM"] = "${TEAM}"
    os.environ["ENVIRONMENT"] = "testing"
    
    # Configure test logging
    logging.basicConfig(level=logging.WARNING)
    
    yield
    
    # Cleanup
    for env_var in ["ORGANIZATION", "TEAM", "ENVIRONMENT"]:
        if env_var in os.environ:
            del os.environ[env_var]
PY

# ==================== ORGANIZATION SCRIPTS ====================
/scripts
  setup-org.sh <<SH
#!/usr/bin/env bash
# Organization Project Setup Script

echo "🏢 ${ORGANIZATION} - Project Setup"
echo "==================================="

# Organization requirements check
echo "🔍 Checking organization requirements..."

# Check for organization tools
command -v docker >/dev/null 2>&1 || echo "⚠️  Docker not found (required for org)"
command -v kubectl >/dev/null 2>&1 || echo "⚠️  kubectl not found (required for org)"
command -v terraform >/dev/null 2>&1 || echo "⚠️  Terraform not found (required for org)"

# Setup virtual environment
echo "🐍 Setting up Python environment..."
python -m venv .venv
source .venv/bin/activate

# Install with organization dependencies
echo "📦 Installing organization dependencies..."
pip install -e ".[dev,org]"

# Organization-specific setup
echo "⚙️  Running organization setup..."
python -c "
from src.services.core import CoreService
service = CoreService(team='${TEAM}', environment='development')
service.initialize_development()
print('✅ Organization service initialized')
"

echo "🎯 Organization project setup complete!"
echo ""
echo "📋 Next Steps:"
echo "   1. Update config/organization.yaml with your settings"
echo "   2. Review .github/ workflows for CI/CD"
echo "   3. Join Slack channel: ${SLACK_CHANNEL}"
echo "   4. Contact team: ${MAINTAINER_TEAM}"
SH
  @chmod scripts/setup-org.sh +x

  test-org.sh <<SH
#!/usr/bin/env bash
# Organization Test Suite

echo "🧪 ${ORGANIZATION} Test Suite"
echo "============================="

# Run unit tests
echo "📝 Running unit tests..."
python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Run integration tests (slow)
echo "🔗 Running integration tests..."
python -m pytest tests/integration/ -v -m integration

# Organization-specific checks
echo "🏢 Organization standards check..."
python -m flake8 src/ --max-complexity=12
python -m mypy src/ --strict
python -m black --check src/ tests/

# Security scan
echo "🔒 Organization security scan..."
python -m bandit -r src/ -f json -o reports/security-scan.json

echo "✅ Organization test suite completed!"
SH
  @chmod scripts/test-org.sh +x

  deploy-org.sh <<SH
#!/usr/bin/env bash
# Organization Deployment Script

ENVIRONMENT=${1:-staging}
TEAM="${TEAM}"

echo "🚀 ${ORGANIZATION} Deployment"
echo "============================="

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "💡 Use: staging or production"
    exit 1
fi

echo "👥 Deployment Team: $TEAM"
echo "🌍 Environment: $ENVIRONMENT"

# Pre-deployment checks
echo "🔍 Pre-deployment checks..."
./scripts/test-org.sh

# Organization deployment process
echo "📦 Deploying to $ENVIRONMENT..."

case $ENVIRONMENT in
    staging)
        echo "🔄 Deploying to staging environment..."
        kubectl apply -f deploy/kubernetes/staging/
        ;;
    production)
        echo "🎯 Deploying to production environment..."
        # Additional production checks
        echo "🔒 Running production security scan..."
        python -m bandit -r src/ -ll
        kubectl apply -f deploy/kubernetes/production/
        ;;
esac

# Post-deployment verification
echo "✅ Verifying deployment..."
kubectl get deployments -l team=$TEAM

echo "🎉 Deployment to $ENVIRONMENT completed successfully!"
echo "📊 Monitor in organization dashboard"
SH
  @chmod scripts/deploy-org.sh +x

# ==================== ORGANIZATION CONFIGURATION ====================
/config
  organization.yaml <<YAML
# Organization Configuration
organization: "${ORGANIZATION}"
team: "${TEAM}"
project: "${PROJECT_NAME}"

# Team Settings
slack_channel: "${SLACK_CHANNEL}"
maintainer_team: "${MAINTAINER_TEAM}"
code_owners: "${CODE_OWNERS}"

# Development Standards
python_version: "${PYTHON_VERSION}"
code_style: "black"
testing_framework: "pytest"
logging_format: "structured"

# Deployment
environments:
  - development
  - staging  
  - production

kubernetes:
  namespace: "${TEAM}"
  team_label: "${TEAM}"

compliance:
  security_scan: true
  code_review: true
  automated_testing: true
YAML

  development.yaml <<YAML
# Development Configuration
environment: development
debug: true
log_level: DEBUG

database:
  host: localhost
  port: 5432
  name: ${PROJECT_NAME}_dev

features:
  monitoring: true
  security: false
  caching: false
YAML

# ==================== ORGANIZATION DEPLOYMENT ====================
/deploy
  /kubernetes
    /staging
      deployment.yaml <<YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${PROJECT_NAME}
  namespace: ${TEAM}
  labels:
    app: ${PROJECT_NAME}
    team: ${TEAM}
    environment: staging
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ${PROJECT_NAME}
  template:
    metadata:
      labels:
        app: ${PROJECT_NAME}
        team: ${TEAM}
    spec:
      containers:
      - name: ${PROJECT_NAME}
        image: ${ORGANIZATION}/${PROJECT_NAME}:staging
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "staging"
        - name: TEAM
          value: "${TEAM}"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
YAML

    /production
      deployment.yaml <<YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${PROJECT_NAME}
  namespace: ${TEAM}
  labels:
    app: ${PROJECT_NAME}
    team: ${TEAM}
    environment: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ${PROJECT_NAME}
  template:
    metadata:
      labels:
        app: ${PROJECT_NAME}
        team: ${TEAM}
    spec:
      containers:
      - name: ${PROJECT_NAME}
        image: ${ORGANIZATION}/${PROJECT_NAME}:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: TEAM
          value: "${TEAM}"
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
YAML

# ==================== ORGANIZATION GITHUB ====================
/.github
  /workflows
    organization-ci.yml <<YAML
name: Organization CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run organization tests
      run: ./scripts/test-org.sh
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Security scan
      run: |
        pip install bandit safety
        bandit -r src/ -f json -o security-report.json
        safety check --json --output safety-report.json
    
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          security-report.json
          safety-report.json
YAML

  CODEOWNERS <<TXT
# Organization Code Owners
* ${CODE_OWNERS}

# Team-specific ownership
/src/services/ @org/platform-engineering
/deploy/ @org/devops-team
/.github/ @org/platform-engineering
TXT

  pull_request_template.md <<MD
# Organization Pull Request

## Description
<!-- Describe your changes -->

## Team
- **Team:** ${TEAM}
- **JIRA:** ${JIRA_PROJECT}-<!-- issue-number -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Checklist
- [ ] Code follows organization standards
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Security considerations addressed
- [ ] CI/CD checks passing

## Deployment Notes
<!-- Any special deployment instructions -->

## Screenshots
<!-- If UI changes -->

/label ~"${TEAM}"
/cc ${CODE_OWNERS}
MD

# ==================== ORGANIZATION COMPLIANCE ====================
/compliance
  security-policy.md <<MD
# Organization Security Policy

## Overview
**Organization:** ${ORGANIZATION}
**Team:** ${TEAM}
**Project:** ${PROJECT_NAME}

## Security Requirements

### Code Security
- [ ] All code must pass SAST scanning
- [ ] Dependencies must be vulnerability-free
- [ ] Secrets must not be committed
- [ ] Input validation required

### Access Control
- [ ] Team-based access enforcement
- [ ] Principle of least privilege
- [ ] Regular access reviews

### Monitoring
- [ ] Security event logging
- [ ] Anomaly detection
- [ ] Incident response plan

## Compliance
This project follows organization security standards and undergoes regular security reviews.

## Contact
**Security Team:** ${MAINTAINER_TEAM}
**Slack:** ${SLACK_CHANNEL}
MD

# ==================== ORGANIZATION DOCUMENTATION ====================
/docs
  README.md <<MD
# ${PROJECT_NAME}

> **Organization Edition**

${DESCRIPTION}

## 🏢 Organization Information

- **Organization:** ${ORGANIZATION}
- **Team:** ${TEAM}
- **Maintainers:** ${MAINTAINER_TEAM}
- **Slack:** ${SLACK_CHANNEL}

## 🚀 Quick Start

\`\`\`bash
# Generate organization project
lrc schema_org_example.lrc -o ./${PROJECT_NAME}
cd ${PROJECT_NAME}

# Setup organization environment
./scripts/setup-org.sh

# Run organization tests
./scripts/test-org.sh
\`\`\`

## 📁 Organization Structure

\`\`\`
${PROJECT_NAME}/
├── src/           # Source code with org standards
│   ├── services/  # Organization services
│   ├── models/    # Data models
│   └── utils/     # Organization utilities
├── tests/         # Comprehensive test suite
├── deploy/        # Deployment configurations
├── config/        # Organization settings
├── .github/       # CI/CD workflows
├── compliance/    # Security & compliance
└── scripts/       # Organization scripts
\`\`\`

## 🔧 Organization Features

- **Team-based architecture** with proper separation
- **Organization standards** for code quality
- **Security compliance** with policies and scanning
- **CI/CD workflows** with organization checks
- **Monitoring ready** with team context
- **Deployment configurations** for multiple environments

## 👥 Team Collaboration

### Development Workflow
\`\`\`bash
# Start development
${PROJECT_NAME} dev

# Run organization tests
./scripts/test-org.sh

# Deploy to staging
./scripts/deploy-org.sh staging
\`\`\`

### Code Review
- All changes require code review
- Follow organization coding standards
- Include appropriate tests
- Update documentation as needed

## 🔒 Security & Compliance

### Security Practices
- Regular security scanning
- Dependency vulnerability monitoring
- Access control enforcement
- Security event logging

### Compliance Requirements
- Follow organization security policy
- Regular security reviews
- Incident response readiness
- Data protection compliance

## 📊 Monitoring & Operations

### Health Checks
\`\`\`bash
# Service health
${PROJECT_NAME} health

# Team-specific metrics
${PROJECT_NAME} metrics --team ${TEAM}
\`\`\`

### Deployment
\`\`\`bash
# Staging deployment
./scripts/deploy-org.sh staging

# Production deployment  
./scripts/deploy-org.sh production
\`\`\`

## 🤝 Contributing

### Organization Standards
1. Follow team coding conventions
2. Include comprehensive tests
3. Update documentation
4. Pass security scans
5. Get appropriate reviews

### Communication
- **Slack:** ${SLACK_CHANNEL}
- **Email:** ${MAINTAINER_TEAM}
- **Code Owners:** ${CODE_OWNERS}

## 📄 License

${LICENSE} License - see [LICENSE](../LICENSE) for details.

---

*Built for ${ORGANIZATION} by ${TEAM} 🏢*
MD

  TEAM_GUIDE.md <<MD
# Team Development Guide

## 🎯 Team Standards

### Code Organization
- Use team-specific namespaces
- Follow organization naming conventions
- Implement proper error handling
- Include comprehensive logging

### Testing Strategy
- Unit tests for all business logic
- Integration tests for workflows
- Performance tests for critical paths
- Security tests for data access

### Deployment Process
1. **Development** - Local testing
2. **Staging** - Team validation
3. **Production** - Organization deployment

## 🔧 Team Tools

### Development
\`\`\`bash
# Team development setup
./scripts/setup-org.sh

# Team-specific testing
./scripts/test-org.sh

# Team deployment
./scripts/deploy-org.sh staging
\`\`\`

### Monitoring
- Team-specific dashboards
- Custom metrics collection
- Alerting for team services
- Performance monitoring

## 👥 Collaboration

### Code Review
- Review within 24 hours
- Provide constructive feedback
- Verify organization standards
- Check security considerations

### Communication
- Daily standups in ${SLACK_CHANNEL}
- Weekly team meetings
- Monthly organization reviews
- Incident response coordination

## 🚀 Best Practices

### Development
- Small, focused PRs
- Comprehensive testing
- Clear documentation
- Security-first approach

### Operations
- Monitor team services
- Respond to incidents
- Regular performance reviews
- Capacity planning

## 📞 Support

### Team Support
- **Slack:** ${SLACK_CHANNEL}
- **Email:** ${MAINTAINER_TEAM}
- **On-call:** Team rotation

### Organization Support
- Platform engineering team
- Security team
- DevOps team
MD

# ==================== ORGANIZATION PROJECT FILES ====================
.gitignore <<GIT
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.mypy_cache/
.pytest_cache/

# Virtual environment
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Organization
.coverage
htmlcov/
reports/
secrets.txt
*.local.*
.env.local
GIT

LICENSE <<TXT
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

[Full Apache 2.0 License Text - Same as enterprise template]

END OF TERMS AND CONDITIONS
TXT

pyproject.toml <<TOML
[project]
name = "${PROJECT_NAME}"
version = "1.0.0"
description = "${DESCRIPTION}"
readme = "README.md"
requires-python = ">=${PYTHON_VERSION}"
authors = [
    { name = "${ORGANIZATION}", email = "${MAINTAINER_TEAM}" }
]
keywords = ["organization", "team", "enterprise", "collaboration"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Libraries :: Application Frameworks",
]

dependencies = [
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "bandit>=1.7.0",
]
org = [
    "requests>=2.31.0",
    "pyyaml>=6.0",
]

[project.scripts]
${PROJECT_NAME} = "src.cli:main"

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py39']

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "--verbose --strict-markers --strict-config"
testpaths = ["tests"]
pythonpath = ["src"]
markers = [
    "slow: slow tests",
    "integration: integration tests",
]
TOML

README.md <<MD
# ${PROJECT_NAME}

${DESCRIPTION}

## 🏢 Organization Ready

This template is designed for teams and organizations that need:
- **Structured collaboration** with clear team boundaries
- **Organization standards** for code quality and security
- **Scalable architecture** that grows with your team
- **Compliance ready** with security policies and procedures

## 🚀 Organization Quick Start

\`\`\`bash
# Generate organization project
lrc schema_org_example.lrc -o ./${PROJECT_NAME}
cd ${PROJECT_NAME}

# Setup organization environment
./scripts/setup-org.sh

# Verify organization standards
./scripts/test-org.sh
\`\`\`

## 📁 Organization Structure

\`\`\`
${PROJECT_NAME}/
├── src/           # Team-based source code
├── tests/         # Comprehensive testing
├── deploy/        # Multi-environment deployment
├── config/        # Organization configuration
├── .github/       # CI/CD with org checks
├── compliance/    # Security & policies
├── scripts/       # Organization workflows
└── docs/          # Team documentation
\`\`\`

## 🔧 Built for Teams

- **Team-based services** with proper separation
- **Organization utilities** for common patterns
- **Security compliance** with built-in scanning
- **CI/CD workflows** with organization gates
- **Monitoring ready** with team context

## 👥 Team Collaboration

### Development Workflow
\`\`\`bash
# Team development
${PROJECT_NAME} dev --team ${TEAM}

# Organization testing
./scripts/test-org.sh

# Team deployment
./scripts/deploy-org.sh staging
\`\`\`

### Code Review & Standards
- All changes require team review
- Follow organization coding standards
- Include comprehensive tests
- Pass security scans

## 📄 License

${LICENSE} License - see [LICENSE](LICENSE) for details.

---

*Built for ${ORGANIZATION} teams to collaborate effectively 🏢*
MD

# ==================== END OF ORGANIZATION SCHEMA ====================
# This schema is designed for teams and organizations
# Generate with: lrc schema_org_example.lrc -o ./org-project
# Follow organization standards and team collaboration practices

# Built for scalable, maintainable team development! 🏢


FILE: install_deps.sh
Kind: text
Size: 8533
Last modified: 2026-01-21T07:58:23Z

CONTENT:
#!/bin/bash
# LRC dependency installer - cross-platform support

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[LRC]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Detect platform
detect_platform() {
    case "$(uname -s)" in
        Linux*)
            if [[ -f /proc/version && $(grep -i microsoft /proc/version) ]]; then
                echo "wsl"
            elif [[ -d /data/data/com.termux ]]; then
                echo "termux"
            elif [[ $(uname -o) == "Android" ]]; then
                echo "android"
            else
                echo "linux"
            fi
            ;;
        Darwin*)
            echo "macos"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            echo "windows"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install system dependencies
install_system_deps() {
    local platform=$1
    
    case $platform in
        linux)
            if command_exists apt; then
                log "Installing Ubuntu/Debian dependencies..."
                sudo apt update && sudo apt install -y \
                    python3 \
                    python3-pip \
                    python3-venv \
                    git \
                    libmagic1 \
                    fonts-powerline
            elif command_exists dnf; then
                log "Installing Fedora/RHEL dependencies..."
                sudo dnf install -y \
                    python3 \
                    python3-pip \
                    python3-virtualenv \
                    git \
                    file-devel \
                    powerline-fonts
            elif command_exists pacman; then
                log "Installing Arch Linux dependencies..."
                sudo pacman -S --noconfirm \
                    python \
                    python-pip \
                    git \
                    libmagic \
                    powerline-fonts
            elif command_exists zypper; then
                log "Installing openSUSE dependencies..."
                sudo zypper install -y \
                    python3 \
                    python3-pip \
                    git \
                    python3-virtualenv \
                    file-devel
            else
                warn "Unknown package manager - please install Python 3.8+ and git manually"
            fi
            ;;
            
        wsl)
            log "Installing WSL dependencies..."
            if command_exists apt; then
                sudo apt update && sudo apt install -y \
                    python3 \
                    python3-pip \
                    python3-venv \
                    git \
                    libmagic1 \
                    fonts-powerline
            else
                warn "Unknown package manager in WSL"
            fi
            ;;
            
        termux)
            log "Installing Termux dependencies..."
            pkg update && pkg install -y \
                python \
                git \
                libmagic
            ;;
            
        macos)
            if command_exists brew; then
                log "Installing macOS dependencies via Homebrew..."
                brew install \
                    python@3 \
                    git \
                    libmagic
            else
                warn "Homebrew not found - please install Python 3.8+ and git manually"
                info "To install Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            fi
            ;;
            
        windows)
            log "Windows detected - please ensure you have:"
            info "  - Python 3.8+ (from Microsoft Store or python.org)"
            info "  - Git for Windows (from git-scm.com)"
            info "  - Windows Terminal (recommended)"
            return 0
            ;;
            
        *)
            warn "Unknown platform - please install dependencies manually"
            return 1
            ;;
    esac
}

# Setup Python environment
setup_python_env() {
    local with_venv=$1
    
    if [[ $with_venv == "yes" ]]; then
        log "Creating Python virtual environment..."
        python3 -m venv .venv
        source .venv/bin/activate
        
        if [[ $platform == "windows" ]]; then
            source .venv/Scripts/activate
        fi
    fi
    
    log "Installing LRC package..."
    pip install -e .
    
    if [[ -f "requirements.txt" ]]; then
        log "Installing runtime dependencies..."
        pip install -r requirements.txt
    fi
}

# Setup shell integration
setup_shell_integration() {
    local platform=$1
    
    log "Setting up shell integration..."
    
    # Detect shell
    local shell_name=$(basename "$SHELL")
    local rc_file=""
    
    case $shell_name in
        bash)
            rc_file="$HOME/.bashrc"
            ;;
        zsh)
            rc_file="$HOME/.zshrc"
            ;;
        fish)
            rc_file="$HOME/.config/fish/config.fish"
            mkdir -p "$(dirname "$rc_file")"
            ;;
        *)
            warn "Unknown shell $shell_name - please add LRC to PATH manually"
            return 1
            ;;
    esac
    
    if [[ -n "$rc_file" ]]; then
        # Get the directory where LRC is installed
        local lrc_dir=$(pwd)
        local bin_dir="$lrc_dir/.venv/bin"  # If using venv
        
        if [[ -d "$bin_dir" ]]; then
            local path_cmd=""
            
            case $shell_name in
                bash|zsh)
                    path_cmd="export PATH=\"$bin_dir:\$PATH\""
                    ;;
                fish)
                    path_cmd="set -gx PATH \"$bin_dir\" \$PATH"
                    ;;
            esac
            
            if [[ -n "$path_cmd" ]]; then
                if ! grep -q "$bin_dir" "$rc_file" 2>/dev/null; then
                    echo -e "\n# LRC - Local Repo Compile" >> "$rc_file"
                    echo "$path_cmd" >> "$rc_file"
                    log "Added LRC to $rc_file"
                else
                    info "LRC already in PATH in $rc_file"
                fi
            fi
        fi
    fi
}

# Verify installation
verify_installation() {
    log "Verifying installation..."
    
    # Try to run lrc with --version
    if command_exists lrc; then
        if lrc --version >/dev/null 2>&1; then
            log "LRC installed successfully!"
            return 0
        fi
    fi
    
    # Fallback: try Python module
    if python -c "import lrc; print(lrc.__version__)" >/dev/null 2>&1; then
        log "LRC Python package installed successfully!"
        info "You can run it with: python -m lrc"
        return 0
    fi
    
    error "Installation verification failed"
    return 1
}

# Main installation function
main() {
    local with_venv="no"
    local platform=$(detect_platform)
    
    log "LRC Dependency Installer"
    info "Platform: $platform"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --with-venv)
                with_venv="yes"
                shift
                ;;
            *)
                warn "Unknown option: $1"
                shift
                ;;
        esac
    done
    
    # Install system dependencies
    install_system_deps "$platform"
    
    # Setup Python environment
    setup_python_env "$with_venv"
    
    # Setup shell integration
    setup_shell_integration "$platform"
    
    # Verify installation
    if verify_installation; then
        log "🎉 LRC is ready to use!"
        info "Quick start:"
        info "  lrc --help                          # Show help"
        info "  lrc examples/schema_example.lrc     # Run example"
        
        if [[ $with_venv == "yes" ]]; then
            info "Remember to activate virtual environment:"
            if [[ $platform == "windows" ]]; then
                info "  .venv\\Scripts\\activate"
            else
                info "  source .venv/bin/activate"
            fi
        fi
    else
        error "Installation completed with issues"
        error "Please check the output above and fix any errors"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"


FILE: jadis_publickey.asc
Kind: text
Size: 3216
Last modified: 2026-01-21T07:58:23Z

CONTENT:
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQINBGj60tEBEADU16rLe2aGRI24MWNLPwiMzleumN8byevl/fCinHIt6TomD9vF
nftIn+bLq6rvIbcTcSU+v/KAOL9Xl2tXc+GbXI71jv81hBFvEj9ZmKK/MEVh32Lj
2DU5N8N2WbCUsQj7pHNhpu+ZxzHNNpLrFQR9fd0SN+3QHugu9kyqPsleuxVFQvnI
7L9TdHNvbB8cjOa69T1wpLaMgOgA3klW9kGaMtIvr3Hb2c6phYMRqiSX2mO9O/X6
G9HGLFjs1S0+MvTzNDvULIDSPza6lNlWDdbqRfpJu9PdqpzalxGpDCHq0vXHxoV0
xR6Ep1fnxxKbWYq8m2tC4J0HXVRh15obAppIRy4E2iseovULRvV54bWm0QAmekqS
+0KYP6LGq9++SwJPnj9z+ZGswuRWPwAZP3zzZRtMSEt7A1rItKGGnYyFgXs4qu0L
wFBhE9I5M5CqKukrpKWjSd+msSX1YZYQseSdDynNv0wklLAHq25P0fmmLxQfmX8c
6ReRwjEfJPcTUHjCOuOHxjPhKUvr+eza6Qcoqhs3TTReq0nKSCIpGtzL6c1LLRY3
2TdSrUdR33vgPWMLEHdhR3o/XEPBFHCpFOnJ7LUAfa62GtCwdkpqC2XvEhS/ZkkX
2/qFQaAxYt556zhyzvSAniOYq5NMXPvvxnd6Xha0LoqYdGCWV/FaiEwGfwARAQAB
tFJ+SkFESVMgfCBKdXN0YWR1ZGVpbnNwYWNlIChNYWtpbmcgSW1wb3NzaWJsZSBQ
b3NzaWJsZS4pIDx0aGVvdXRlcnZvaWRAb3V0bG9vay5jb20+iQJUBBMBCgA+FiEE
RHymoPHfp2qcbsJgKcCAMn2ygHEFAmj60tECGwMFCQHhM4AFCwkIBwIGFQoJCAsC
BBYCAwECHgECF4AACgkQKcCAMn2ygHEigQ//Sa/AwGdET7O0krQUo0ZlkjUKwJu5
XPBQHZUE75y/XYx1JT5TfuJie+0k67833DefE36ysP3NxazrdSUzPHowokW59m1H
h/AQol4lWPgPoBqivcsqjU3kl/IZOu+JBGcKWkewAW0nABl1hZBCayJLYsLFRuoB
ICUxOqQHs2yXISt3ryMe9D3ivq3JCmp5+b0Y23kPTxBkQVlWicocozlqojyD6hYN
je+mLMvYjeVIbugqaVp9ehtK18khzleP6ysCR06aXmP+RRteKx6PqWCfamD9mmxz
glo5DPpyBMySFUMXUFMvfMjia2jq7YkBDHvkSxMC/X9y2ljrqx2P/S1eh9eULo5j
0YaPjMGtPaoX7VyekZy4KCE6j+DGFcDdruqyRiv/oUAHi94rQ2IjvT6ipkEYSX3y
HqUc4uNlgQsntlOzD71r3yNlHBNlg9WliiNjb+U7/me9C3H5GlHyu0zVvh2dZ1sp
YqN9GS5m6FTfdXLHryJeWjTBfyXsPspJQxYYbLze9Fc2E6U0O3u0us/RKo35mK7i
PZb4gLxDnCzpvKtdUuh0N3N8QxEME7iXyUS5NDmdBWx25iB7hdvtRUpftCfdj4J/
Mqg+LF9ieJ7/QtOnD/Ac6f2DtweROJrZNTRLTnjcZC411Q7EtQVsz7e8H1mz5AAp
Jv2AnlfBTbQ5yy65Ag0EaPrS0QEQALnzhoOzga1fSye2qcEDnOr1HlcFdQrH/bH+
dah/j3PBLHrjQUzV7a1pUZ7rbd3QIjMNqahLFJgvh2Oe18ALfrgzaJk/SRU9Ixj4
ooy6/kM71HA7A5IaaVV9N9soK+0MiLFuaJTGIL0pVeelBVwrIHytPYGIyEKujE5h
tx+VVvEzut5s+tc+jB4uc+jl0ZYAdbmI0DWOjYteEWULiN5NZg1eNXQtYIVB4bar
rYcgx6WL69/GlViUMLG2sgpRDFeetOhRjXQXfY/pl1+a9/C7DV1aOO1XMIeYhoUd
H+gg/8iFBXIVID1QRKH/FGEP+AvjjcvVrRUxLJCUAXZX1JGaatWwtxrkaiVRssOS
ihnHSNrySLWPod4d+T2Y3qpi4KcPIbcrU9kYua4tsONZmId3fkK7y/0Ifa1CrHd5
4ExX7mGySeFUO1YItGqWA8WoZkQgnD9eMSw5sYXUJjB1iCk1q0Xjvf6PC+uaUKY8
jzOt57Zap51HprUZKoJD+CqiIj9fH90xgfo2T8yymEFnSR/iB3ENTvbG2yZZry18
eTy3BYsDij6fL/SuKsFlRsIpk6OKZHn0UW0Qs1qnodZKZQ8lPf3bI4A17ph14XJZ
1ac1dF3DkhG90GttOBzlJF4LkmvvJ6ZHJM2bEEXeauz/DYoGqn9WP8FSGV5pOtJH
7qQbTPQ1ABEBAAGJAjwEGAEKACYWIQREfKag8d+napxuwmApwIAyfbKAcQUCaPrS
0QIbDAUJAeEzgAAKCRApwIAyfbKAcRuBD/sEVY3qkx0h+saRmVQxugN+y6znScUy
NSsAqcCVj4Z/zomdNdkIcomfeThPOJ1UACqqw/Q7UxSeFpF/yGV0Hc3aaKiqExcO
oKvoGah15WipxOTYicK02ekvoVoctYkSgb5bE9fzLiFike9V8RUQWeiOTfqLsy01
qsFeVq3FOaM3LQKTpTHECYaM6fIYge/dq64vCidESXvzfA3+YUdAPwLHVRoa0+fg
6jES7DAZ+iK6C8xv6/1dlM9GFJf1LV1oaaF1mmONE7zCgSH6rSr/0afQhFgnw3ry
A4hJVRyl9zwrGlt3HYazQ5X29Hj0E39oy9YcVxy3O3/7wiMXs8RIVfEWXvJJT9/R
oU5A2CW4Ut+7WyWFdzSVVig6yCVIJMsX7sVJcGS0lVf7ek0U6cFIHInofe2p4uVR
DquyHw0lb1LgRDvfbphHflmwtTajT01Op8hSBEqHtV1a8znGl+GNq+rJeH+CoZVP
YCawUqxt4p8z/OgdCEJLxcazKxLFu5MTQegO/FEGVzlrr2mZ7C0GPDOYM5h23JAt
6DMUlPbtIH469edniD77APv47/LFNUouZYTbjnsrUQoB+k6j7kiANalkIxPWFZje
X5Ec7YV7WKoVW9jzhZbZcEBNBPfv/w60AqCFhRJA7CQHT+ViJ+olM/TgBrG00239
Ez5ivAe7gbnoeA==
=io3E
-----END PGP PUBLIC KEY BLOCK-----


FILE: lrc
Kind: text
Size: 11478
Last modified: 2026-01-21T07:58:23Z

CONTENT:
#!/usr/bin/env python3
"""
lrc — Local Repo Compile
Build a local repo from a declarative text schema.

Cross-platform support for: Android/Termux, Android/Linux, Linux, WSL2, macOS, Windows

Schema example (repo_example.lrc):

# Project: myapp
# Description: Minimal Python CLI
# Version: 0.1.0

@set AUTHOR=Justadudeinspace
@template python-cli
/src
  main.py -> print("Hello ${AUTHOR}")
  utils.py
/docs
  README.md <<EOF
# MyApp CLI
Author: ${AUTHOR}
EOF
/tests
  test_main.py
.gitignore -> __pycache__/
requirements.txt -> requests
@chmod src/main.py +x
@ignore node_modules .venv

Usage:
  lrc repo_example.lrc
  lrc repo_example.lrc -o ./outdir
  lrc repo_example.lrc --dry-run
  lrc repo_example.lrc -f  # overwrite existing files
  lrc --bootstrap          # install to ~/.local/bin (or Termux bin) and wire PATH

Options:
  -n, --dry-run    Preview actions; do not write.
  -f, --force      Overwrite files if they already exist.
  -o, --out DIR    Output root. Defaults to "./<ProjectName>" if present, else platform default.
  -v, --verbose    Extra logs.
  -b, --bootstrap  Install lrc into user bin and persist PATH.
  --version        Show version info.

Notes:
- Indentation defines nesting (spaces). Deeper indent = child of previous directory.
- Lines starting with "#" are comments/metadata. Recognized keys: "Project", "Description", "Version".
- Lines starting with "@" are directives (tags). See below.
- Absolute sections begin with "/" (e.g., "/src").
- "name -> CONTENT" creates a file with inline one-line content.
- "name <<EOF" ... "EOF" creates a file with multi-line content (heredoc; custom delimiter supported).
- "name" (without arrow) creates an empty file.
- Directories end with "/" (e.g., "assets/").
- Variables: use @set KEY=VALUE, then reference with ${KEY} in file paths and contents.
"""

from __future__ import annotations
import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional, Dict

# Import from the package
try:
    from lrc.core import (
        parse_schema, 
        realize, 
        get_default_output_dir, 
        print_platform_info,
        do_bootstrap,
        ParseError,
        __version__
    )
except ImportError:
    # Fallback to direct import for development
    import sys
    sys.path.insert(0, str(Path(__file__).parent / 'src'))
    from lrc.core import (
        parse_schema, 
        realize, 
        get_default_output_dir, 
        print_platform_info,
        do_bootstrap,
        ParseError,
        __version__
    )


def extract_project_metadata(schema_text: str) -> dict:
    """Extract project metadata from schema comments."""
    metadata = {
        "Project": None,
        "Description": None, 
        "Version": None
    }
    
    for line in schema_text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            # Remove comment markers and clean up
            content = line.lstrip("#").strip()
            for key in metadata.keys():
                if content.lower().startswith(f"{key.lower()}:"):
                    metadata[key] = content.split(":", 1)[1].strip()
                    break
                    
    return metadata


def safe_read_schema(schema_path: Path) -> str:
    """Safely read schema file with proper error handling."""
    try:
        return schema_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Try other common encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                return schema_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Cannot decode schema file: {schema_path}")
    except Exception as e:
        raise ValueError(f"Cannot read schema file {schema_path}: {e}")


def validate_output_directory(out_dir: Path, force: bool = False) -> bool:
    """Validate that output directory is safe and writable."""
    try:
        # Check if directory exists and has content
        if out_dir.exists() and any(out_dir.iterdir()):
            if not force:
                print(f"[WARNING] Output directory '{out_dir}' exists and is not empty")
                print("  Use --force to overwrite files, or choose a different directory with -o")
                return False
            else:
                print(f"[INFO] Output directory '{out_dir}' exists, --force enabled")
        return True
    except Exception as e:
        print(f"[ERROR] Cannot access output directory '{out_dir}': {e}")
        return False


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point with enhanced error handling and user experience."""
    
    parser = argparse.ArgumentParser(
        prog="lrc",
        description="Local Repo Compile — build a repo from a declarative schema file. Cross-platform.",
        epilog="""
Examples:
  lrc schema.lrc                 # Generate project
  lrc schema.lrc -o ./myproject  # Custom output directory  
  lrc schema.lrc --dry-run       # Preview only
  lrc schema.lrc --force         # Overwrite existing
  lrc --bootstrap                # Install system-wide

Schema Language:
  # Project: Name              # Metadata comments
  @set VAR=value              # Define variables
  dir/                        # Create directory
  file.txt -> content         # Inline file content
  file.txt <<EOF              # Heredoc multi-line content
  ...content...
  EOF
  /absolute/path              # Absolute directory
  @template python-cli        # Apply template
  @chmod script.py +x         # Set permissions
  @ignore pattern             # Ignore files

Templates: python-cli, node-cli, rust-cli
Platforms: Linux, macOS, Windows, WSL2, Android/Termux
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "schema", 
        nargs="?", 
        help="Path to schema file (e.g., myproject.lrc)"
    )
    
    parser.add_argument(
        "-o", "--out", 
        help="Output root directory (default: platform-appropriate location)"
    )
    
    parser.add_argument(
        "-n", "--dry-run", 
        action="store_true",
        help="Preview actions without writing"
    )
    
    parser.add_argument(
        "-f", "--force", 
        action="store_true",
        help="Overwrite files if they exist"
    )
    
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "-b", "--bootstrap", 
        action="store_true",
        help="Install lrc into user bin and wire PATH"
    )
    
    parser.add_argument(
        "--platform-info",
        action="store_true", 
        help="Show detailed platform information"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"lrc {__version__}"
    )

    # Parse arguments
    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)

    # Handle bootstrap command
    if args.bootstrap:
        try:
            do_bootstrap(sys.argv[0], verbose=args.verbose)
            print("[SUCCESS] lrc installed successfully!")
            print("[INFO] You may need to restart your terminal or run: source ~/.bashrc")
            return 0
        except Exception as e:
            print(f"[ERROR] Bootstrap failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

    # Handle platform info
    if args.platform_info:
        print_platform_info(verbose=True)
        return 0

    # Validate schema argument
    if not args.schema:
        parser.print_help()
        print("\n[ERROR] No schema file specified")
        print("[INFO]  Example: lrc myproject.lrc")
        return 2

    # Read and validate schema file
    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(f"[ERROR] Schema file not found: {schema_path}")
        print("[INFO]  Check the file path and try again")
        return 2

    try:
        schema_text = safe_read_schema(schema_path)
    except Exception as e:
        print(f"[ERROR] {e}")
        return 2

    # Extract project metadata for better defaults
    metadata = extract_project_metadata(schema_text)
    project_name = metadata["Project"]

    # Determine output directory
    if args.out:
        out_root = Path(args.out).resolve()
    else:
        out_root = get_default_output_dir(project_name).resolve()

    # Validate output directory
    if not validate_output_directory(out_root, args.force):
        return 1

    # Platform info for debugging
    if args.verbose:
        print_platform_info(verbose=True)
        print(f"[CONFIG] Schema: {schema_path}")
        print(f"[CONFIG] Output: {out_root}")
        print(f"[CONFIG] Project: {project_name or 'Unnamed'}")
        print(f"[CONFIG] Dry run: {args.dry_run}")
        print(f"[CONFIG] Force: {args.force}")

    try:
        # Parse schema
        base_dir = schema_path.parent
        actions, meta, vars_ = parse_schema(schema_text, out_root, base_dir, args.verbose)
        
        # Show project information
        print("\n" + "="*50)
        if meta.get("Project"):
            print(f"🏗️   PROJECT: {meta['Project']}")
        if meta.get("Description"):
            print(f"📝  {meta['Description']}")
        if meta.get("Version"):
            print(f"🏷️   VERSION: {meta['Version']}")
        print(f"📂  OUTPUT: {out_root}")
        print(f"⚡  ACTIONS: {len(actions)}")
        print("="*50)

        # Show dry run warning
        if args.dry_run:
            print("\n🚧 DRY RUN MODE - No files will be written")
            print("   Remove --dry-run to actually create files\n")

        # Execute actions
        success = realize(actions, out_root, args.dry_run, args.force, args.verbose)

        if success:
            if args.dry_run:
                print(f"\n✅ DRY RUN COMPLETED")
                print(f"   Would create {len(actions)} actions")
                print(f"   Output: {out_root}")
            else:
                print(f"\n✅ PROJECT GENERATED SUCCESSFULLY")
                print(f"   Created {len(actions)} items")
                print(f"   Location: {out_root}")
                
                # Show next steps
                if project_name:
                    print(f"\n🎯 NEXT STEPS:")
                    print(f"   cd {out_root}")
                    print(f"   Explore your new project!")
                    
        else:
            print(f"\n❌ PROJECT GENERATION COMPLETED WITH ERRORS")
            print(f"   Check output above for details")
            return 1

        return 0

    except ParseError as e:
        print(f"\n❌ SCHEMA PARSE ERROR:")
        print(f"   {e}")
        print(f"\n💡 TIPS:")
        print(f"   - Check indentation (use spaces, not tabs)")
        print(f"   - Verify variable syntax: @set VAR=value")
        print(f"   - Check heredoc markers match")
        return 1
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Operation cancelled by user")
        return 1
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        if args.verbose:
            print(f"\nDEBUG INFO:")
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


FILE: pyproject.toml
Kind: text
Size: 2053
Last modified: 2026-01-21T07:58:23Z

CONTENT:
[project]
name = "lrc"
version = "1.0.0-alpha.1"
description = "Local Repo Compile — build a repo from a declarative schema file"
readme = "README.md"
authors = [
    { name = "Justadudeinspace", email = "justadudeinspace@example.com" }
]
license = { text = "MIT" }
requires-python = ">=3.9"
keywords = ["scaffolding", "templates", "code-generation", "productivity"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]

dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0,<9.0",
    "pytest-cov>=4.1.0,<5.0.0",
    "black>=24.0.0,<25.0.0",
    "mypy>=1.8.0,<2.0.0",
    "flake8>=7.0.0,<8.0.0",
    "isort>=5.13.0,<6.0.0",
    "build>=1.0.0,<2.0.0",
]

pdf = [
    "reportlab>=4.0.8,<5.0",
    "Pillow>=11.3.0,<12.0",
]

perf = [
    "orjson>=3.9.0,<4.0.0",
    "tqdm>=4.65.0,<5.0.0",
]

all = [
    "reportlab>=4.0.8,<5.0",
    "Pillow>=11.3.0,<12.0",
    "orjson>=3.9.0,<4.0.0",
    "tqdm>=4.65.0,<5.0.0",
    "python-dateutil>=2.8.2,<3.0.0",
]

[project.urls]
Homepage = "https://github.com/Justadudeinspace/lrc"
Repository = "https://github.com/Justadudeinspace/lrc"
Documentation = "https://github.com/Justadudeinspace/lrc#readme"

[project.scripts]
lrc = "lrc.main:main"

[build-system]
requires = ["setuptools>=65.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "--verbose --strict-markers --strict-config"
testpaths = ["tests"]
pythonpath = ["src"]


FILE: requirements.txt
Kind: text
Size: 54
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# LRC runtime has no mandatory external dependencies.


FILE: src/lrc/__init__.py
Kind: text
Size: 7250
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""
Local Repo Compiler (LRC) - Public API.

LRC is a declarative tool for generating repository structures from text schemas.
It provides cross-platform support with security-focused features and enterprise integration.

Key Features:
- Declarative schema language for repository definition
- Cross-platform support (Windows, macOS, Linux, Android, Termux, WSL)
- Template system for common project types
- Security features including path traversal protection and signature verification
- DAT (Dev Audit Tool) integration for security auditing
- Extensible architecture with plugin support

Example Usage:
    >>> from lrc import parse_schema, realize
    >>> actions, metadata, variables = parse_schema(schema_text, output_dir)
    >>> result = realize(actions, output_dir)

Command Line:
    $ lrc schema.txt
    $ lrc --help

For complete documentation, visit: https://github.com/org/lrc
"""

from __future__ import annotations

__version__ = "1.0.0-alpha.1"
__author__ = "Justadudeinspace"
__email__ = "justadudeinspace@example.com"
__license__ = "MIT"
__copyright__ = "Copyright 2024 LRC Project"

import sys
from typing import TYPE_CHECKING

# Public API imports
from .core import (
    ParseError,
    do_bootstrap,
    get_default_output_dir,
    parse_schema,
    print_platform_info,
    realize,
)

from .audit import run_dat_audit
from .cli import main as cli_main

# Re-export types for public API
if TYPE_CHECKING:
    from .core import Action, GenerationResult
    from .compiler import BuildPlan

# Public API exports
__all__ = [
    # Core functionality
    "parse_schema",
    "realize", 
    "get_default_output_dir",
    "print_platform_info",
    "do_bootstrap",
    
    # Error handling
    "ParseError",
    
    # Enterprise features
    "run_dat_audit",
    
    # CLI interface
    "cli_main",
    
    # Types (re-exported for type checking)
    "Action",
    "BuildPlan", 
    "GenerationResult",
]


def get_version_info() -> dict[str, str]:
    """
    Get comprehensive version information for debugging and support.
    
    Returns:
        Dictionary containing version metadata
        
    Example:
        >>> get_version_info()
        {
            'version': '1.0.0-alpha.1',
            'author': 'Justadudeinspace',
            'python_version': '3.9.0',
            'platform': 'linux'
        }
    """
    import platform
    
    return {
        'version': __version__,
        'author': __author__,
        'python_version': platform.python_version(),
        'platform': platform.system().lower(),
        'license': __license__,
    }


def check_compatibility(min_python_version: tuple[int, int] = (3, 8)) -> bool:
    """
    Check if the current environment meets LRC's requirements.
    
    Args:
        min_python_version: Minimum Python version as (major, minor)
        
    Returns:
        True if compatible, False otherwise
        
    Raises:
        SystemExit: If running as main and incompatible
    """
    if sys.version_info < min_python_version:
        if __name__ == "__main__":
            min_ver_str = ".".join(map(str, min_python_version))
            current_ver = ".".join(map(str, sys.version_info[:2]))
            print(
                f"Error: LRC requires Python {min_ver_str} or newer. "
                f"Current version: {current_ver}",
                file=sys.stderr
            )
            sys.exit(1)
        return False
    return True


def setup_logging(level: str = "WARNING") -> None:
    """
    Configure logging for LRC modules.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Note:
        This is called automatically when using the CLI.
        For library use, call this function to enable logging.
    """
    import logging
    
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.WARNING),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


class LRCConfig:
    """
    Global configuration for LRC behavior.
    
    This class provides a centralized way to configure LRC's behavior
    across different modules and functions.
    """
    
    # Security settings
    REQUIRE_SIGNED_IMPORTS: bool = False
    VALIDATE_FILE_EXTENSIONS: bool = True
    ENABLE_PATH_TRAVERSAL_CHECKS: bool = True
    
    # Generation settings  
    DEFAULT_LINE_ENDINGS: str = "unix"  # "unix" or "windows"
    CREATE_BACKUPS: bool = False
    DRY_RUN_BY_DEFAULT: bool = False
    
    # Template settings
    TRUSTED_TEMPLATES: set[str] = {
        "python-cli", "node-cli", "rust-cli"
    }
    
    # Audit settings
    AUTO_AUDIT_AFTER_GENERATE: bool = False
    AUDIT_FORMAT: str = "json"  # "json", "pdf", "md", "combined"
    
    @classmethod
    def enable_enterprise_mode(cls) -> None:
        """
        Enable enterprise security features.
        
        This enables stricter security checks and audit requirements
        suitable for enterprise environments.
        """
        cls.REQUIRE_SIGNED_IMPORTS = True
        cls.VALIDATE_FILE_EXTENSIONS = True
        cls.ENABLE_PATH_TRAVERSAL_CHECKS = True
        cls.AUTO_AUDIT_AFTER_GENERATE = True
    
    @classmethod
    def disable_security_checks(cls) -> None:
        """
        Disable security checks (not recommended).
        
        Warning: This should only be used in trusted environments
        and may expose your system to security risks.
        """
        cls.REQUIRE_SIGNED_IMPORTS = False
        cls.VALIDATE_FILE_EXTENSIONS = False
        cls.ENABLE_PATH_TRAVERSAL_CHECKS = False


# Initialize package
def _initialize_package() -> None:
    """
    Initialize LRC package on import.
    
    This function is called automatically when the package is imported
    and handles package-level initialization tasks.
    """
    # Check Python version compatibility
    check_compatibility()
    
    # Set up environment variables
    import os
    os.environ.setdefault('LRC_FORCE_COLOR', '0')
    os.environ.setdefault('LRC_DEBUG', '0')
    
    # Initialize logging if debug mode is enabled
    if os.environ.get('LRC_DEBUG') == '1':
        setup_logging('DEBUG')


# Backwards compatibility imports
# These ensure that existing code continues to work after refactoring
try:
    from .core import Action
    __all__.append('Action')
except ImportError:
    # Action might be defined elsewhere or not available
    pass

try:
    from .compiler import BuildPlan
    __all__.append('BuildPlan')
except ImportError:
    # BuildPlan might be defined elsewhere or not available  
    pass

try:
    from .core import GenerationResult
    __all__.append('GenerationResult')
except ImportError:
    # GenerationResult might be defined elsewhere or not available
    pass

# Initialize package on import
_initialize_package()

# Convenience function for direct execution
def main() -> int:
    """
    Convenience function for executing LRC CLI.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
        
    Example:
        >>> from lrc import main
        >>> exit_code = main()
    """
    return cli_main()


# Allow direct execution: python -m lrc
if __name__ == "__main__":
    sys.exit(main())


FILE: src/lrc/__main__.py
Kind: text
Size: 3676
Last modified: 2026-01-21T07:58:23Z

CONTENT:
#!/usr/bin/env python3
"""
LRC (Local Repo Compiler) - Module entry point for ``python -m lrc``.

This module provides the entry point when LRC is executed as a module:
    python -m lrc [ARGS]

It handles proper initialization, error handling, and clean shutdown.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path
from typing import NoReturn


def setup_environment() -> None:
    """
    Set up the runtime environment for LRC.
    
    This function:
    - Ensures proper UTF-8 encoding
    - Sets up Python path if needed
    - Configures environment variables
    """
    # Ensure UTF-8 encoding for cross-platform compatibility
    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except (AttributeError, Exception):
            # Fallback for older Python versions
            pass
    
    if sys.stderr.encoding.lower() != 'utf-8':
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except (AttributeError, Exception):
            # Fallback for older Python versions
            pass
    
    # Add current directory to Python path for development
    if str(Path.cwd()) not in sys.path:
        sys.path.insert(0, str(Path.cwd()))
    
    # Set environment variables for consistent behavior
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    os.environ.setdefault('LRC_FORCE_COLOR', '0')


def handle_import_error() -> NoReturn:
    """
    Handle import errors with helpful error messages.
    
    This provides guidance for common installation and setup issues.
    """
    print("Error: Could not import LRC modules.", file=sys.stderr)
    print("\nThis usually indicates:", file=sys.stderr)
    print("  1. LRC is not properly installed", file=sys.stderr)
    print("  2. You're running from the wrong directory", file=sys.stderr)
    print("  3. There's a missing dependency", file=sys.stderr)
    print("\nTroubleshooting steps:", file=sys.stderr)
    print("  - Install with: pip install -e .", file=sys.stderr)
    print("  - Run from project root directory", file=sys.stderr)
    print("  - Check Python path and virtual environment", file=sys.stderr)
    
    # Debug information
    print(f"\nDebug info:", file=sys.stderr)
    print(f"  Python: {sys.version}", file=sys.stderr)
    print(f"  Executable: {sys.executable}", file=sys.stderr)
    print(f"  Current dir: {Path.cwd()}", file=sys.stderr)
    print(f"  Python path: {sys.path}", file=sys.stderr)
    
    sys.exit(1)


def main() -> int:
    """
    Main entry point for module execution.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        # Set up environment before importing LRC modules
        setup_environment()
        
        # Import the main CLI function
        try:
            from .cli import main as cli_main
        except ImportError as e:
            print(f"Import error: {e}", file=sys.stderr)
            handle_import_error()
        
        # Execute the CLI with command line arguments
        return cli_main()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
        
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        
        # Provide debug information for unexpected errors
        if os.environ.get('LRC_DEBUG'):
            import traceback
            traceback.print_exc()
            
        return 1


if __name__ == "__main__":
    # Ensure clean exit with proper exit code
    exit_code = main()
    sys.exit(exit_code)


FILE: src/lrc/audit.py
Kind: text
Size: 3170
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""Integration with the DAT auditing pipeline."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Sequence

CONFIG_PATH = Path.home() / ".config" / "lrc" / "dat_integration.json"


class DataAuditResult(Dict[str, str]):
    """Simple dictionary-based container for audit metadata."""


def _load_config(config_path: Path = CONFIG_PATH) -> Optional[Dict[str, object]]:
    if not config_path.exists():
        return None
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid DAT integration config: {exc}") from exc


def _coerce_command(command: object) -> Sequence[str]:
    if isinstance(command, str):
        return command.split()
    if isinstance(command, (list, tuple)):
        return [str(part) for part in command]
    raise TypeError("DAT integration command must be a string or sequence")


def run_dat_audit(
    build_dir: Path, *, logger=print, config_path: Path = CONFIG_PATH
) -> DataAuditResult:
    """Run the DAT audit pipeline if it is configured.

    Parameters
    ----------
    build_dir:
        Directory that was generated by LRC.
    logger:
        Callable used to emit log lines.  Defaults to :func:`print`.
    config_path:
        Location of the DAT integration configuration file.

    Returns
    -------
    DataAuditResult
        Mapping containing the status and captured output.
    """

    cfg = _load_config(config_path)
    result: DataAuditResult = DataAuditResult()
    result["status"] = "skipped"

    if not cfg:
        logger("[AUDIT] DAT integration config not found; skipping")
        return result

    if not cfg.get("enabled", True):
        logger("[AUDIT] DAT integration disabled in config")
        return result

    command = _coerce_command(cfg.get("command", ["dat", "audit"]))
    args = list(command)
    if "${BUILD_DIR}" in args:
        args = [part.replace("${BUILD_DIR}", str(build_dir)) for part in args]
    else:
        args.append(str(build_dir))

    env = os.environ.copy()
    extra_env = cfg.get("env")
    if isinstance(extra_env, dict):
        env.update({str(k): str(v) for k, v in extra_env.items()})

    logger(f"[AUDIT] Running: {' '.join(args)}")

    try:
        completed = subprocess.run(
            args,
            cwd=str(build_dir),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"DAT command not found: {args[0]}") from exc

    result["stdout"] = completed.stdout.strip()
    result["stderr"] = completed.stderr.strip()
    result["returncode"] = str(completed.returncode)

    if completed.returncode == 0:
        result["status"] = "passed"
        logger("[AUDIT] DAT audit completed successfully")
    else:
        result["status"] = "failed"
        logger("[AUDIT] DAT audit reported issues")
        if completed.stderr:
            logger(completed.stderr)

    if completed.stdout:
        logger(completed.stdout)

    return result


FILE: src/lrc/bootstrap.py
Kind: text
Size: 2319
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""Utility helpers for the ``--bootstrap`` flag."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from .compiler import IS_WINDOWS


def detect_install_bin() -> Path:
    if _is_termux():
        return Path("/data/data/com.termux/files/usr/bin")
    if IS_WINDOWS:
        for candidate in [
            Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps",
            Path.home() / "AppData" / "Local" / "Programs" / "Python",
        ]:
            if candidate.exists():
                return candidate
        return Path.home() / "AppData" / "Local" / "bin"
    return Path.home() / ".local" / "bin"


def persist_path(bin_dir: Path, verbose: bool = False) -> None:
    export_line = f'export PATH="{bin_dir}:$PATH"'
    shell = os.environ.get("SHELL", "").split("/")[-1] or "bash"
    targets = {
        "zsh": [Path.home() / ".zshrc", Path.home() / ".zprofile"],
        "bash": [Path.home() / ".bashrc", Path.home() / ".bash_profile", Path.home() / ".profile"],
        "fish": [Path.home() / ".config" / "fish" / "config.fish"],
        "pwsh": [Path.home() / "Documents" / "PowerShell" / "profile.ps1"],
    }
    for rc in targets.get(shell, targets["bash"]):
        try:
            rc.parent.mkdir(parents=True, exist_ok=True)
            rc.touch(exist_ok=True)
            content = rc.read_text(encoding="utf-8")
            if export_line not in content:
                rc.write_text(content + f"\n# Added by lrc\n{export_line}\n", encoding="utf-8")
                if verbose:
                    print(f"[PATH] Updated {rc}")
        except OSError as exc:
            if verbose:
                print(f"[WARN] Could not update {rc}: {exc}")


def do_bootstrap(argv0: str, verbose: bool = False) -> Path:
    bin_dir = detect_install_bin()
    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / ("lrc.exe" if IS_WINDOWS else "lrc")
    source = Path(argv0).resolve()
    if not source.exists():
        source = Path(__file__).resolve()
    shutil.copy2(source, target)
    if not IS_WINDOWS:
        target.chmod(0o755)
    persist_path(bin_dir, verbose)
    if verbose:
        print(f"[BOOTSTRAP] Installed to {target}")
    return target


def _is_termux() -> bool:
    return "com.termux" in os.environ.get("PREFIX", "")


FILE: src/lrc/cli/__init__.py
Kind: text
Size: 106
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""CLI entry points for LRC."""

from .main import build_parser, main

__all__ = ["build_parser", "main"]


FILE: src/lrc/cli/main.py
Kind: text
Size: 5950
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""Command line interface for LRC."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .. import core
from ..audit import run_dat_audit
from ..parser import ParseError, parse_schema
from ..compiler import realize

RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def colorize(message: str, color: str) -> str:
    if not sys.stdout.isatty():
        return message
    return f"{color}{message}{RESET}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="lrc — Local Repo Compile — Build a local repo from a declarative text schema.",
        epilog="""Examples:\n  lrc schema.txt --dry-run\n  lrc schema.txt --audit\n  lrc --bootstrap""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("schema", nargs="?", help="Input schema file")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument(
        "--base-dir", help="Base directory for includes (default: schema file dir)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be created"
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument(
        "--audit", action="store_true", help="Run DAT audit after successful build"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--bootstrap", action="store_true", help="Install lrc to user bin directory"
    )
    parser.add_argument(
        "--platform-info", action="store_true", help="Show platform information"
    )
    parser.add_argument(
        "--version", action="store_true", help="Show version information"
    )
    return parser


def _display_metadata(meta: dict) -> None:
    if meta.get("Project") or meta.get("Description"):
        print(colorize("\n[PROJECT]", CYAN))
        for key in ["Project", "Description", "Version"]:
            if meta.get(key):
                print(f"  {key}: {meta[key]}")
        print()


def _print_error_context(path: Path, line_num: int, message: str, snippet: str) -> None:
    pointer = colorize("--> ", RED)
    print(colorize(f"[PARSE ERROR] {message}", RED))
    if path.exists():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []
    else:
        lines = []
    if 1 <= line_num <= len(lines):
        context = lines[line_num - 1]
        print(f"{pointer}{path}:{line_num}: {context}")
        if snippet:
            print(f"    {snippet}")
    elif snippet:
        print(f"{pointer}{snippet}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"lrc version {core.__version__}")
        return 0

    if args.platform_info:
        core.print_platform_info(verbose=True)
        return 0

    if args.bootstrap:
        core.do_bootstrap(sys.argv[0], verbose=args.verbose)
        return 0

    if not args.schema:
        parser.print_help()
        print(colorize("\n[ERROR] No schema file specified", RED))
        return 1

    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(colorize(f"[ERROR] Schema file not found: {schema_path}", RED))
        return 1

    base_dir = Path(args.base_dir) if args.base_dir else schema_path.parent
    base_dir = base_dir.resolve()

    if args.output:
        out_root = Path(args.output).resolve()
    else:
        schema_text = schema_path.read_text(encoding="utf-8")
        project_name = None
        for line in schema_text.splitlines():
            if line.strip().lower().startswith("# project:"):
                project_name = line.split(":", 1)[1].strip()
                break
        out_root = core.get_default_output_dir(project_name)

    fs_ok, fs_msg = core.check_fs_ok(out_root)
    if not fs_ok:
        print(colorize(f"[ERROR] Filesystem issue: {fs_msg}", RED))
        return 1

    if args.verbose:
        core.print_platform_info()
        print(f"[INFO] Schema: {schema_path}")
        print(f"[INFO] Base dir: {base_dir}")
        print(f"[INFO] Output: {out_root}")
        print(f"[INFO] Force: {args.force}")
        print(f"[INFO] Dry run: {args.dry_run}")
        print(f"[INFO] Audit: {args.audit}")

    try:
        schema_text = schema_path.read_text(encoding="utf-8")
        actions, meta, vars_ = parse_schema(
            schema_text, out_root, base_dir, args.verbose
        )
        _display_metadata(meta)

        print(colorize(f"[BUILD] Creating repository in {out_root}", CYAN))
        success = realize(actions, out_root, args.dry_run, args.force, args.verbose)

        if not success:
            print(colorize("[ERROR] Some operations failed", RED))
            return 1

        if args.dry_run:
            print(
                colorize(
                    f"[SUCCESS] Dry run completed - would create {len(actions)} actions",
                    GREEN,
                )
            )
            return 0

        print(colorize(f"[SUCCESS] Repository created: {out_root}", GREEN))

        if args.audit:
            try:
                run_dat_audit(out_root)
            except Exception as exc:  # pragma: no cover - unexpected env issues
                print(colorize(f"[AUDIT] Failed: {exc}", YELLOW))
        return 0
    except ParseError as err:
        _print_error_context(schema_path, err.line_num, err.message, err.line_content)
        return 2
    except Exception as exc:  # pragma: no cover - defensive programming
        print(colorize(f"[ERROR] {exc}", RED))
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


__all__ = ["build_parser", "main"]


FILE: src/lrc/compiler.py
Kind: text
Size: 6530
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""Compilation helpers for LRC.

The compiler module coordinates schema parsing, signature verification and
high-level planning before the generator materialises files on disk.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from .parser import (
    Action,
    GPGReport,
    ParseError,
    coalesce_mkdirs,
    detect_signature_file,
    parse_schema,
)

__all__ = [
    "BuildPlan",
    "ParseError",
    "compile_schema_path",
    "get_default_output_dir",
    "print_platform_info",
    "resolve_output_directory",
    "SYSTEM",
]

SYSTEM = platform.system().lower()
IS_WINDOWS = SYSTEM == "windows"
IS_LINUX = SYSTEM == "linux"
IS_MACOS = SYSTEM == "darwin"


@dataclass
class BuildPlan:
    """Structured representation of the actions required for a build."""

    source: Path
    root: Path
    actions: List[Action]
    metadata: Dict[str, str]
    variables: Dict[str, str]
    ignores: List[str]
    gpg_reports: List[GPGReport]
    schema_signature: Optional[GPGReport]

    @property
    def project_name(self) -> str:
        for key in ("Project", "PROJECT", "NAME"):
            value = self.metadata.get(key) or self.variables.get(key, "")
            if value:
                return value
        return self.source.stem

    def rebase(self, new_root: Path) -> "BuildPlan":
        if new_root == self.root:
            return self
        rebased_actions: List[Action] = []
        for action in self.actions:
            try:
                relative = action.path.relative_to(self.root)
                new_path = new_root / relative
            except ValueError:
                new_path = action.path
            rebased_actions.append(
                Action(
                    kind=action.kind,
                    path=new_path,
                    content=action.content,
                    mode=action.mode,
                    src=action.src,
                    target=action.target,
                )
            )
        return BuildPlan(
            source=self.source,
            root=new_root,
            actions=rebased_actions,
            metadata=self.metadata,
            variables=self.variables,
            ignores=self.ignores,
            gpg_reports=self.gpg_reports,
            schema_signature=self.schema_signature,
        )


def compile_schema_path(
    schema_path: Path,
    out_dir: Path,
    *,
    verbose: bool = False,
) -> BuildPlan:
    schema_path = schema_path.resolve()
    out_dir = out_dir.resolve()
    if not schema_path.exists():
        raise FileNotFoundError(schema_path)

    schema_signature = verify_schema_signature(schema_path, verbose=verbose)

    text = schema_path.read_text(encoding="utf-8")
    result = parse_schema(text, out_dir, schema_path.parent, verbose=verbose)

    metadata = {k: (v or "") for k, v in result.metadata.items()}

    return BuildPlan(
        source=schema_path,
        root=out_dir,
        actions=coalesce_mkdirs(result.actions),
        metadata=metadata,
        variables=result.variables,
        ignores=result.ignores,
        gpg_reports=result.gpg_reports,
        schema_signature=schema_signature,
    )


def verify_schema_signature(schema_path: Path, *, verbose: bool = False) -> Optional[GPGReport]:
    signature = detect_signature_file(schema_path)
    if not signature:
        return None
    if shutil.which("gpg") is None:
        raise ParseError(0, "GPG executable not available for schema verification", schema_path.name)
    result = subprocess.run(
        ["gpg", "--verify", str(signature), str(schema_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise ParseError(0, f"Schema signature verification failed: {schema_path.name}", stderr)
    if verbose:
        print(f"[tag] verified schema signature {signature}")
    return GPGReport(path=str(schema_path), verified=True, signature=str(signature))


def sanitize_name(value: str) -> str:
    return re.sub(r"[^\w\-_.]", "_", value)


def get_default_output_dir(project_name: Optional[str] = None) -> Path:
    base_dir = Path.cwd()
    if IS_LINUX and _is_termux():
        base_dir = Path.home() / "projects"
        base_dir.mkdir(exist_ok=True)
    if project_name:
        return base_dir / sanitize_name(project_name)
    return base_dir / "lrc_output"


def resolve_output_directory(plan: BuildPlan, explicit: Optional[Path]) -> Path:
    if explicit:
        return explicit.resolve()
    project = plan.project_name
    return get_default_output_dir(project)


def check_fs_ok(path: Path) -> tuple[bool, str]:
    try:
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        test_file = parent / ".lrc_test.tmp"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        if IS_WINDOWS and len(str(path)) > 260:
            return False, "Path exceeds Windows MAX_PATH limit (260 chars)"
        return True, "OK"
    except PermissionError:
        return False, "Permission denied"
    except OSError as exc:
        return False, f"Filesystem error: {exc}"


def print_platform_info(verbose: bool = False) -> None:
    info = [
        f"Platform: {platform.platform()}",
        f"System: {SYSTEM}",
        f"Windows: {IS_WINDOWS}",
        f"Linux: {IS_LINUX}",
        f"macOS: {IS_MACOS}",
        f"Python: {platform.python_version()}",
    ]
    if verbose:
        info.extend(
            [
                f"Current dir: {Path.cwd()}",
                f"Home dir: {Path.home()}",
                f"Executable: {os.environ.get('PYTHONEXECUTABLE', '')}",
            ]
        )
    for line in info:
        print(f"[INFO] {line}")


def build_metadata(plan: BuildPlan) -> Dict[str, object]:
    data: Dict[str, object] = {
        "schema": str(plan.source),
        "root": str(plan.root),
        "project": plan.project_name,
        "metadata": plan.metadata,
        "variables": plan.variables,
        "ignores": plan.ignores,
        "gpg": [report.__dict__ for report in plan.gpg_reports],
    }
    if plan.schema_signature:
        data.setdefault("gpg", []).append(plan.schema_signature.__dict__)
    return data


def _is_termux() -> bool:
    return "com.termux" in os.environ.get("PREFIX", "")


import re
import shutil
import subprocess



FILE: src/lrc/compiler/__init__.py
Kind: text
Size: 515
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""Compilation helpers for LRC actions."""

from __future__ import annotations

from typing import List
from pathlib import Path

from ..core import Action as _Action, realize as _realize

Action = _Action
__all__ = ["Action", "realize"]


def realize(
    actions: List[_Action],
    base_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    verbose: bool = False,
) -> bool:
    """Execute actions using the legacy implementation."""

    return _realize(actions, base_dir, dry_run, force, verbose)


FILE: src/lrc/core.py
Kind: text
Size: 45170
Last modified: 2026-01-21T07:58:23Z

CONTENT:
#!/usr/bin/env python3
"""
LRC — Local Repo Compiler
Build local repositories from declarative text schemas.

Cross-platform support for: Android/Termux, Android/Linux, Linux, WSL2, macOS, Windows
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import os
import platform
import shutil
import textwrap
import re
import fnmatch
import json
import subprocess
from typing import List, Optional, Tuple, Literal, Dict, Any, Set
import hashlib
import tempfile

# ----------------------------- Constants & Configuration --------------------

__version__ = "1.0.0-alpha.1"

SYSTEM = platform.system().lower()
IS_WINDOWS = SYSTEM == "windows"
IS_LINUX = SYSTEM == "linux"
IS_MACOS = SYSTEM == "darwin"
IS_ANDROID = (
    "android" in platform.platform().lower()
    or "linux-android" in platform.platform().lower()
)
IS_TERMUX = IS_ANDROID and "com.termux" in os.environ.get("PREFIX", "")
IS_WSL = False
if IS_LINUX:
    try:
        with open("/proc/version", "r") as f:
            if "microsoft" in f.read().lower():
                IS_WSL = True
    except Exception:
        pass

LINE_ENDINGS = "windows" if IS_WINDOWS else "unix"

DEFAULT_TRUSTED_TEMPLATES: Set[str] = {
    "python-cli",
    "node-cli",
    "rust-cli",
}

REQUIRE_SIGNED_IMPORTS = os.environ.get("LRC_REQUIRE_SIGNED_INCLUDES", "").lower() in {
    "1",
    "true",
    "yes",
}

# ----------------------------- Data Models ---------------------------------

@dataclass
class Action:
    """Represents a filesystem operation to be performed."""
    kind: Literal["mkdir", "write", "chmod", "copy", "symlink"]
    path: Path
    content: Optional[str] = None
    mode: Optional[int] = None
    src: Optional[Path] = None
    target: Optional[Path] = None

    def __str__(self) -> str:
        base = f"{self.kind}: {self.path}"
        if self.kind == "write":
            return f"{base} ({len(self.content or '')} bytes)"
        elif self.kind == "chmod":
            return f"{base} (mode: {oct(self.mode or 0o644)})"
        elif self.kind == "copy":
            return f"{base} <- {self.src}"
        elif self.kind == "symlink":
            return f"{base} -> {self.target}"
        return base


@dataclass
class ParseError(Exception):
    """Custom exception for schema parsing errors."""
    line_num: int
    message: str
    line_content: str = ""

    def __str__(self) -> str:
        return f"Line {self.line_num}: {self.message}\n  {self.line_content}"


@dataclass
class GenerationResult:
    """Result of repository generation operation."""
    success: bool
    actions_performed: int
    errors: List[str]
    warnings: List[str]

    def __bool__(self) -> bool:
        return self.success


# ----------------------------- Trust & Verification ------------------------

def load_trusted_templates(base_dir: Path) -> Set[str]:
    """
    Load template trust policy from disk.
    
    Args:
        base_dir: Base directory to search for trust configuration
        
    Returns:
        Set of trusted template names
    """
    candidates = [
        base_dir / "trusted_templates.json",
        base_dir / ".lrc" / "trusted_templates.json",
        Path.home() / ".config" / "lrc" / "trusted_templates.json",
        Path(__file__).resolve().parent.parent / "trusted_templates.json",
        Path(__file__).resolve().parents[2] / "trusted_templates.json",
    ]
    
    for candidate in candidates:
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return {str(item).strip() for item in data if str(item).strip()}
                elif isinstance(data, dict) and "templates" in data:
                    return {str(item).strip() for item in data["templates"] if str(item).strip()}
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise ParseError(
                    0, f"Invalid trusted template policy: {candidate}", str(exc)
                ) from exc
            except Exception as exc:
                # Continue to next candidate on other errors
                continue
    
    return DEFAULT_TRUSTED_TEMPLATES


def _detect_signature_file(include_path: Path) -> Optional[Path]:
    """
    Detect signature file for an included schema.
    
    Args:
        include_path: Path to the included schema file
        
    Returns:
        Path to signature file if found, None otherwise
    """
    candidates = [
        include_path.with_name(include_path.name + ".asc"),
        include_path.with_name(include_path.name + ".sig"),
        include_path.with_suffix(include_path.suffix + ".asc"),
        include_path.with_suffix(include_path.suffix + ".sig"),
        include_path.parent / (include_path.name + ".asc"),
        include_path.parent / (include_path.name + ".sig"),
    ]
    
    seen = set()
    for cand in candidates:
        if cand in seen:
            continue
        seen.add(cand)
        if cand.exists() and cand.is_file():
            return cand
    return None


def verify_include_signature(
    include_path: Path, line_num: int, line: str, verbose: bool
) -> None:
    """
    Ensure that included schema files are signed by a trusted key.
    
    Args:
        include_path: Path to included schema file
        line_num: Line number in original schema
        line: Original line content
        verbose: Enable verbose output
        
    Raises:
        ParseError: If signature verification fails
    """
    signature = _detect_signature_file(include_path)
    if not signature:
        if REQUIRE_SIGNED_IMPORTS:
            raise ParseError(
                line_num, f"No signature found for include: {include_path.name}", line
            )
        return
    
    if shutil.which("gpg") is None:
        raise ParseError(
            line_num, "GPG executable not available for signature verification", line
        )
    
    try:
        result = subprocess.run(
            ["gpg", "--verify", str(signature), str(include_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,  # Prevent hanging on large files
        )
        
        if result.returncode != 0:
            stderr = result.stderr.strip()
            error_msg = stderr.split('\n')[0] if stderr else "Unknown GPG error"
            raise ParseError(
                line_num,
                f"GPG signature verification failed for {include_path.name}: {error_msg}",
                line,
            )
            
        if verbose:
            print(f"[VERIFY] ✓ Verified signature {signature.name}")
            
    except subprocess.TimeoutExpired:
        raise ParseError(
            line_num, "GPG signature verification timed out", line
        )
    except Exception as exc:
        raise ParseError(
            line_num, f"GPG verification error: {exc}", line
        )


# ----------------------------- Security & Utilities ------------------------

def get_safe_path(path: Path) -> Path:
    """
    Get safe, normalized path with proper error handling.
    
    Args:
        path: Input path to normalize
        
    Returns:
        Normalized absolute path
    """
    try:
        return path.resolve()
    except (OSError, RuntimeError, ValueError):
        return path.absolute()


def normalize_line_endings(content: str, target: str = LINE_ENDINGS) -> str:
    """
    Normalize line endings for target platform.
    
    Args:
        content: Text content to normalize
        target: Target line ending style ('windows' or 'unix')
        
    Returns:
        Content with normalized line endings
    """
    if not content:
        return content
        
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    if target == "windows":
        content = content.replace("\n", "\r\n")
    return content


def expand_vars(s: str, vars_: Dict[str, str]) -> str:
    """
    Expand ${VAR} variables with proper escaping and error handling.
    
    Args:
        s: String containing variables to expand
        vars_: Dictionary of variable names to values
        
    Returns:
        String with variables expanded
    """
    if not s:
        return s

    def replace_var(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name in vars_:
            return vars_[var_name]
        # Leave unknown variables as-is for later resolution
        return match.group(0)

    pattern = r"\$\{([^}]+)\}"
    return re.sub(pattern, replace_var, s)


def is_safe_under_base(path: Path, base_dir: Path) -> bool:
    """
    Enhanced security check to prevent path traversal.
    
    Args:
        path: Target path to check
        base_dir: Base directory that path must be contained within
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        base_real = os.path.realpath(str(get_safe_path(base_dir)))
        target_real = os.path.realpath(str(get_safe_path(path)))
        common = os.path.commonpath([base_real, target_real])
        return common == base_real
    except (ValueError, OSError, RuntimeError):
        return False


def validate_file_extension(filename: str) -> bool:
    """
    Validate file extensions for security.
    
    Args:
        filename: Name of file to validate
        
    Returns:
        True if extension is safe, False otherwise
    """
    dangerous_extensions = {
        ".exe", ".bat", ".cmd", ".sh", ".bin", ".app", ".dmg", 
        ".pkg", ".deb", ".rpm", ".msi", ".scr", ".com", ".vbs",
        ".ps1", ".psm1", ".jar", ".war", ".apk", ".ipa",
    }

    ext = Path(filename).suffix.lower()
    return ext not in dangerous_extensions


def get_default_output_dir(project_name: Optional[str] = None) -> Path:
    """
    Get platform-appropriate default output directory.
    
    Args:
        project_name: Optional project name to use in directory path
        
    Returns:
        Path to default output directory
    """
    base_dir = Path.cwd()

    if IS_TERMUX:
        base_dir = Path.home() / "projects"
        base_dir.mkdir(exist_ok=True)
    elif IS_ANDROID:
        for candidate in ["Downloads", "Documents", "projects"]:
            candidate_path = Path.home() / candidate
            if candidate_path.exists() and os.access(candidate_path, os.W_OK):
                base_dir = candidate_path
                break
        else:
            # Create projects directory if no suitable one exists
            base_dir = Path.home() / "projects"
            base_dir.mkdir(exist_ok=True)

    if project_name:
        # Sanitize project name for filesystem safety
        safe_name = re.sub(r"[^\w\-_.]", "_", project_name)
        return base_dir / safe_name
    else:
        return base_dir / "lrc_output"


def check_fs_ok(path: Path) -> Tuple[bool, str]:
    """
    Check filesystem compatibility and permissions.
    
    Args:
        path: Path to check
        
    Returns:
        Tuple of (is_ok, message)
    """
    try:
        # Check parent directory writability
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)

        # Test write permissions
        test_file = parent / ".lrc_test.tmp"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink(missing_ok=True)

        # Platform-specific checks
        if IS_WINDOWS:
            # Windows path length limit
            if len(str(path)) > 260:
                return False, "Path exceeds Windows MAX_PATH limit (260 chars)"
            
            # Check for reserved names
            reserved_names = {
                "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
                "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3",
                "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
            }
            if path.stem.upper() in reserved_names:
                return False, f"Reserved Windows name: {path.stem}"

        return True, "OK"
        
    except PermissionError:
        return False, "Permission denied"
    except OSError as e:
        return False, f"Filesystem error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def print_platform_info(verbose: bool = False) -> None:
    """Print platform information for debugging."""
    info = [
        f"[INFO] Platform: {platform.platform()}",
        f"[INFO] System: {SYSTEM}",
        f"[INFO] Windows: {IS_WINDOWS}",
        f"[INFO] Linux: {IS_LINUX}",
        f"[INFO] macOS: {IS_MACOS}",
        f"[INFO] Android: {IS_ANDROID}",
        f"[INFO] Termux: {IS_TERMUX}",
        f"[INFO] WSL: {IS_WSL}",
        f"[INFO] Python: {platform.python_version()}",
        f"[INFO] Line endings: {LINE_ENDINGS}",
    ]

    if verbose:
        info.extend([
            f"[INFO] Current dir: {Path.cwd()}",
            f"[INFO] Home dir: {Path.home()}",
            f"[INFO] Executable: {sys.executable}",
            f"[INFO] Architecture: {platform.architecture()[0]}",
            f"[INFO] Machine: {platform.machine()}",
        ])

    print("\n".join(info))


# ----------------------------- Templates -----------------------------------

def template_actions(name: str, root: Path, vars_: Dict[str, str]) -> List[Action]:
    """
    Generate template-based actions.
    
    Args:
        name: Template name
        root: Root directory for generated files
        vars_: Variables for template expansion
        
    Returns:
        List of actions to create template structure
    """
    name = name.lower().strip()
    acts: List[Action] = []

    if name in ("python-cli", "py-cli"):
        acts.extend([
            Action("mkdir", root / "src"),
            Action("write", root / "src" / "__init__.py", ""),
            Action(
                "write",
                root / "src" / "main.py",
                normalize_line_endings(
                    textwrap.dedent(
                        f"""\
                        #!/usr/bin/env python3
                        \"\"\"{expand_vars('${PROJECT}', vars_) or 'App'} - {expand_vars('${DESCRIPTION}', vars_) or 'CLI application'}\"\"\"

                        def main():
                            print("Hello {expand_vars('${AUTHOR}', vars_) or 'World'}!")

                        if __name__ == "__main__":
                            main()
                        """
                    )
                ),
            ),
            Action("chmod", root / "src" / "main.py", mode=0o755),
            Action(
                "write",
                root / "README.md",
                f"# {expand_vars('${PROJECT}', vars_) or 'App'}\n\n"
                f"{expand_vars('${DESCRIPTION}', vars_) or 'A minimal Python CLI.'}\n",
            ),
            Action(
                "write",
                root / ".gitignore",
                "__pycache__/\n.venv/\n.DS_Store\n*.pyc\n*.pyo\n*.pyd\n",
            ),
            Action(
                "write",
                root / "pyproject.toml",
                textwrap.dedent(
                    f"""\
                    [project]
                    name = "{expand_vars('${PKG}', vars_) or 'app'}"
                    version = "{expand_vars('${VERSION}', vars_) or '0.1.0'}"
                    description = "{expand_vars('${DESCRIPTION}', vars_) or 'CLI application'}"
                    authors = [{{name = "{expand_vars('${AUTHOR}', vars_) or 'Unknown'}"}}]
                    requires-python = ">=3.8"

                    [project.scripts]
                    {expand_vars('${PKG}', vars_) or 'app'} = "src.main:main"
                    """
                ),
            ),
        ])
    elif name in ("node-cli", "js-cli"):
        acts.extend([
            Action("mkdir", root / "bin"),
            Action(
                "write",
                root / "bin" / "cli.js",
                normalize_line_endings(
                    "#!/usr/bin/env node\nconsole.log('Hello CLI');\n"
                ),
            ),
            Action("chmod", root / "bin" / "cli.js", mode=0o755),
            Action(
                "write",
                root / "package.json",
                normalize_line_endings(
                    textwrap.dedent(
                        f"""\
                        {{
                          "name": "{expand_vars('${PKG}', vars_) or 'app'}",
                          "version": "{expand_vars('${VERSION}', vars_) or '0.1.0'}",
                          "description": "{expand_vars('${DESCRIPTION}', vars_) or 'CLI application'}",
                          "bin": "bin/cli.js",
                          "author": "{expand_vars('${AUTHOR}', vars_) or ''}"
                        }}
                        """
                    )
                ),
            ),
            Action(
                "write",
                root / ".gitignore",
                "node_modules/\n.DS_Store\nnpm-debug.log*\n",
            ),
            Action(
                "write",
                root / "README.md",
                f"# {expand_vars('${PROJECT}', vars_) or 'Node CLI'}\n",
            ),
        ])
    elif name in ("rust-cli", "rs-cli"):
        acts.extend([
            Action(
                "write",
                root / "Cargo.toml",
                textwrap.dedent(
                    f"""\
                    [package]
                    name = "{expand_vars('${PKG}', vars_) or 'app'}"
                    version = "{expand_vars('${VERSION}', vars_) or '0.1.0'}"
                    authors = ["{expand_vars('${AUTHOR}', vars_) or 'Unknown'}"]
                    description = "{expand_vars('${DESCRIPTION}', vars_) or 'CLI application'}"

                    [[bin]]
                    name = "{expand_vars('${PKG}', vars_) or 'app'}"
                    path = "src/main.rs"
                    """
                ),
            ),
            Action("mkdir", root / "src"),
            Action(
                "write",
                root / "src" / "main.rs",
                textwrap.dedent(
                    """\
                    fn main() {
                        println!("Hello, Rust CLI!");
                    }
                    """
                ),
            ),
        ])
    else:
        # Unknown template - create basic structure
        acts.append(
            Action(
                "write",
                root / "README.md",
                f"# {name}\n\nProject generated from template: {name}\n",
            )
        )

    return acts


# ----------------------------- Parsing -------------------------------------

class ParserState:
    """State maintained during schema parsing."""

    def __init__(self, out_root: Path):
        self.out_root = out_root
        self.dir_stack: List[Path] = [out_root]
        self.indent_stack: List[int] = [0]
        self.actions: List[Action] = []
        self.meta: Dict[str, Optional[str]] = {
            "Project": None,
            "Description": None,
            "Version": None,
        }
        self.vars: Dict[str, str] = {
            "AUTHOR": "",
            "PROJECT": "",
            "DESCRIPTION": "",
            "VERSION": "",
            "PKG": "",
        }
        self.ignores: List[str] = []
        self.heredoc_stack: List[Tuple[str, Path, int]] = (
            []
        )  # (marker, target_path, start_line)
        self.trusted_templates: Optional[Set[str]] = None
        self.base_dir: Path = out_root

    def current_dir(self) -> Path:
        """Get current directory from stack."""
        return self.dir_stack[-1]


def parse_schema(
    schema_text: str, out_root: Path, base_dir: Path, verbose: bool = False
) -> Tuple[List[Action], Dict[str, Optional[str]], Dict[str, str]]:
    """
    Parse schema text into actions, metadata, and variables.
    
    Args:
        schema_text: Schema content as string
        out_root: Root directory for output
        base_dir: Base directory for relative includes
        verbose: Enable verbose output
        
    Returns:
        Tuple of (actions, metadata, variables)
        
    Raises:
        ParseError: If schema parsing fails
    """
    st = ParserState(out_root)
    st.base_dir = base_dir
    st.trusted_templates = load_trusted_templates(base_dir)
    lines = schema_text.splitlines()

    # First pass: extract metadata and variables
    _extract_metadata_and_vars(lines, st, verbose)

    # Second pass: parse structure
    i = 0
    while i < len(lines):
        try:
            i = _parse_line(lines, i, st, base_dir, verbose)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(
                i + 1, f"Unexpected error: {e}", lines[i] if i < len(lines) else ""
            )

    # Apply ignore patterns
    if st.ignores:
        st.actions = _filter_ignored_actions(st.actions, st.ignores, verbose)

    return coalesce_mkdirs(st.actions), st.meta, st.vars


def _extract_metadata_and_vars(lines: List[str], st: ParserState, verbose: bool) -> None:
    """Extract metadata comments and variable directives in first pass."""
    for i, raw in enumerate(lines):
        line = raw.rstrip()
        if not line.strip():
            continue

        stripped = line.strip()

        # Metadata comments
        if stripped.startswith("#"):
            body = stripped.lstrip("#").strip()
            for key in ("Project", "Description", "Version"):
                pref = f"{key}:"
                if body.lower().startswith(pref.lower()):
                    val = body[len(pref):].strip()
                    if val:
                        st.meta[key] = val
                        # Also set corresponding variable
                        st.vars[key.upper()] = val
                        if verbose:
                            print(f"[META] {key}: {val}")
            continue

        # Variable directives
        if stripped.startswith("@set "):
            try:
                body = stripped[len("@set "):].strip()
                if "=" not in body:
                    continue
                k, v = body.split("=", 1)
                key = k.strip()
                value = v.strip()
                st.vars[key] = value
                if verbose:
                    print(f"[VAR] @set {key} = {value}")
            except Exception:
                continue  # Silently skip malformed @set in first pass


def _parse_line(
    lines: List[str], index: int, st: ParserState, base_dir: Path, verbose: bool
) -> int:
    """Parse a single line and return next line index."""
    raw = lines[index]
    line_num = index + 1

    if not raw.strip():
        return index + 1

    if raw.lstrip().startswith("#"):
        return index + 1

    # Handle directives
    stripped = raw.strip()
    if stripped.startswith("@"):
        return _handle_directive(stripped, st, base_dir, line_num, verbose, index)

    # Handle heredoc continuation
    if st.heredoc_stack:
        return _handle_heredoc_continuation(raw, lines, index, st, line_num, verbose)

    # Parse indentation and adjust directory stack
    leading_spaces = len(raw) - len(raw.lstrip())
    _adjust_directory_stack(leading_spaces, st)

    entry = raw.strip()

    # Handle different entry types
    if entry.startswith("/"):
        return _handle_absolute_section(entry, st, line_num, verbose)
    elif entry.endswith("/") and "->" not in entry and "<<" not in entry:
        return _handle_directory(entry, leading_spaces, st, line_num, verbose)
    elif "<<" in entry:
        return _handle_heredoc_start(entry, lines, index, st, line_num, verbose)
    elif "->" in entry:
        return _handle_inline_file(entry, st, line_num, verbose)
    else:
        return _handle_plain_file(entry, st, line_num, verbose)


def _adjust_directory_stack(leading_spaces: int, st: ParserState) -> None:
    """Adjust directory stack based on indentation changes."""
    # Pop stack until we find matching indentation level
    while st.indent_stack and leading_spaces < st.indent_stack[-1]:
        st.indent_stack.pop()
        st.dir_stack.pop()

    # Push new level if indentation increased
    if leading_spaces > st.indent_stack[-1]:
        st.indent_stack.append(leading_spaces)


def _handle_absolute_section(
    entry: str, st: ParserState, line_num: int, verbose: bool
) -> int:
    """Handle absolute section starting with /."""
    section = entry.lstrip("/")
    if section.endswith("/"):
        section = section[:-1]

    section = expand_vars(section, st.vars)
    new_dir = st.out_root / Path(section)
    st.actions.append(Action("mkdir", new_dir))

    # Update directory stack
    if st.indent_stack[-1] == (len(entry) - len(entry.lstrip())):
        st.dir_stack[-1] = new_dir
    else:
        st.dir_stack.append(new_dir)

    if verbose:
        print(f"[PARSE] L{line_num}: enter /{section}")
    return line_num


def _handle_directory(
    entry: str, leading_spaces: int, st: ParserState, line_num: int, verbose: bool
) -> int:
    """Handle directory declaration."""
    dir_name = expand_vars(entry[:-1].strip(), st.vars)
    new_dir = st.current_dir() / dir_name
    st.actions.append(Action("mkdir", new_dir))

    # Update directory stack
    if st.indent_stack and (leading_spaces > st.indent_stack[-1]):
        st.dir_stack.append(new_dir)
    else:
        st.dir_stack[-1] = new_dir

    if verbose:
        print(f"[PARSE] L{line_num}: dir {new_dir}")
    return line_num


def _handle_heredoc_start(
    entry: str,
    lines: List[str],
    index: int,
    st: ParserState,
    line_num: int,
    verbose: bool,
) -> int:
    """Handle heredoc start with <<."""
    left, marker = entry.split("<<", 1)
    file_name = expand_vars(left.strip(), st.vars)
    marker = marker.strip() or "EOF"
    target_path = st.current_dir() / file_name

    # Security check for file extensions
    if not validate_file_extension(file_name):
        raise ParseError(
            line_num, f"Potentially dangerous file extension: {file_name}", entry
        )

    # Start heredoc parsing
    st.heredoc_stack.append((marker, target_path, line_num))
    return index + 1


def _handle_heredoc_continuation(
    raw: str,
    lines: List[str],
    index: int,
    st: ParserState,
    line_num: int,
    verbose: bool,
) -> int:
    """Handle lines within a heredoc block."""
    if not st.heredoc_stack:
        return index + 1

    marker, target_path, start_line = st.heredoc_stack[-1]

    # Check for heredoc end marker
    if raw.strip() == marker:
        # End of heredoc - create the file
        content_lines = lines[start_line:index]
        content = "\n".join(content_lines)
        content = expand_vars(content, st.vars)
        content = normalize_line_endings(content)

        st.actions.append(Action("write", target_path, content))

        # Add executable permission for script files
        if not IS_WINDOWS and target_path.suffix in (".sh", ".py", ".pl", ".rb"):
            st.actions.append(Action("chmod", target_path, mode=0o755))

        if verbose:
            print(
                f"[PARSE] L{start_line}-{line_num-1}: heredoc {target_path} ({len(content)} bytes)"
            )

        st.heredoc_stack.pop()
        return index + 1
    else:
        # Continue collecting heredoc content
        return index + 1


def _handle_inline_file(
    entry: str, st: ParserState, line_num: int, verbose: bool
) -> int:
    """Handle inline file with -> syntax."""
    left, right = entry.split("->", 1)
    file_name = expand_vars(left.strip(), st.vars)
    content = expand_vars(right.lstrip(), st.vars)
    content = normalize_line_endings(content)

    # Security check
    if not validate_file_extension(file_name):
        raise ParseError(
            line_num, f"Potentially dangerous file extension: {file_name}", entry
        )

    target_path = st.current_dir() / file_name
    st.actions.append(Action("write", target_path, content))

    # Add executable permission for script files
    if not IS_WINDOWS and target_path.suffix in (".sh", ".py", ".pl", ".rb"):
        st.actions.append(Action("chmod", target_path, mode=0o755))

    if verbose:
        print(f"[PARSE] L{line_num}: file {target_path} (inline, {len(content)} chars)")
    return line_num + 1


def _handle_plain_file(
    entry: str, st: ParserState, line_num: int, verbose: bool
) -> int:
    """Handle plain file declaration."""
    file_name = expand_vars(entry, st.vars)

    # Security check
    if not validate_file_extension(file_name):
        raise ParseError(
            line_num, f"Potentially dangerous file extension: {file_name}", entry
        )

    target_path = st.current_dir() / file_name

    # Ensure parent directory exists
    st.actions.append(Action("mkdir", target_path.parent))
    st.actions.append(Action("write", target_path, ""))

    # Add executable permission for script files
    if not IS_WINDOWS and target_path.suffix in (".sh", ".py", ".pl", ".rb"):
        st.actions.append(Action("chmod", target_path, mode=0o755))

    if verbose:
        print(f"[PARSE] L{line_num}: file {target_path} (empty)")
    return line_num + 1


def _handle_directive(
    line: str, st: ParserState, base_dir: Path, line_num: int, verbose: bool, index: int
) -> int:
    """Handle @ directives."""
    try:
        if line.startswith("@set "):
            body = line[len("@set "):].strip()
            if "=" not in body:
                raise ParseError(
                    line_num, "Invalid @set syntax, use: @set KEY=VALUE", line
                )
            k, v = body.split("=", 1)
            key = k.strip()
            value = v.strip()
            st.vars[key] = value
            if verbose:
                print(f"[DIRECTIVE] @set {key} = {value}")

        elif line.startswith("@include "):
            inc_file = expand_vars(line[len("@include "):].strip(), st.vars)
            inc_path = (base_dir / inc_file).resolve()

            # Security check for included files
            if not is_safe_under_base(inc_path, base_dir):
                raise ParseError(
                    line_num, f"Included file path traversal detected: {inc_file}", line
                )

            if not inc_path.exists():
                raise ParseError(line_num, f"Included file not found: {inc_file}", line)

            verify_include_signature(inc_path, line_num, line, verbose)

            included_text = inc_path.read_text(encoding="utf-8")
            included_actions, _, included_vars = parse_schema(
                included_text, st.out_root, inc_path.parent, verbose
            )
            st.actions.extend(included_actions)
            st.vars.update(included_vars)  # Merge variables
            if verbose:
                print(f"[DIRECTIVE] @include {inc_path}")

        elif line.startswith("@ignore"):
            patterns = line.split()[1:]
            st.ignores.extend(patterns)
            if verbose:
                print(f"[DIRECTIVE] @ignore {patterns}")

        elif line.startswith("@chmod "):
            rest = line[len("@chmod "):].strip()
            parts = rest.split()
            if len(parts) < 2:
                raise ParseError(
                    line_num, "Invalid @chmod syntax, use: @chmod PATH MODE", line
                )
            path_str = parts[0]
            mode_str = parts[1]
            target_path = st.out_root / expand_vars(path_str, st.vars)
            mode = _parse_chmod_mode(mode_str)
            st.actions.append(Action("chmod", target_path, mode=mode))
            if verbose:
                print(f"[DIRECTIVE] @chmod {target_path} {oct(mode)}")

        elif line.startswith("@copy "):
            rest = line[len("@copy "):].strip()
            parts = rest.split()
            if len(parts) < 2:
                raise ParseError(
                    line_num, "Invalid @copy syntax, use: @copy SRC DEST", line
                )
            src_str, dest_str = parts[0], parts[1]
            src_path = (base_dir / expand_vars(src_str, st.vars)).resolve()
            dest_path = (st.out_root / expand_vars(dest_str, st.vars)).resolve()

            # Security checks
            if not is_safe_under_base(src_path, base_dir):
                raise ParseError(
                    line_num, f"Copy source path traversal detected: {src_str}", line
                )
            if not is_safe_under_base(dest_path, st.out_root):
                raise ParseError(
                    line_num,
                    f"Copy destination path traversal detected: {dest_str}",
                    line,
                )

            if not src_path.exists():
                raise ParseError(line_num, f"Copy source not found: {src_path}", line)
            st.actions.append(Action("copy", dest_path, src=src_path))
            if verbose:
                print(f"[DIRECTIVE] @copy {src_path} -> {dest_path}")

        elif line.startswith("@template "):
            name = line[len("@template "):].strip()
            if st.trusted_templates is not None and name not in st.trusted_templates:
                raise ParseError(line_num, f"Template '{name}' is not trusted", line)
            template_acts = template_actions(name, st.out_root, st.vars)
            st.actions.extend(template_acts)
            if verbose:
                print(f"[DIRECTIVE] @template {name} ({len(template_acts)} actions)")

        elif line.startswith("@symlink "):
            rest = line[len("@symlink "):].strip()
            parts = rest.split()
            if len(parts) < 2:
                raise ParseError(
                    line_num,
                    "Invalid @symlink syntax, use: @symlink TARGET LINKNAME",
                    line,
                )
            target_str, link_str = parts[0], parts[1]
            target_path = Path(expand_vars(target_str, st.vars))
            link_path = st.out_root / expand_vars(link_str, st.vars)

            # Security check
            if not is_safe_under_base(link_path, st.out_root):
                raise ParseError(
                    line_num, f"Symlink path traversal detected: {link_str}", line
                )

            st.actions.append(Action("symlink", link_path, target=target_path))
            if verbose:
                print(f"[DIRECTIVE] @symlink {target_path} -> {link_path}")

        else:
            raise ParseError(line_num, f"Unknown directive: {line.split()[0]}", line)

    except ParseError:
        raise
    except Exception as e:
        raise ParseError(line_num, f"Directive error: {e}", line)

    return index + 1


def _parse_chmod_mode(mode_str: str) -> int:
    """Parse chmod mode string into integer."""
    if mode_str.startswith("+"):
        if "x" in mode_str:
            return 0o755
        elif "w" in mode_str:
            return 0o644
        else:
            return 0o644
    else:
        try:
            if mode_str.startswith("0o"):
                return int(mode_str, 8)
            else:
                return int(mode_str, 8)
        except ValueError:
            # Default to readable
            return 0o644


def _filter_ignored_actions(
    actions: List[Action], ignores: List[str], verbose: bool
) -> List[Action]:
    """Filter actions based on ignore patterns."""
    filtered = []
    for act in actions:
        skip = False
        rel_path = str(act.path)
        for pattern in ignores:
            if pattern in rel_path or fnmatch.fnmatch(rel_path, pattern):
                skip = True
                if verbose:
                    print(f"[FILTER] ignore {act.path} (pattern: {pattern})")
                break
        if not skip:
            filtered.append(act)
    return filtered


def coalesce_mkdirs(actions: List[Action]) -> List[Action]:
    """Remove redundant mkdir actions."""
    seen_dirs = set()
    result = []

    for act in actions:
        if act.kind == "mkdir":
            if act.path not in seen_dirs:
                seen_dirs.add(act.path)
                result.append(act)
        else:
            result.append(act)

    return result


# ----------------------------- Realization ---------------------------------

def realize(
    actions: List[Action],
    base_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    verbose: bool = False,
) -> GenerationResult:
    """
    Execute actions to create the repository structure with enhanced security.
    
    Args:
        actions: List of actions to perform
        base_dir: Base directory for security checks
        dry_run: If True, only show what would be done
        force: If True, overwrite existing files
        verbose: Enable verbose output
        
    Returns:
        GenerationResult with success status and messages
    """
    success = True
    actions_performed = 0
    errors: List[str] = []
    warnings: List[str] = []

    for act in actions:
        try:
            # Enhanced security check
            if not is_safe_under_base(act.path, base_dir):
                error_msg = f"Skipping unsafe path: {act.path}"
                errors.append(error_msg)
                if verbose:
                    print(f"[SECURITY] {error_msg}")
                continue

            if act.kind == "mkdir":
                if verbose or dry_run:
                    print(f"[{'DRY' if dry_run else 'MKDIR'}] {act.path}")
                if not dry_run:
                    act.path.mkdir(parents=True, exist_ok=True)
                    actions_performed += 1

            elif act.kind == "write":
                if verbose or dry_run:
                    size = len(act.content or "")
                    print(
                        f"[{'DRY' if dry_run else 'WRITE'}] {act.path} ({size} bytes)"
                    )
                if not dry_run:
                    if act.path.exists() and not force:
                        warning_msg = f"Skipping existing file (use --force to overwrite): {act.path}"
                        warnings.append(warning_msg)
                        if verbose:
                            print(f"[WARN] {warning_msg}")
                        continue
                    act.path.parent.mkdir(parents=True, exist_ok=True)
                    act.path.write_text(act.content or "", encoding="utf-8")
                    actions_performed += 1

            elif act.kind == "chmod":
                if verbose or dry_run:
                    print(
                        f"[{'DRY' if dry_run else 'CHMOD'}] {act.path} {oct(act.mode or 0o644)}"
                    )
                if not dry_run and not IS_WINDOWS:
                    act.path.chmod(act.mode or 0o644)
                    actions_performed += 1

            elif act.kind == "copy":
                if verbose or dry_run:
                    print(f"[{'DRY' if dry_run else 'COPY'}] {act.src} -> {act.path}")
                if not dry_run:
                    if act.path.exists() and not force:
                        warning_msg = f"Skipping existing file (use --force to overwrite): {act.path}"
                        warnings.append(warning_msg)
                        if verbose:
                            print(f"[WARN] {warning_msg}")
                        continue

                    # Security check for copy source
                    if not is_safe_under_base(act.src, base_dir):
                        error_msg = f"Skipping unsafe copy source: {act.src}"
                        errors.append(error_msg)
                        if verbose:
                            print(f"[SECURITY] {error_msg}")
                        continue

                    act.path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(act.src, act.path)
                    actions_performed += 1

            elif act.kind == "symlink":
                if verbose or dry_run:
                    print(
                        f"[{'DRY' if dry_run else 'SYMLINK'}] {act.target} -> {act.path}"
                    )
                if not dry_run:
                    if act.path.exists():
                        if force:
                            act.path.unlink()
                        else:
                            warning_msg = f"Skipping existing symlink (use --force to overwrite): {act.path}"
                            warnings.append(warning_msg)
                            if verbose:
                                print(f"[WARN] {warning_msg}")
                            continue
                    act.path.parent.mkdir(parents=True, exist_ok=True)
                    act.path.symlink_to(act.target)
                    actions_performed += 1

        except Exception as e:
            error_msg = f"Failed to {act.kind} {act.path}: {e}"
            errors.append(error_msg)
            print(f"[ERROR] {error_msg}")
            success = False

    return GenerationResult(
        success=success and len(errors) == 0,
        actions_performed=actions_performed,
        errors=errors,
        warnings=warnings,
    )


# ----------------------------- Bootstrap -----------------------------------

def detect_install_bin() -> Path:
    """Detect appropriate bin directory for installation."""
    if IS_TERMUX:
        return Path("/data/data/com.termux/files/usr/bin")
    elif IS_WINDOWS:
        # Try common Windows locations
        for candidate in [
            Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps",
            Path.home() / "AppData" / "Local" / "Programs" / "Python",
            Path.home() / "AppData" / "Local" / "bin",
        ]:
            if candidate.exists():
                return candidate
        return Path.home() / "AppData" / "Local" / "bin"
    else:
        # Unix-like systems
        return Path.home() / ".local" / "bin"


def persist_path(bin_dir: Path, verbose: bool = False) -> None:
    """Persist PATH configuration for various shells."""
    export_line = f'export PATH="{bin_dir}:$PATH"'

    shell_rc_files = {
        "zsh": [Path.home() / ".zshrc", Path.home() / ".zprofile"],
        "bash": [
            Path.home() / ".bashrc",
            Path.home() / ".bash_profile",
            Path.home() / ".profile",
        ],
        "fish": [Path.home() / ".config" / "fish" / "config.fish"],
        "default": [Path.home() / ".profile"],
    }

    def add_to_file(file_path: Path, content: str):
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch(exist_ok=True)

            current_content = file_path.read_text(encoding="utf-8")
            if content not in current_content:
                with file_path.open("a", encoding="utf-8") as f:
                    f.write(f"\n# Added by lrc bootstrap\n{content}\n")
                if verbose:
                    print(f"[PATH] Added to {file_path}")
            else:
                if verbose:
                    print(f"[PATH] Already in {file_path}")
        except Exception as e:
            if verbose:
                print(f"[WARN] Could not update {file_path}: {e}")

    # Detect shell and update appropriate files
    shell = (
        os.environ.get("SHELL", "").split("/")[-1]
        if "SHELL" in os.environ
        else "default"
    )

    target_files = shell_rc_files.get(shell, shell_rc_files["default"])
    for rc_file in target_files:
        add_to_file(rc_file, export_line)


def do_bootstrap(argv0: str, verbose: bool = False) -> Path:
    """
    Bootstrap installation of lrc to user bin directory.
    
    Args:
        argv0: Path to current script
        verbose: Enable verbose output
        
    Returns:
        Path to installed executable
        
    Raises:
        Exception: If installation fails
    """
    bin_dir = detect_install_bin()
    bin_dir.mkdir(parents=True, exist_ok=True)

    # Determine target name
    target_name = "lrc.exe" if IS_WINDOWS else "lrc"
    target_path = bin_dir / target_name

    # Copy current script
    source_path = Path(argv0).resolve()
    if not source_path.exists():
        # Fallback to __file__
        source_path = Path(__file__).resolve()

    print(f"[BOOTSTRAP] Installing lrc to {target_path}")

    try:
        shutil.copy2(source_path, target_path)

        # Make executable on Unix-like systems
        if not IS_WINDOWS:
            target_path.chmod(0o755)

        print(f"[SUCCESS] Installed to {target_path}")

        # Update PATH configuration
        persist_path(bin_dir, verbose)
        print(f"[PATH] Added {bin_dir} to PATH configuration")
        print(f"[INFO] Restart your shell or run: source ~/.profile")

        return target_path

    except Exception as e:
        print(f"[ERROR] Installation failed: {e}")
        raise


# ----------------------------- Main CLI ------------------------------------

def main() -> int:
    """Compatibility wrapper around the refactored CLI module."""
    from .cli import main as cli_main
    return cli_main()


if __name__ == "__main__":
    sys.exit(main())


FILE: src/lrc/generator.py
Kind: text
Size: 4768
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""Apply compiled actions to the filesystem."""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .compiler import BuildPlan, build_metadata
from .parser import Action, is_safe_under_base

__all__ = ["GenerationResult", "realize", "write_build_manifest"]


@dataclass
class GenerationResult:
    success: bool
    created_paths: List[Path]


def realize(
    plan: BuildPlan,
    output_dir: Path,
    *,
    dry_run: bool = False,
    force: bool = False,
    verbose: bool = False,
) -> GenerationResult:
    created: List[Path] = []
    success = True

    for action in plan.actions:
        path = action.path
        if not is_safe_under_base(path, output_dir):
            print(f"[SECURITY] Skipping unsafe path: {path}")
            success = False
            continue

        if action.kind == "mkdir":
            if verbose or dry_run:
                print(f"[{'DRY' if dry_run else 'mkdir'}] {path}")
            if dry_run:
                continue
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)
            continue

        if action.kind == "write":
            if verbose or dry_run:
                size = len(action.content or "")
                print(f"[{'DRY' if dry_run else 'write'}] {path} ({size} bytes)")
            if dry_run:
                continue
            if path.exists() and not force:
                print(f"[WARN] Skipping existing file (use --force to overwrite): {path}")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(action.content or "", encoding="utf-8")
            created.append(path)
            continue

        if action.kind == "chmod":
            if verbose or dry_run:
                print(f"[{'DRY' if dry_run else 'chmod'}] {path} {oct(action.mode or 0o644)}")
            if dry_run:
                continue
            if os.name != "nt":
                try:
                    path.chmod(action.mode or 0o644)
                except FileNotFoundError:
                    pass
            continue

        if action.kind == "copy":
            if verbose or dry_run:
                print(f"[{'DRY' if dry_run else 'copy'}] {action.src} -> {path}")
            if dry_run:
                continue
            if path.exists() and not force:
                print(f"[WARN] Skipping existing file (use --force to overwrite): {path}")
                continue
            if not action.src or not action.src.exists():
                print(f"[ERROR] Copy source missing: {action.src}")
                success = False
                continue
            if not is_safe_under_base(action.src, action.src.parent):
                print(f"[SECURITY] Skipping unsafe copy source: {action.src}")
                success = False
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(action.src, path)
            created.append(path)
            continue

        if action.kind == "symlink":
            if verbose or dry_run:
                print(f"[{'DRY' if dry_run else 'symlink'}] {action.target} -> {path}")
            if dry_run:
                continue
            if path.exists():
                if force:
                    if path.is_symlink() or path.is_file():
                        path.unlink()
                else:
                    print(
                        f"[WARN] Skipping existing symlink (use --force to overwrite): {path}"
                    )
                    continue
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                path.symlink_to(action.target)
            except OSError as exc:
                print(f"[ERROR] Failed to create symlink {path}: {exc}")
                success = False
            else:
                created.append(path)
            continue

        print(f"[WARN] Unknown action kind: {action.kind}")

    return GenerationResult(success=success, created_paths=created)


def write_build_manifest(
    plan: BuildPlan,
    output_dir: Path,
    *,
    dry_run: bool,
    audit_summary: Optional[Dict[str, object]] = None,
) -> Optional[Path]:
    if dry_run:
        return None
    manifest_path = output_dir / ".lrc-build.json"
    manifest = build_metadata(plan)
    manifest.update(
        {
            "output": str(output_dir),
            "timestamp": int(time.time()),
        }
    )
    if audit_summary is not None:
        manifest["audit"] = audit_summary
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path


FILE: src/lrc/generator/__init__.py
Kind: text
Size: 531
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""Template and code generation helpers for LRC."""

from __future__ import annotations

from typing import Dict, List
from pathlib import Path

from ..core import template_actions as _template_actions
from ..core import expand_vars as _expand_vars

__all__ = ["template_actions", "expand_vars"]


def template_actions(name: str, root: Path, vars_: Dict[str, str]) -> List["Action"]:
    return _template_actions(name, root, vars_)


def expand_vars(value: str, vars_: Dict[str, str]) -> str:
    return _expand_vars(value, vars_)


FILE: src/lrc/integration.py
Kind: text
Size: 4098
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""DAT integration helpers for the LRC CLI."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional

from .compiler import BuildPlan

CONFIG_PATH = Path.home() / ".config" / "lrc" / "dat_integration.json"
DEFAULT_CONFIG = {
    "version": "1",
    "dat_exec": "dat",
    "audit_defaults": {
        "ignore": [".git", "__pycache__", ".venv", "node_modules"],
        "max_lines": 1000,
        "max_size": 10485760,
    },
    "gpg": {"enable_signing": True, "signing_key": ""},
}


def ensure_dat_config(verbose: bool = False) -> Dict[str, object]:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    if verbose:
        print(f"[audit] created integration config at {CONFIG_PATH}")
    return DEFAULT_CONFIG.copy()


def run_dat_audit(
    plan: BuildPlan,
    output_dir: Path,
    *,
    audit_out: Optional[Path] = None,
    audit_format: str = "json",
    audit_args: str = "",
    verbose: bool = False,
) -> Dict[str, object]:
    config = ensure_dat_config(verbose=verbose)
    dat_exec = str(config.get("dat_exec", "dat"))
    audit_format = audit_format.lower()

    command = [dat_exec, "--from-lrc", str(output_dir)]

    if audit_args:
        command.extend(shlex.split(audit_args))

    started = time.time()
    mocked = False
    exit_code = 0
    stdout = ""
    stderr = ""

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        exit_code = result.returncode
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
    except FileNotFoundError:
        mocked = True
        exit_code = 127
        stderr = "dat executable not found; using mocked audit"
    except OSError as exc:
        mocked = True
        exit_code = 127
        stderr = f"failed to execute dat: {exc}"

    duration = time.time() - started
    summary: Dict[str, object] = {
        "command": command,
        "exit_code": exit_code,
        "duration": duration,
        "timestamp": int(started),
        "mocked": mocked,
        "stdout": stdout,
        "stderr": stderr,
        "defaults": config.get("audit_defaults", {}),
        "project": plan.project_name,
    }

    audit_path = output_dir / ".lrc-audit.json"
    audit_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    if audit_format in {"pdf", "combined"}:
        pdf_path = output_dir / "audit.pdf"
        pdf_path.write_text("DAT audit placeholder PDF", encoding="utf-8")
        if config.get("gpg", {}).get("enable_signing"):
            asc_path = output_dir / "audit.pdf.asc"
            asc_path.write_text("signed-placeholder", encoding="utf-8")
    if audit_format in {"md", "combined"}:
        md_path = output_dir / "audit.md"
        md_path.write_text("# DAT Audit\n\nThis is a placeholder report.", encoding="utf-8")

    if audit_out:
        audit_out.parent.mkdir(parents=True, exist_ok=True)
        if audit_format == "json":
            audit_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        elif audit_format == "pdf":
            audit_out.write_text("DAT audit placeholder PDF", encoding="utf-8")
        elif audit_format == "md":
            audit_out.write_text("# DAT Audit\n\nPlaceholder report.", encoding="utf-8")
        elif audit_format == "combined":
            base = audit_out
            audit_out_json = base.with_suffix(".json")
            audit_out_pdf = base.with_suffix(".pdf")
            audit_out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            audit_out_pdf.write_text("DAT audit placeholder PDF", encoding="utf-8")

    if verbose:
        status = "mocked" if mocked else "completed"
        print(f"[audit] {status} with exit code {exit_code}")

    return summary


FILE: src/lrc/main.py
Kind: text
Size: 8549
Last modified: 2026-01-21T07:58:23Z

CONTENT:
#!/usr/bin/env python3
"""LRC (Local Repo Compiler) CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .bootstrap import do_bootstrap
from .compiler import (
    check_fs_ok, 
    compile_schema_path, 
    print_platform_info, 
    resolve_output_directory
)
from .generator import realize, write_build_manifest
from .integration import run_dat_audit


def build_parser() -> argparse.ArgumentParser:
    """Build the command line argument parser for LRC."""
    parser = argparse.ArgumentParser(
        prog="lrc",
        description="Local Repo Compiler — Build repositories from declarative schemas",
        epilog="""
Examples:
  lrc schema.yaml                    # Generate project from schema
  lrc schema.yaml --out ./my-project # Specify output directory
  lrc schema.yaml --dry-run          # Preview without writing files
  lrc schema.yaml --audit            # Run security audit after generation
  lrc --bootstrap                    # Install LRC to user PATH
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Core arguments
    parser.add_argument(
        "schema", 
        nargs="?", 
        help="Path to the .lrc schema file (YAML or JSON)"
    )
    
    # Information and setup
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"lrc {__version__}"
    )
    parser.add_argument(
        "--bootstrap", 
        action="store_true", 
        help="Install LRC into the user PATH"
    )
    parser.add_argument(
        "--platform-info",
        action="store_true",
        help="Print detected platform information and exit"
    )
    
    # Generation options
    parser.add_argument(
        "-o", "--out", 
        type=Path, 
        help="Output directory for generated project"
    )
    parser.add_argument(
        "-n", "--dry-run", 
        action="store_true", 
        help="Do not modify the filesystem, only show planned actions"
    )
    parser.add_argument(
        "-f", "--force", 
        action="store_true", 
        help="Overwrite existing files and directories"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    # Audit integration
    audit_group = parser.add_argument_group('audit options')
    audit_group.add_argument(
        "--audit", 
        action="store_true", 
        help="Run DAT security audit after generation"
    )
    audit_group.add_argument(
        "--audit-out", 
        type=Path, 
        help="Path to write audit artifact"
    )
    audit_group.add_argument(
        "--audit-format",
        choices=["json", "pdf", "md", "combined"],
        default="json",
        help="Audit artifact format (default: %(default)s)"
    )
    audit_group.add_argument(
        "--audit-args", 
        default="",
        help="Additional arguments forwarded to DAT"
    )
    
    # Backwards compatibility
    parser.add_argument(
        "--audit-out-format",
        dest="audit_format",
        choices=["json", "pdf", "md", "combined"],
        help=argparse.SUPPRESS,  # Hidden for backwards compatibility
    )
    
    return parser


def validate_args(args: argparse.Namespace) -> tuple[bool, str]:
    """
    Validate command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for conflicting audit format arguments
    if hasattr(args, 'audit_out_format') and args.audit_out_format:
        args.audit_format = args.audit_out_format
    
    # Validate schema file exists when required
    if args.schema and not Path(args.schema).exists():
        return False, f"schema file not found: {args.schema}"
    
    # Validate output directory permissions
    if args.out and args.out.exists() and not args.out.is_dir():
        return False, f"output path exists but is not a directory: {args.out}"
    
    return True, ""


def main(argv: Optional[list[str]] = None) -> int:
    """
    Main entry point for LRC CLI.
    
    Args:
        argv: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    
    # Handle information commands first
    if args.platform_info:
        print_platform_info(verbose=args.verbose)
        return 0

    if args.bootstrap:
        try:
            target = do_bootstrap(sys.argv[0], verbose=args.verbose)
            print(f"✓ Installed LRC to {target}")
            return 0
        except Exception as e:
            print(f"✗ Bootstrap failed: {e}", file=sys.stderr)
            return 1

    # Validate arguments
    is_valid, error_msg = validate_args(args)
    if not is_valid:
        parser.error(error_msg)

    # Schema is required for generation commands
    if not args.schema:
        parser.error("a schema path is required unless using --platform-info or --bootstrap")

    schema_path = Path(args.schema)
    output_hint = args.out

    try:
        # Compile schema into execution plan
        plan = compile_schema_path(
            schema_path, 
            output_hint or Path.cwd(), 
            verbose=args.verbose
        )
    except FileNotFoundError:
        parser.error(f"schema file not found: {schema_path}")
    except Exception as exc:
        print(f"[ERROR] Failed to compile schema: {exc}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Resolve output directory
    try:
        output_dir = resolve_output_directory(plan, output_hint)
        if output_dir != plan.root:
            plan = plan.rebase(output_dir)
    except Exception as exc:
        print(f"[ERROR] Failed to resolve output directory: {exc}", file=sys.stderr)
        return 2

    # Check filesystem permissions
    ok, reason = check_fs_ok(output_dir)
    if not ok:
        print(f"[ERROR] Output directory not writable: {reason}", file=sys.stderr)
        return 3

    if args.verbose:
        print(f"[PLAN] Generating project to: {output_dir}")
        print(f"[PLAN] Total operations: {len(plan.operations)}")

    # Execute generation plan
    try:
        result = realize(
            plan, 
            output_dir, 
            dry_run=args.dry_run, 
            force=args.force, 
            verbose=args.verbose
        )
    except Exception as exc:
        print(f"[ERROR] Generation failed: {exc}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 4

    # Run DAT audit if requested
    audit_summary = None
    if args.audit and not args.dry_run:
        if args.verbose:
            print("[AUDIT] Running security audit...")
        
        try:
            audit_summary = run_dat_audit(
                plan,
                output_dir,
                audit_out=args.audit_out,
                audit_format=args.audit_format,
                audit_args=args.audit_args,
                verbose=args.verbose,
            )
            
            if args.verbose and audit_summary:
                print(f"[AUDIT] Completed with {audit_summary.get('violations', 0)} violations")
                
        except Exception as exc:
            print(f"[WARNING] Audit failed: {exc}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()

    # Write build manifest
    try:
        manifest_path = write_build_manifest(
            plan, 
            output_dir, 
            dry_run=args.dry_run, 
            audit_summary=audit_summary
        )
        
        if args.verbose and manifest_path:
            print(f"[INFO] Build manifest written to: {manifest_path}")
            
    except Exception as exc:
        print(f"[WARNING] Failed to write build manifest: {exc}", file=sys.stderr)

    # Report results
    if args.verbose:
        if result.success:
            if args.dry_run:
                print("✓ Dry run completed successfully")
            else:
                print("✓ Project generation completed successfully")
        else:
            print("✗ Project generation completed with errors")

    return 0 if result.success else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


FILE: src/lrc/parser.py
Kind: text
Size: 22744
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""Schema parsing utilities for LRC.

This module converts declarative ``.lrc`` schema files into a sequence of
filesystem actions that later stages of the compiler can realise.  It handles
variable expansion, heredocs, nested includes, template expansion, ignore
patterns and security enforcement for paths and file types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import fnmatch
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Dict, Iterable, List, Literal, Optional, Tuple

try:
    from importlib import resources as importlib_resources
except ImportError:  # pragma: no cover - Python <3.9 fallback
    import importlib_resources  # type: ignore


__all__ = [
    "Action",
    "GPGReport",
    "ParseError",
    "ParserResult",
    "coalesce_mkdirs",
    "detect_signature_file",
    "expand_vars",
    "is_safe_under_base",
    "load_trusted_templates",
    "normalize_line_endings",
    "parse_schema",
    "validate_file_extension",
]


SYSTEM = os.uname().sysname.lower() if hasattr(os, "uname") else "windows"
IS_WINDOWS = SYSTEM.startswith("win")

DEFAULT_TRUSTED_TEMPLATES = {
    "python-cli",
    "node-cli",
    "rust-cli",
}

REQUIRE_SIGNED_IMPORTS = (
    os.environ.get("LRC_REQUIRE_SIGNED_INCLUDES", "").lower() in {"1", "true", "yes"}
)


@dataclass
class Action:
    """Filesystem action produced by the parser/ compiler."""

    kind: Literal["mkdir", "write", "chmod", "copy", "symlink"]
    path: Path
    content: Optional[str] = None
    mode: Optional[int] = None
    src: Optional[Path] = None
    target: Optional[Path] = None


@dataclass
class GPGReport:
    """Result of verifying a schema or include signature."""

    path: str
    verified: bool
    signature: Optional[str] = None
    message: Optional[str] = None


@dataclass
class ParserResult:
    """Container for the parser output."""

    actions: List[Action]
    metadata: Dict[str, Optional[str]]
    variables: Dict[str, str]
    ignores: List[str]
    gpg_reports: List[GPGReport] = field(default_factory=list)


@dataclass
class ParseError(Exception):
    """Exception raised for schema parsing issues."""

    line_num: int
    message: str
    line_content: str = ""

    def __str__(self) -> str:  # pragma: no cover - convenience
        if self.line_content:
            return f"Line {self.line_num}: {self.message}\n  {self.line_content}"
        return f"Line {self.line_num}: {self.message}"


class ParserState:
    """Internal mutable state used while parsing a schema."""

    def __init__(self, out_root: Path):
        self.out_root = out_root
        self.dir_stack: List[Path] = [out_root]
        self.indent_stack: List[int] = [0]
        self.actions: List[Action] = []
        self.meta: Dict[str, Optional[str]] = {
            "Project": None,
            "Description": None,
            "Version": None,
        }
        self.vars: Dict[str, str] = {
            "AUTHOR": "",
            "PROJECT": "",
            "DESCRIPTION": "",
            "VERSION": "",
            "PKG": "",
        }
        self.ignores: List[str] = []
        self.heredoc_stack: List[Tuple[str, Path, int]] = []  # (marker, path, start_index)
        self.trusted_templates: Optional[set[str]] = None
        self.base_dir: Path = out_root
        self.gpg_reports: List[GPGReport] = []

    def current_dir(self) -> Path:
        return self.dir_stack[-1]


# ---------------------------------------------------------------------------
# Utility helpers


def get_safe_path(path: Path) -> Path:
    try:
        return path.resolve()
    except (OSError, RuntimeError):  # pragma: no cover - fallback path handling
        return path.absolute()


def normalize_line_endings(content: str, target: Optional[str] = None) -> str:
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    if target is None:
        target = "windows" if IS_WINDOWS else "unix"
    if target == "windows":
        content = content.replace("\n", "\r\n")
    return content


def expand_vars(value: str, vars_: Dict[str, str]) -> str:
    if not value:
        return value

    pattern = re.compile(r"\$\{([^}]+)\}")

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return vars_.get(key, match.group(0))

    return pattern.sub(repl, value)


def validate_file_extension(filename: str) -> bool:
    dangerous = {
        ".exe",
        ".bat",
        ".cmd",
        ".sh",
        ".bin",
        ".app",
        ".dmg",
        ".pkg",
        ".deb",
        ".rpm",
        ".msi",
    }
    ext = Path(filename).suffix.lower()
    return ext not in dangerous


def is_safe_under_base(path: Path, base_dir: Path) -> bool:
    try:
        base_real = os.path.realpath(str(get_safe_path(base_dir)))
        target_real = os.path.realpath(str(get_safe_path(path)))
        return os.path.commonpath([base_real, target_real]) == base_real
    except (ValueError, OSError):
        return False


def load_trusted_templates(base_dir: Path) -> set[str]:
    candidates = [
        base_dir / "trusted_templates.json",
        base_dir / ".lrc" / "trusted_templates.json",
        Path.home() / ".config" / "lrc" / "trusted_templates.json",
        Path(__file__).resolve().parent.parent / "trusted_templates.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ParseError(0, f"Invalid trusted template policy: {candidate}", str(exc))
            if isinstance(data, list):
                return {str(item).strip() for item in data if str(item).strip()}
    return set(DEFAULT_TRUSTED_TEMPLATES)


# ---------------------------------------------------------------------------
# Signature validation helpers


def detect_signature_file(schema_path: Path) -> Optional[Path]:
    candidates = [
        schema_path.with_name(schema_path.name + ".asc"),
        schema_path.with_name(schema_path.name + ".sig"),
        schema_path.with_suffix(schema_path.suffix + ".asc"),
        schema_path.with_suffix(schema_path.suffix + ".sig"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def verify_include_signature(
    include_path: Path,
    st: ParserState,
    line_num: int,
    line: str,
    verbose: bool,
) -> None:
    signature = detect_signature_file(include_path)
    if not signature:
        if REQUIRE_SIGNED_IMPORTS:
            raise ParseError(line_num, f"No signature found for include: {include_path.name}", line)
        st.gpg_reports.append(
            GPGReport(path=str(include_path), verified=False, message="signature missing")
        )
        return

    if shutil.which("gpg") is None:
        raise ParseError(line_num, "GPG executable not available for signature verification", line)

    result = subprocess.run(
        ["gpg", "--verify", str(signature), str(include_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise ParseError(
            line_num,
            f"GPG signature verification failed for {include_path.name}",
            stderr or line,
        )
    st.gpg_reports.append(
        GPGReport(path=str(include_path), verified=True, signature=str(signature))
    )
    if verbose:
        print(f"[tag] verified signature {signature}")


# ---------------------------------------------------------------------------
# Template loading


def _iter_template_entries(name: str) -> Iterable[Tuple[str, Optional[str]]]:
    base = importlib_resources.files("lrc.templates").joinpath(name)
    if not base.is_dir():
        raise FileNotFoundError(name)

    stack = [(base, Path(""))]
    while stack:
        current, rel = stack.pop()
        for entry in current.iterdir():
            relative = rel / entry.name
            if entry.is_dir():
                yield str(relative) + "/", None
                stack.append((entry, relative))
            else:
                try:
                    text = entry.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    text = ""
                yield str(relative), text


def template_actions(name: str, st: ParserState, verbose: bool) -> List[Action]:
    acts: List[Action] = []
    normalized = name.lower().strip()
    if st.trusted_templates is not None and normalized not in st.trusted_templates:
        raise ParseError(0, f"Template '{name}' is not trusted", name)

    try:
        for rel_path, content in _iter_template_entries(normalized):
            rel_path = expand_vars(rel_path, st.vars)
            target = st.out_root / rel_path.strip("/")
            if rel_path.endswith("/"):
                acts.append(Action("mkdir", target))
            else:
                acts.append(Action("write", target, normalize_line_endings(content or "")))
                if not IS_WINDOWS and target.suffix in (".sh", ".py"):
                    acts.append(Action("chmod", target, mode=0o755))
        if verbose:
            print(f"[tag] @template {name} ({len(acts)} actions)")
    except FileNotFoundError:
        raise ParseError(0, f"Template '{name}' not found", name)
    return acts


# ---------------------------------------------------------------------------
# Parsing implementation


def parse_schema(
    schema_text: str,
    out_root: Path,
    base_dir: Path,
    *,
    verbose: bool = False,
) -> ParserResult:
    st = ParserState(out_root)
    st.base_dir = base_dir
    st.trusted_templates = load_trusted_templates(base_dir)
    lines = schema_text.splitlines()

    _extract_metadata_and_vars(lines, st, verbose)

    index = 0
    while index < len(lines):
        try:
            index = _parse_line(lines, index, st, base_dir, verbose)
        except ParseError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise ParseError(
                index + 1,
                f"Unexpected error: {exc}",
                lines[index] if index < len(lines) else "",
            )

    if st.ignores:
        st.actions = _filter_ignored_actions(st.actions, st.ignores, verbose)

    return ParserResult(
        actions=coalesce_mkdirs(st.actions),
        metadata=st.meta,
        variables=st.vars,
        ignores=st.ignores,
        gpg_reports=st.gpg_reports,
    )


def _extract_metadata_and_vars(lines: List[str], st: ParserState, verbose: bool) -> None:
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue

        stripped = line.strip()
        if stripped.startswith("#"):
            body = stripped.lstrip("#").strip()
            for key in ("Project", "Description", "Version"):
                prefix = f"{key}:"
                if body.lower().startswith(prefix.lower()):
                    value = body[len(prefix) :].strip()
                    if value:
                        st.meta[key] = value
                        st.vars[key.upper()] = value
                        if key == "Project" and not st.vars.get("PKG"):
                            st.vars["PKG"] = re.sub(r"[^a-zA-Z0-9]+", "-", value).lower()
            continue

        if stripped.startswith("@set "):
            body = stripped[len("@set ") :].strip()
            if "=" not in body:
                continue
            key, value = body.split("=", 1)
            key = key.strip()
            value = value.strip()
            st.vars[key] = value
            if verbose:
                print(f"[parse] @set {key} = {value}")


def _parse_line(
    lines: List[str],
    index: int,
    st: ParserState,
    base_dir: Path,
    verbose: bool,
) -> int:
    raw = lines[index]
    line_num = index + 1

    if not raw.strip() or raw.lstrip().startswith("#"):
        return index + 1

    stripped = raw.strip()
    if stripped.startswith("@"):
        return _handle_directive(stripped, st, base_dir, line_num, verbose, index, lines)

    if st.heredoc_stack:
        return _handle_heredoc_continuation(raw, lines, index, st, line_num, verbose)

    leading_spaces = len(raw) - len(raw.lstrip())
    _adjust_directory_stack(leading_spaces, st)

    entry = raw.strip()
    if entry.startswith("/"):
        return _handle_absolute_section(entry, st, line_num, verbose)
    if entry.endswith("/") and "->" not in entry and "<<" not in entry:
        return _handle_directory(entry, leading_spaces, st, line_num, verbose)
    if "<<" in entry:
        return _handle_heredoc_start(entry, lines, index, st, line_num, verbose)
    if "->" in entry:
        return _handle_inline_file(entry, st, line_num, verbose)
    return _handle_plain_file(entry, st, line_num, verbose)


def _adjust_directory_stack(leading_spaces: int, st: ParserState) -> None:
    while st.indent_stack and leading_spaces < st.indent_stack[-1]:
        st.indent_stack.pop()
        st.dir_stack.pop()

    if leading_spaces > st.indent_stack[-1]:
        st.indent_stack.append(leading_spaces)


def _handle_absolute_section(entry: str, st: ParserState, line_num: int, verbose: bool) -> int:
    section = entry.lstrip("/")
    if section.endswith("/"):
        section = section[:-1]
    section = expand_vars(section, st.vars)
    new_dir = st.out_root / Path(section)
    st.actions.append(Action("mkdir", new_dir))
    if st.indent_stack[-1] == (len(entry) - len(entry.lstrip())):
        st.dir_stack[-1] = new_dir
    else:
        st.dir_stack.append(new_dir)
    if verbose:
        print(f"[parse] L{line_num}: enter /{section}")
    return line_num


def _handle_directory(
    entry: str,
    leading_spaces: int,
    st: ParserState,
    line_num: int,
    verbose: bool,
) -> int:
    dir_name = expand_vars(entry[:-1].strip(), st.vars)
    new_dir = st.current_dir() / dir_name
    st.actions.append(Action("mkdir", new_dir))
    if st.indent_stack and (leading_spaces > st.indent_stack[-1]):
        st.dir_stack.append(new_dir)
    else:
        st.dir_stack[-1] = new_dir
    if verbose:
        print(f"[parse] L{line_num}: dir {new_dir}")
    return line_num


def _handle_heredoc_start(
    entry: str,
    lines: List[str],
    index: int,
    st: ParserState,
    line_num: int,
    verbose: bool,
) -> int:
    left, marker = entry.split("<<", 1)
    file_name = expand_vars(left.strip(), st.vars)
    marker = marker.strip() or "EOF"
    target_path = st.current_dir() / file_name
    if not validate_file_extension(file_name):
        raise ParseError(line_num, f"Potentially dangerous file extension: {file_name}", entry)
    st.heredoc_stack.append((marker, target_path, index + 1))
    if verbose:
        print(f"[parse] L{line_num}: heredoc start {file_name} <<{marker}")
    return index + 1


def _handle_heredoc_continuation(
    raw: str,
    lines: List[str],
    index: int,
    st: ParserState,
    line_num: int,
    verbose: bool,
) -> int:
    marker, target_path, start_line = st.heredoc_stack[-1]
    if raw.strip() == marker:
        content_lines = lines[start_line:index]
        content = "\n".join(content_lines)
        content = expand_vars(content, st.vars)
        content = normalize_line_endings(content)
        st.actions.append(Action("write", target_path, content))
        if not IS_WINDOWS and target_path.suffix in (".sh", ".py", ".pl", ".rb"):
            st.actions.append(Action("chmod", target_path, mode=0o755))
        if verbose:
            print(
                f"[parse] L{start_line}-{line_num - 1}: heredoc {target_path} ({len(content)} bytes)"
            )
        st.heredoc_stack.pop()
        return index + 1
    return index + 1


def _handle_inline_file(entry: str, st: ParserState, line_num: int, verbose: bool) -> int:
    left, right = entry.split("->", 1)
    file_name = expand_vars(left.strip(), st.vars)
    if not validate_file_extension(file_name):
        raise ParseError(line_num, f"Potentially dangerous file extension: {file_name}", entry)
    content = expand_vars(right.lstrip(), st.vars)
    content = normalize_line_endings(content)
    target_path = st.current_dir() / file_name
    st.actions.append(Action("write", target_path, content))
    if not IS_WINDOWS and target_path.suffix in (".sh", ".py", ".pl", ".rb"):
        st.actions.append(Action("chmod", target_path, mode=0o755))
    if verbose:
        print(f"[parse] L{line_num}: file {target_path} (inline, {len(content)} chars)")
    return line_num + 1


def _handle_plain_file(entry: str, st: ParserState, line_num: int, verbose: bool) -> int:
    file_name = expand_vars(entry, st.vars)
    if not validate_file_extension(file_name):
        raise ParseError(line_num, f"Potentially dangerous file extension: {file_name}", entry)
    target_path = st.current_dir() / file_name
    st.actions.append(Action("mkdir", target_path.parent))
    st.actions.append(Action("write", target_path, ""))
    if not IS_WINDOWS and target_path.suffix in (".sh", ".py", ".pl", ".rb"):
        st.actions.append(Action("chmod", target_path, mode=0o755))
    if verbose:
        print(f"[parse] L{line_num}: file {target_path} (empty)")
    return line_num + 1


def _handle_directive(
    line: str,
    st: ParserState,
    base_dir: Path,
    line_num: int,
    verbose: bool,
    index: int,
    lines: List[str],
) -> int:
    if line.startswith("@set "):
        body = line[len("@set ") :].strip()
        if "=" not in body:
            raise ParseError(line_num, "Invalid @set syntax, use: @set KEY=VALUE", line)
        key, value = body.split("=", 1)
        st.vars[key.strip()] = value.strip()
        if verbose:
            print(f"[tag] @set {key.strip()} = {value.strip()}")
        return index + 1

    if line.startswith("@include "):
        inc_file = expand_vars(line[len("@include ") :].strip(), st.vars)
        inc_path = (base_dir / inc_file).resolve()
        if not is_safe_under_base(inc_path, base_dir):
            raise ParseError(line_num, f"Included file path traversal detected: {inc_file}", line)
        if not inc_path.exists():
            raise ParseError(line_num, f"Included file not found: {inc_file}", line)
        verify_include_signature(inc_path, st, line_num, line, verbose)
        included_text = inc_path.read_text(encoding="utf-8")
        result = parse_schema(included_text, st.out_root, inc_path.parent, verbose=verbose)
        st.actions.extend(result.actions)
        st.vars.update(result.variables)
        st.gpg_reports.extend(result.gpg_reports)
        return index + 1

    if line.startswith("@ignore"):
        patterns = line.split()[1:]
        st.ignores.extend(patterns)
        if verbose:
            print(f"[tag] @ignore {patterns}")
        return index + 1

    if line.startswith("@chmod "):
        rest = line[len("@chmod ") :].strip()
        parts = rest.split()
        if len(parts) < 2:
            raise ParseError(line_num, "Invalid @chmod syntax, use: @chmod PATH MODE", line)
        path_str, mode_str = parts[0], parts[1]
        target_path = st.out_root / expand_vars(path_str, st.vars)
        mode = _parse_chmod_mode(mode_str)
        st.actions.append(Action("chmod", target_path, mode=mode))
        if verbose:
            print(f"[tag] @chmod {target_path} {oct(mode)}")
        return index + 1

    if line.startswith("@copy "):
        rest = line[len("@copy ") :].strip()
        parts = rest.split()
        if len(parts) < 2:
            raise ParseError(line_num, "Invalid @copy syntax, use: @copy SRC DEST", line)
        src_str, dest_str = parts[0], parts[1]
        src_path = (base_dir / expand_vars(src_str, st.vars)).resolve()
        dest_path = (st.out_root / expand_vars(dest_str, st.vars)).resolve()
        if not is_safe_under_base(src_path, base_dir):
            raise ParseError(line_num, f"Copy source path traversal detected: {src_str}", line)
        if not is_safe_under_base(dest_path, st.out_root):
            raise ParseError(line_num, f"Copy destination path traversal detected: {dest_str}", line)
        if not src_path.exists():
            raise ParseError(line_num, f"Copy source not found: {src_path}", line)
        st.actions.append(Action("copy", dest_path, src=src_path))
        if verbose:
            print(f"[tag] @copy {src_path} -> {dest_path}")
        return index + 1

    if line.startswith("@template "):
        template_name = line[len("@template ") :].strip()
        acts = template_actions(template_name, st, verbose)
        st.actions.extend(acts)
        return index + 1

    if line.startswith("@symlink "):
        rest = line[len("@symlink ") :].strip()
        parts = rest.split()
        if len(parts) < 2:
            raise ParseError(
                line_num,
                "Invalid @symlink syntax, use: @symlink TARGET LINKNAME",
                line,
            )
        target_str, link_str = parts[0], parts[1]
        target_path = Path(expand_vars(target_str, st.vars))
        link_path = st.out_root / expand_vars(link_str, st.vars)
        st.actions.append(Action("symlink", link_path, target=target_path))
        if verbose:
            print(f"[tag] @symlink {target_path} -> {link_path}")
        return index + 1

    raise ParseError(line_num, f"Unknown directive: {line.split()[0]}", line)


def _parse_chmod_mode(mode_str: str) -> int:
    if mode_str.startswith("+"):
        if "x" in mode_str:
            return 0o755
        if "w" in mode_str:
            return 0o644
        return 0o644
    try:
        if mode_str.startswith("0o"):
            return int(mode_str, 8)
        return int(mode_str, 8)
    except ValueError:
        return 0o644


def _filter_ignored_actions(actions: List[Action], ignores: List[str], verbose: bool) -> List[Action]:
    filtered: List[Action] = []
    for act in actions:
        rel_path = str(act.path)
        skip = False
        for pattern in ignores:
            if pattern in rel_path or fnmatch.fnmatch(rel_path, pattern):
                skip = True
                if verbose:
                    print(f"[filter] ignore {act.path} (pattern: {pattern})")
                break
        if not skip:
            filtered.append(act)
    return filtered


def coalesce_mkdirs(actions: List[Action]) -> List[Action]:
    seen_dirs = set()
    result: List[Action] = []
    for act in actions:
        if act.kind == "mkdir":
            if act.path not in seen_dirs:
                seen_dirs.add(act.path)
                result.append(act)
        else:
            result.append(act)
    return result


FILE: src/lrc/parser/__init__.py
Kind: text
Size: 834
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""Parser interfaces for LRC schemas."""

from __future__ import annotations

from typing import Dict, List, Tuple
from pathlib import Path

from ..core import ParseError, ParserState, parse_schema as _parse_schema

__all__ = ["ParseError", "ParserState", "parse_schema"]


def parse_schema(
    schema_text: str, out_root: Path, base_dir: Path, verbose: bool = False
) -> Tuple[List["Action"], Dict[str, str], Dict[str, str]]:
    """Typed wrapper that delegates to the legacy parser implementation.

    The parser package provides an extension point for the refactored
    architecture without breaking backward compatibility with the
    existing `lrc.core` module.  Consumers should import the parser
    through ``lrc.parser`` instead of ``lrc.core``.
    """

    return _parse_schema(schema_text, out_root, base_dir, verbose)


FILE: src/lrc/templates/__init__.py
Kind: text
Size: 53
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""Embedded starter templates used by the parser."""


FILE: src/lrc/templates/node-cli/README.md
Kind: text
Size: 61
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# ${PROJECT}

Run the CLI with:

```bash
node bin/cli.js
```


FILE: src/lrc/templates/node-cli/bin/cli.js
Kind: text
Size: 59
Last modified: 2026-01-21T07:58:23Z

CONTENT:
#!/usr/bin/env node
console.log('Welcome to ${PROJECT}!');


FILE: src/lrc/templates/node-cli/package.json
Kind: text
Size: 157
Last modified: 2026-01-21T07:58:23Z

CONTENT:
{
  "name": "${PKG}",
  "version": "${VERSION}",
  "description": "${DESCRIPTION}",
  "bin": {
    "${PROJECT}": "bin/cli.js"
  },
  "author": "${AUTHOR}"
}


FILE: src/lrc/templates/python-cli/README.md
Kind: text
Size: 88
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# ${PROJECT}

${DESCRIPTION}

## Getting Started

```bash
python -m ${PROJECT}.main
```


FILE: src/lrc/templates/python-cli/pyproject.toml
Kind: text
Size: 196
Last modified: 2026-01-21T07:58:23Z

CONTENT:
[project]
name = "${PKG}"
version = "${VERSION}"
description = "${DESCRIPTION}"
authors = [{ name = "${AUTHOR}" }]
requires-python = ">=3.9"

[project.scripts]
${PROJECT} = "${PROJECT}.main:main"


FILE: src/lrc/templates/python-cli/src/__init__.py
Kind: text
Size: 26
Last modified: 2026-01-21T07:58:23Z

CONTENT:
"""${PROJECT} package."""


FILE: src/lrc/templates/python-cli/src/main.py
Kind: text
Size: 212
Last modified: 2026-01-21T07:58:23Z

CONTENT:
#!/usr/bin/env python3
"""Entry point for ${PROJECT}."""


def main() -> None:
    print("Hello from ${PROJECT}!")
    print("Maintained by ${AUTHOR}")


if __name__ == "__main__":  # pragma: no cover
    main()


FILE: src/lrc/templates/rust-cli/Cargo.toml
Kind: text
Size: 106
Last modified: 2026-01-21T07:58:23Z

CONTENT:
[package]
name = "${PKG}"
version = "${VERSION}"
authors = ["${AUTHOR}"]
edition = "2021"

[dependencies]


FILE: src/lrc/templates/rust-cli/README.md
Kind: text
Size: 38
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# ${PROJECT}

Build with `cargo run`.


FILE: src/lrc/templates/rust-cli/src/main.rs
Kind: text
Size: 54
Last modified: 2026-01-21T07:58:23Z

CONTENT:
fn main() {
    println!("Welcome to ${PROJECT}!");
}


FILE: tests/data/simple.lrc
Kind: text
Size: 126
Last modified: 2026-01-21T07:58:23Z

CONTENT:
# Project: demo-app
# Description: Example project
# Version: 0.1.0

@set AUTHOR=Unit Tester

/src
  main.py -> print("demo")


FILE: tests/test_cli.py
Kind: text
Size: 600
Last modified: 2026-01-21T07:58:23Z

CONTENT:
import json
from pathlib import Path

from lrc.main import main


SCHEMA = Path("tests/data/simple.lrc")


def test_cli_dry_run(tmp_path):
    out_dir = tmp_path / "dry"
    code = main([str(SCHEMA), "--out", str(out_dir), "--dry-run"])
    assert code == 0
    assert not out_dir.exists()


def test_cli_generates_manifest(tmp_path):
    out_dir = tmp_path / "build"
    code = main([str(SCHEMA), "--out", str(out_dir)])
    assert code == 0
    manifest = out_dir / ".lrc-build.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text())
    assert data["project"] == "demo-app"


FILE: tests/test_cli_audit.py
Kind: text
Size: 604
Last modified: 2026-01-21T07:58:23Z

CONTENT:
from __future__ import annotations

from pathlib import Path

from lrc.cli import main as cli_main


def test_cli_runs_audit_skip(tmp_path: Path, capsys) -> None:
    schema = tmp_path / "schema.lrc"
    schema.write_text("""\n# Project: Audit Test\n@set AUTHOR=QA\nREADME.md\n""")
    output_dir = tmp_path / "output"

    exit_code = cli_main(
        [
            str(schema),
            "--output",
            str(output_dir),
            "--audit",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert output_dir.exists()
    assert "[AUDIT]" in captured.out


FILE: tests/test_dat_integration.py
Kind: text
Size: 798
Last modified: 2026-01-21T07:58:23Z

CONTENT:
from __future__ import annotations

import json
from pathlib import Path

from lrc.audit import run_dat_audit


def test_run_dat_audit_success(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "enabled": True,
                "command": ["python", "-c", "print('audit-ok')"],
            }
        )
    )

    result = run_dat_audit(tmp_path, config_path=config, logger=lambda *_: None)

    assert result["status"] == "passed"
    assert "audit-ok" in result.get("stdout", "")


def test_run_dat_audit_skipped_when_config_missing(tmp_path: Path) -> None:
    result = run_dat_audit(
        tmp_path, config_path=tmp_path / "missing.json", logger=lambda *_: None
    )
    assert result["status"] == "skipped"


FILE: tests/test_integration.py
Kind: text
Size: 653
Last modified: 2026-01-21T07:58:23Z

CONTENT:
import json
from pathlib import Path

from lrc.compiler import compile_schema_path
from lrc.generator import realize
from lrc.integration import run_dat_audit


def test_run_dat_audit_creates_summary(tmp_path):
    schema = Path("tests/data/simple.lrc")
    plan = compile_schema_path(schema, tmp_path / "out")
    out_dir = plan.root
    realize(plan, out_dir, dry_run=False, force=True)
    summary = run_dat_audit(plan, out_dir, audit_format="json")
    audit_file = out_dir / ".lrc-audit.json"
    assert audit_file.exists()
    data = json.loads(audit_file.read_text())
    assert data["mocked"] is True
    assert summary["project"] == "demo-app"


FILE: tests/test_parser.py
Kind: text
Size: 1129
Last modified: 2026-01-21T07:58:23Z

CONTENT:
from pathlib import Path

import pytest

from lrc.parser import ParseError, parse_schema


def test_parse_basic_schema(tmp_path: Path) -> None:
    schema = Path("tests/data/simple.lrc").read_text(encoding="utf-8")
    result = parse_schema(schema, tmp_path, Path("tests/data"))
    assert result.metadata["Project"] == "demo-app"
    assert result.variables["AUTHOR"] == "Unit Tester"
    paths = {action.path.relative_to(tmp_path) for action in result.actions if action.kind == "write"}
    assert Path("src/main.py") in paths


def test_template_expansion(tmp_path: Path) -> None:
    schema = """
# Project: template-demo
@template python-cli
"""
    result = parse_schema(schema, tmp_path, tmp_path)
    written = {action.path.relative_to(tmp_path) for action in result.actions if action.kind == "write"}
    assert Path("pyproject.toml") in written
    assert any("python" in action.content.lower() for action in result.actions if action.content)


def test_invalid_directive_raises(tmp_path: Path) -> None:
    schema = "@unknown value"
    with pytest.raises(ParseError):
        parse_schema(schema, tmp_path, tmp_path)


FILE: tests/test_parser_trust.py
Kind: text
Size: 1145
Last modified: 2026-01-21T07:58:23Z

CONTENT:
from __future__ import annotations

import json
from pathlib import Path

import pytest

from lrc.core import (
    DEFAULT_TRUSTED_TEMPLATES,
    ParseError,
    load_trusted_templates,
    parse_schema,
)


def test_load_trusted_templates_uses_default(tmp_path: Path) -> None:
    policy = load_trusted_templates(tmp_path)
    assert DEFAULT_TRUSTED_TEMPLATES.issubset(policy)


def test_parse_schema_rejects_untrusted_template(tmp_path: Path) -> None:
    schema = """\n@template forbidden\n"""
    out_root = tmp_path / "out"
    with pytest.raises(ParseError):
        parse_schema(schema, out_root, tmp_path)


def test_parse_schema_allows_trusted_template(tmp_path: Path) -> None:
    policy_file = tmp_path / "trusted_templates.json"
    policy_file.write_text(json.dumps(["custom-template"]))

    schema = """\n@template custom-template\n"""
    out_root = tmp_path / "out"
    actions, meta, vars_ = parse_schema(schema, out_root, tmp_path)
    # Template expands into at least one action (README fallback)
    assert actions
    assert meta == {"Project": None, "Description": None, "Version": None}
    assert vars_["AUTHOR"] == ""


FILE: trusted_templates.json
Kind: text
Size: 47
Last modified: 2026-01-21T07:58:23Z

CONTENT:
[
  "python-cli",
  "node-cli",
  "rust-cli"
]


## 4) Workflow Inventory (index only)
- .github/workflows/lrc-build.yml: push, pull_request
- .github/workflows/sign-and-release.yaml: push, workflow_dispatch
- .github/workflows/sign-and-release.yml: push, workflow_dispatch

## 5) Search Index (raw results)

subprocess:
docs/dat-integration.md
examples/forgekit_schema_full.lrc
examples/schema_entprse_example.lrc
examples/schema_org_example.lrc
src/lrc/audit.py
src/lrc/compiler.py
src/lrc/core.py
src/lrc/integration.py
src/lrc/parser.py

os.system:
none

exec(:
none

spawn:
none

shell:
README.md
docs/troubleshooting.md
install_deps.sh
src/lrc/bootstrap.py
src/lrc/core.py

child_process:
none

policy:
README.md
examples/schema_entprse_example.lrc
examples/schema_org_example.lrc
src/lrc/core.py
src/lrc/parser.py
tests/test_parser_trust.py

ethic:
none

enforce:
examples/schema_org_example.lrc
src/lrc/parser.py

guard:
none

receipt:
none

token:
.github/workflows/sign-and-release.yaml
docs/dat-integration.md
docs/troubleshooting.md
examples/schema_entprse_example.lrc
examples/schema_org_example.lrc

signature:
.github/workflows/sign-and-release.yaml
.github/workflows/sign-and-release.yml
README.md
docs/assets/lrc-logo-green.png
docs/troubleshooting.md
src/lrc/__init__.py
src/lrc/compiler.py
src/lrc/core.py
src/lrc/parser.py

verify:
.github/workflows/sign-and-release.yaml
.github/workflows/sign-and-release.yml
README.md
examples/forgekit_schema_full.lrc
examples/schema_entprse_example.lrc
install_deps.sh
src/lrc/compiler.py
src/lrc/core.py
src/lrc/parser.py

capability:
none

key_id:
none

contract:
examples/schema_entprse_example.lrc

schema:
.gitignore
README.md
docs/getting-started.md
docs/troubleshooting.md
examples/forgekit_schema_full.lrc
examples/schema_dev_example.lrc
examples/schema_entprse_example.lrc
examples/schema_example.lrc
examples/schema_org_example.lrc
install_deps.sh
lrc
pyproject.toml
src/lrc/__init__.py
src/lrc/cli/main.py
src/lrc/compiler.py
src/lrc/core.py
src/lrc/main.py
src/lrc/parser.py
src/lrc/parser/__init__.py
tests/test_cli_audit.py
tests/test_integration.py
tests/test_parser.py
tests/test_parser_trust.py

$schema:
none

json-schema:
none

router:
examples/schema_entprse_example.lrc

orchestr:
none

execute:
docs/dat-integration.md
examples/schema_entprse_example.lrc
src/lrc/__main__.py
src/lrc/integration.py

command:
README.md
docs/dat-integration.md
examples/forgekit_schema_full.lrc
examples/schema_dev_example.lrc
examples/schema_entprse_example.lrc
examples/schema_example.lrc
examples/schema_org_example.lrc
install_deps.sh
lrc
src/lrc/__main__.py
src/lrc/audit.py
src/lrc/integration.py
src/lrc/main.py
tests/test_dat_integration.py

## 6) Notes
none