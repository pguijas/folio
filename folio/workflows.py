from __future__ import annotations

from pathlib import Path


FOLIO_PAGES_WORKFLOW = """name: Deploy Docs

"on":
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pages: write
      pull-requests: read
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Configure GitHub Pages
        id: pages
        uses: actions/configure-pages@v5

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Install pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Build docs
        env:
          FOLIO_BASE_PATH: "${{ steps.pages.outputs.base_path || '/' }}"
        run: uv tool run --from folio-docs folio build --clean

      - name: Preserve branch previews
        shell: bash
        run: uv tool run --from folio-docs folio github-pages preserve-previews --site-dir _site --git-repo . --state-dir _pages-state --state-branch folio-pages-state

      - name: Prune stale previews
        shell: bash
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          open_prs="$(gh pr list --state open --json number,headRefName)"
          uv tool run --from folio-docs folio github-pages prune-previews \\
            --previews-dir _site/previews \\
            --open-prs-json "$open_prs"

      - name: Write previews data
        shell: bash
        run: uv tool run --from folio-docs folio github-pages write-previews-data --previews-dir _site/previews

      - name: Save Pages state
        shell: bash
        run: uv tool run --from folio-docs folio github-pages save-state --artifact-dir _site --git-repo . --state-dir _pages-state --state-branch folio-pages-state --commit-message "Update Pages state"

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: _site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    permissions:
      pages: write
      id-token: write
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4

      - name: Verify and print deployment URL
        shell: bash
        run: |
          url="${{ steps.deployment.outputs.page_url }}"
          index_url="${url%/}/previews/"
          uv tool run --from folio-docs folio github-pages verify-url \\
            --url "$url" \\
            --index-url "$index_url" \\
            --summary-heading "Production docs" \\
            --primary-label "Production URL" \\
            --index-label "Previews index" \\
            --success-message "Verified deployment and previews index with HTTP 200." \\
            --error-message "Deployment URL or previews index did not return HTTP 200"
"""


FOLIO_BRANCH_PREVIEW_WORKFLOW = """name: Deploy Branch Preview Docs

"on":
  pull_request_target:
    types: ["opened", "synchronize", "reopened", "ready_for_review"]

permissions:
  contents: read
  pull-requests: read

jobs:
  validate:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
    outputs:
      enabled: ${{ steps.preview-gate.outputs.enabled }}
      pr_number: ${{ steps.preview-gate.outputs.pr_number }}
      head_sha: ${{ steps.preview-gate.outputs.head_sha }}
      head_ref: ${{ steps.preview-gate.outputs.head_ref }}
      pr_title: ${{ steps.preview-gate.outputs.pr_title }}
    steps:
      - name: Validate preview PR
        id: preview-gate
        env:
          GH_TOKEN: ${{ github.token }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          EVENT_HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        shell: bash
        run: |
          skip() {
            echo "enabled=false" >> "$GITHUB_OUTPUT"
            echo "::notice::$1"
            echo "### Branch preview" >> "$GITHUB_STEP_SUMMARY"
            echo "" >> "$GITHUB_STEP_SUMMARY"
            echo "$1" >> "$GITHUB_STEP_SUMMARY"
            exit 0
          }

          if [ -z "$PR_NUMBER" ]; then
            skip "Preview deploy skipped because the workflow could not resolve an open pull request."
          fi

          pr_json="$(gh api --method GET "repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}")"
          PR_STATE="$(jq -r '.state' <<< "$pr_json")"
          IS_DRAFT="$(jq -r '.draft' <<< "$pr_json")"
          HEAD_SHA="$(jq -r '.head.sha' <<< "$pr_json")"
          HEAD_REF="$(jq -r '.head.ref' <<< "$pr_json")"
          HEAD_REPO="$(jq -r '.head.repo.full_name' <<< "$pr_json")"
          PR_TITLE="$(jq -r '.title' <<< "$pr_json")"

          if [ "$PR_STATE" != "open" ]; then
            skip "Preview deploy skipped because PR #${PR_NUMBER} is not open."
          fi
          if [ "${IS_DRAFT:-false}" = "true" ]; then
            skip "Preview deploy skipped because PR #${PR_NUMBER} is still a draft."
          fi
          if [ "$HEAD_REPO" != "$GITHUB_REPOSITORY" ]; then
            skip "Preview deploy skipped because PR #${PR_NUMBER} comes from a fork."
          fi
          if [ -n "$EVENT_HEAD_SHA" ] && [ "$HEAD_SHA" != "$EVENT_HEAD_SHA" ]; then
            skip "Preview deploy skipped because PR #${PR_NUMBER} head has not caught up to ${EVENT_HEAD_SHA}."
          fi

          echo "enabled=true" >> "$GITHUB_OUTPUT"
          echo "pr_number=${PR_NUMBER}" >> "$GITHUB_OUTPUT"
          echo "head_sha=${HEAD_SHA}" >> "$GITHUB_OUTPUT"
          echo "head_ref=${HEAD_REF}" >> "$GITHUB_OUTPUT"
          {
            echo "pr_title<<__FOLIO_EOF__"
            echo "$PR_TITLE"
            echo "__FOLIO_EOF__"
          } >> "$GITHUB_OUTPUT"

  build-preview:
    needs: validate
    if: needs.validate.outputs.enabled == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Check out preview branch
        uses: actions/checkout@v4
        with:
          ref: ${{ needs.validate.outputs.head_sha }}
          path: preview-source
          fetch-depth: 0
          persist-credentials: false

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Install pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Compute preview path
        id: preview
        env:
          HEAD_REF: ${{ needs.validate.outputs.head_ref }}
          PR_NUMBER: ${{ needs.validate.outputs.pr_number }}
          GITHUB_OWNER: ${{ github.repository_owner }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        shell: bash
        run: |
          repo_name="${GITHUB_REPOSITORY#*/}"
          if [ "$repo_name" = "${GITHUB_OWNER}.github.io" ]; then
            pages_base_path="/"
            pages_base_url="https://${GITHUB_OWNER}.github.io"
          else
            pages_base_path="/${repo_name}"
            pages_base_url="https://${GITHUB_OWNER}.github.io/${repo_name}"
          fi

          uv tool run --from folio-docs folio github-pages compute-preview-path \\
            --head-ref "$HEAD_REF" \\
            --pr-number "$PR_NUMBER" \\
            --pages-base-path "$pages_base_path" \\
            --pages-base-url "$pages_base_url"

      - name: Build preview docs
        working-directory: preview-source
        env:
          FOLIO_BASE_PATH: ${{ steps.preview.outputs.base_path }}
        run: uv tool run --from folio-docs folio build --clean

      - name: Upload preview artifact
        uses: actions/upload-artifact@v4
        with:
          name: branch-preview-site
          path: preview-source/_site
          if-no-files-found: error

  deploy:
    needs: ["validate", "build-preview"]
    if: needs.validate.outputs.enabled == 'true'
    runs-on: ubuntu-latest
    concurrency:
      group: "pages"
      cancel-in-progress: false
    permissions:
      contents: write
      issues: write
      pages: write
      id-token: write
      pull-requests: write
    steps:
      - name: Revalidate preview PR
        id: deploy-gate
        env:
          GH_TOKEN: ${{ github.token }}
          PR_NUMBER: ${{ needs.validate.outputs.pr_number }}
          HEAD_SHA: ${{ needs.validate.outputs.head_sha }}
        shell: bash
        run: |
          skip() {
            echo "enabled=false" >> "$GITHUB_OUTPUT"
            echo "::notice::$1"
            echo "### Branch preview" >> "$GITHUB_STEP_SUMMARY"
            echo "" >> "$GITHUB_STEP_SUMMARY"
            echo "$1" >> "$GITHUB_STEP_SUMMARY"
            exit 0
          }

          pr_json="$(gh api --method GET "repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}")"
          PR_STATE="$(jq -r '.state' <<< "$pr_json")"
          IS_DRAFT="$(jq -r '.draft' <<< "$pr_json")"
          CURRENT_HEAD_SHA="$(jq -r '.head.sha' <<< "$pr_json")"
          HEAD_REPO="$(jq -r '.head.repo.full_name' <<< "$pr_json")"

          if [ "$PR_STATE" != "open" ]; then
            skip "Preview deploy skipped because PR #${PR_NUMBER} is not open."
          fi
          if [ "${IS_DRAFT:-false}" = "true" ]; then
            skip "Preview deploy skipped because PR #${PR_NUMBER} is still a draft."
          fi
          if [ "$HEAD_REPO" != "$GITHUB_REPOSITORY" ]; then
            skip "Preview deploy skipped because PR #${PR_NUMBER} comes from a fork."
          fi
          if [ "$CURRENT_HEAD_SHA" != "$HEAD_SHA" ]; then
            skip "Preview deploy skipped because PR #${PR_NUMBER} head has not caught up to ${HEAD_SHA}."
          fi

          echo "enabled=true" >> "$GITHUB_OUTPUT"

      - name: Check out production branch
        if: steps.deploy-gate.outputs.enabled == 'true'
        uses: actions/checkout@v4
        with:
          ref: main
          path: trusted-source
          fetch-depth: 0

      - name: Configure GitHub Pages
        if: steps.deploy-gate.outputs.enabled == 'true'
        id: pages
        uses: actions/configure-pages@v5

      - name: Set up Python
        if: steps.deploy-gate.outputs.enabled == 'true'
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        if: steps.deploy-gate.outputs.enabled == 'true'
        uses: astral-sh/setup-uv@v5

      - name: Install pnpm
        if: steps.deploy-gate.outputs.enabled == 'true'
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Set up Node
        if: steps.deploy-gate.outputs.enabled == 'true'
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Build production docs
        if: steps.deploy-gate.outputs.enabled == 'true'
        working-directory: trusted-source
        env:
          FOLIO_BASE_PATH: "${{ steps.pages.outputs.base_path || '/' }}"
        run: uv tool run --from folio-docs folio build --clean

      - name: Compute preview path
        if: steps.deploy-gate.outputs.enabled == 'true'
        id: preview
        working-directory: trusted-source
        env:
          HEAD_REF: ${{ needs.validate.outputs.head_ref }}
          PR_NUMBER: ${{ needs.validate.outputs.pr_number }}
          PAGES_BASE_PATH: ${{ steps.pages.outputs.base_path }}
          PAGES_BASE_URL: ${{ steps.pages.outputs.base_url }}
        shell: bash
        run: |
          uv tool run --from folio-docs folio github-pages compute-preview-path \\
            --head-ref "$HEAD_REF" \\
            --pr-number "$PR_NUMBER" \\
            --pages-base-path "$PAGES_BASE_PATH" \\
            --pages-base-url "$PAGES_BASE_URL"

      - name: Download preview artifact
        if: steps.deploy-gate.outputs.enabled == 'true'
        uses: actions/download-artifact@v4
        with:
          name: branch-preview-site
          path: _preview-site

      - name: Prepare Pages artifact
        if: steps.deploy-gate.outputs.enabled == 'true'
        working-directory: trusted-source
        shell: bash
        run: |
          uv tool run --from folio-docs folio github-pages prepare-artifact \\
            --production-site _site \\
            --artifact-dir ../_pages-artifact \\
            --git-repo . \\
            --state-dir ../_pages-state \\
            --state-branch folio-pages-state

      - name: Copy branch preview
        if: steps.deploy-gate.outputs.enabled == 'true'
        working-directory: trusted-source
        shell: bash
        run: |
          uv tool run --from folio-docs folio github-pages copy-branch-preview \\
            --preview-site ../_preview-site \\
            --artifact-dir ../_pages-artifact \\
            --preview-id "${{ steps.preview.outputs.safe_branch }}"

      - name: Write preview metadata
        if: steps.deploy-gate.outputs.enabled == 'true'
        working-directory: trusted-source
        shell: bash
        env:
          PR_NUMBER: ${{ needs.validate.outputs.pr_number }}
          PR_TITLE: ${{ needs.validate.outputs.pr_title }}
          BRANCH: ${{ needs.validate.outputs.head_ref }}
          HEAD_SHA: ${{ needs.validate.outputs.head_sha }}
          PR_URL: ${{ github.event.pull_request.html_url }}
          REPO: ${{ github.repository }}
          AUTHOR: ${{ github.event.pull_request.user.login }}
          AUTHOR_URL: ${{ github.event.pull_request.user.html_url }}
          AVATAR_URL: ${{ github.event.pull_request.user.avatar_url }}
        run: |
          uv tool run --from folio-docs folio github-pages write-preview-metadata \\
            --artifact-dir ../_pages-artifact \\
            --preview-id "${{ steps.preview.outputs.safe_branch }}" \\
            --pr-number "$PR_NUMBER" \\
            --title "$PR_TITLE" \\
            --branch "$BRANCH" \\
            --commit "$HEAD_SHA" \\
            --pr-url "$PR_URL" \\
            --repo "$REPO" \\
            --author "$AUTHOR" \\
            --author-url "$AUTHOR_URL" \\
            --avatar-url "$AVATAR_URL" \\
            --updated-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

      - name: Prune stale previews
        if: steps.deploy-gate.outputs.enabled == 'true'
        working-directory: trusted-source
        shell: bash
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          open_prs="$(gh pr list --state open --json number,headRefName)"
          uv tool run --from folio-docs folio github-pages prune-previews \\
            --previews-dir ../_pages-artifact/previews \\
            --open-prs-json "$open_prs"

      - name: Write previews data
        if: steps.deploy-gate.outputs.enabled == 'true'
        working-directory: trusted-source
        shell: bash
        run: uv tool run --from folio-docs folio github-pages write-previews-data --previews-dir ../_pages-artifact/previews

      - name: Save Pages state
        if: steps.deploy-gate.outputs.enabled == 'true'
        working-directory: trusted-source
        shell: bash
        run: |
          uv tool run --from folio-docs folio github-pages save-state \\
            --artifact-dir ../_pages-artifact \\
            --git-repo . \\
            --state-dir ../_pages-state \\
            --state-branch folio-pages-state \\
            --commit-message "Update preview for PR #${{ needs.validate.outputs.pr_number }}"

      - name: Upload Pages artifact
        if: steps.deploy-gate.outputs.enabled == 'true'
        uses: actions/upload-pages-artifact@v3
        with:
          path: _pages-artifact

      - name: Deploy to GitHub Pages
        if: steps.deploy-gate.outputs.enabled == 'true'
        id: deployment
        uses: actions/deploy-pages@v4
        env:
          # pull_request_target runs with GITHUB_SHA pinned to the BASE
          # branch tip, which does not change between preview pushes.
          # deploy-pages derives pages_build_version from GITHUB_SHA, and
          # Pages treats deployments with an unchanged build version as
          # already-live: the CDN never purges and previews go stale.
          # Deploy under the validated PR head sha so every preview push
          # produces a distinct build version.
          GITHUB_SHA: ${{ needs.validate.outputs.head_sha }}

      - name: Verify and print preview URL
        if: steps.deploy-gate.outputs.enabled == 'true'
        working-directory: trusted-source
        env:
          PREVIEW_URL: ${{ steps.preview.outputs.url }}
          INDEX_URL: ${{ steps.pages.outputs.base_url }}/previews/
        shell: bash
        run: |
          uv tool run --from folio-docs folio github-pages verify-url \\
            --url "$PREVIEW_URL" \\
            --index-url "$INDEX_URL" \\
            --summary-heading "Branch preview" \\
            --primary-label "Preview URL" \\
            --index-label "Previews index" \\
            --success-message "Verified preview and index with HTTP 200." \\
            --error-message "Preview URL or index did not return HTTP 200"

      - name: Comment preview URL
        if: steps.deploy-gate.outputs.enabled == 'true'
        working-directory: trusted-source
        env:
          GH_TOKEN: ${{ github.token }}
          BRANCH: ${{ needs.validate.outputs.head_ref }}
          HEAD_SHA: ${{ needs.validate.outputs.head_sha }}
          INDEX_URL: ${{ steps.pages.outputs.base_url }}/previews/
          PREVIEW_URL: ${{ steps.preview.outputs.url }}
          PR_NUMBER: ${{ needs.validate.outputs.pr_number }}
        shell: bash
        run: |
          uv tool run --from folio-docs folio github-pages comment-preview \\
            --repo "${{ github.repository }}" \\
            --pr-number "$PR_NUMBER" \\
            --preview-url "$PREVIEW_URL" \\
            --index-url "$INDEX_URL" \\
            --branch "$BRANCH" \\
            --head-sha "$HEAD_SHA"
"""


def github_pages_workflows() -> dict[Path, str]:
    return {
        Path(".github/workflows/pages.yml"): FOLIO_PAGES_WORKFLOW,
        Path(".github/workflows/branch-previews.yml"): FOLIO_BRANCH_PREVIEW_WORKFLOW,
    }
