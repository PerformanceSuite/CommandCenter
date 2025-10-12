# CommandCenter Analysis GitHub Action

Automatically analyze your repository with CommandCenter and post results to Pull Requests.

## Features

- 🔍 **Automated Analysis**: Trigger CommandCenter analysis on PR events
- 💬 **PR Comments**: Post analysis results directly in PR comments
- ✅ **Status Checks**: Optional workflow failure on critical issues
- 📊 **Customizable Depth**: Choose analysis depth (quick, standard, comprehensive)
- ⚡ **Real-time Progress**: Polls analysis job until completion

## Usage

### Basic Example

```yaml
name: CommandCenter Analysis

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run CommandCenter Analysis
        uses: ./.github/actions/commandcenter-analyze
        with:
          commandcenter-url: ${{ secrets.COMMANDCENTER_URL }}
          api-token: ${{ secrets.COMMANDCENTER_TOKEN }}
          project-id: ${{ secrets.COMMANDCENTER_PROJECT_ID }}
          repository-id: ${{ secrets.COMMANDCENTER_REPO_ID }}
```

### Advanced Example with Quality Gates

```yaml
name: CommandCenter Analysis with Quality Gates

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main, develop]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run CommandCenter Analysis
        id: analysis
        uses: ./.github/actions/commandcenter-analyze
        with:
          commandcenter-url: ${{ secrets.COMMANDCENTER_URL }}
          api-token: ${{ secrets.COMMANDCENTER_TOKEN }}
          project-id: ${{ secrets.COMMANDCENTER_PROJECT_ID }}
          repository-id: ${{ secrets.COMMANDCENTER_REPO_ID }}
          analysis-depth: comprehensive
          post-comment: 'true'
          fail-on-errors: 'true'

      - name: Upload Analysis Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: commandcenter-analysis
          path: analysis-results.json

      - name: Post to Slack
        if: failure()
        run: |
          curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
            -H 'Content-Type: application/json' \
            -d '{
              "text": "CommandCenter analysis failed for PR #${{ github.event.pull_request.number }}",
              "blocks": [{
                "type": "section",
                "text": {
                  "type": "mrkdwn",
                  "text": "*Analysis Results:* ${{ steps.analysis.outputs.summary }}"
                }
              }]
            }'
```

### Schedule Daily Analysis

```yaml
name: Daily Repository Analysis

on:
  schedule:
    - cron: '0 9 * * 1-5'  # Weekdays at 9 AM
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run CommandCenter Analysis
        uses: ./.github/actions/commandcenter-analyze
        with:
          commandcenter-url: ${{ secrets.COMMANDCENTER_URL }}
          api-token: ${{ secrets.COMMANDCENTER_TOKEN }}
          project-id: ${{ secrets.COMMANDCENTER_PROJECT_ID }}
          analysis-depth: comprehensive
          post-comment: 'false'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `commandcenter-url` | CommandCenter API URL (e.g., `https://commandcenter.example.com`) | Yes | - |
| `api-token` | CommandCenter API authentication token | Yes | - |
| `project-id` | CommandCenter project ID | Yes | - |
| `repository-id` | CommandCenter repository ID | No | Auto-detected |
| `post-comment` | Post results as PR comment | No | `true` |
| `fail-on-errors` | Fail workflow if critical issues found | No | `false` |
| `analysis-depth` | Analysis depth: `quick`, `standard`, `comprehensive` | No | `standard` |

## Outputs

| Output | Description |
|--------|-------------|
| `job-id` | CommandCenter job ID for this analysis |
| `status` | Analysis status (`completed`, `failed`, `timeout`) |
| `summary` | Analysis summary text |

## Required Secrets

Store these as GitHub repository secrets:

- `COMMANDCENTER_URL`: Your CommandCenter instance URL
- `COMMANDCENTER_TOKEN`: API token from CommandCenter
- `COMMANDCENTER_PROJECT_ID`: Your project ID
- `COMMANDCENTER_REPO_ID`: Repository ID (optional)

### Generating an API Token

1. Log into CommandCenter
2. Navigate to Settings → API Tokens
3. Click "Generate New Token"
4. Select scope: `jobs:create`, `jobs:read`
5. Copy token to GitHub Secrets

## Analysis Depth

- **quick**: Fast analysis, basic checks only (~30s)
- **standard**: Balanced analysis, most checks (~2-3 min)
- **comprehensive**: Deep analysis, all checks (~5-10 min)

## Quality Gates

Set `fail-on-errors: 'true'` to fail the workflow when critical issues are found. Customize thresholds by editing the action's final step.

## Permissions

The action requires:
- `contents: read` - To access repository code
- `pull-requests: write` - To post PR comments (if `post-comment: true`)

```yaml
permissions:
  contents: read
  pull-requests: write
```

## Examples

### PR Analysis with Status Checks

```yaml
- name: Analyze PR
  uses: ./.github/actions/commandcenter-analyze
  with:
    commandcenter-url: ${{ secrets.COMMANDCENTER_URL }}
    api-token: ${{ secrets.COMMANDCENTER_TOKEN }}
    project-id: ${{ secrets.COMMANDCENTER_PROJECT_ID }}
    fail-on-errors: 'true'
```

### Silent Analysis (No PR Comment)

```yaml
- name: Analyze Repository
  uses: ./.github/actions/commandcenter-analyze
  with:
    commandcenter-url: ${{ secrets.COMMANDCENTER_URL }}
    api-token: ${{ secrets.COMMANDCENTER_TOKEN }}
    project-id: ${{ secrets.COMMANDCENTER_PROJECT_ID }}
    post-comment: 'false'
```

## Troubleshooting

### Action Times Out

Increase the max wait time in `action.yml` or reduce `analysis-depth`:

```yaml
analysis-depth: quick
```

### PR Comments Not Posted

Ensure workflow has `pull-requests: write` permission:

```yaml
permissions:
  pull-requests: write
```

### Authentication Fails

Verify secrets are correctly set:

```bash
# Test API token
curl -H "Authorization: Bearer $COMMANDCENTER_TOKEN" \
  $COMMANDCENTER_URL/api/v1/health
```

## Support

- **Documentation**: https://github.com/your-org/commandcenter/docs
- **Issues**: https://github.com/your-org/commandcenter/issues
- **Discussions**: https://github.com/your-org/commandcenter/discussions

## License

MIT - See LICENSE file for details
