# GitHub Code Scanning Setup

This repository now includes GitHub's native code scanning capabilities using CodeQL.

## What's Included

### CodeQL Workflow (`.github/workflows/codeql.yml`)
- **Languages**: Python (primary), JavaScript
- **Triggers**: 
  - Push to `main` branch
  - Pull requests to `main` branch  
  - Weekly schedule (Sundays at 1:30 AM UTC)
- **Query Sets**: `security-extended` and `security-and-quality`

## Integration with Existing Security Tools

The CodeQL workflow complements the existing security scanning in `enhanced-ci-cd.yml`:

| Tool | Purpose | Scope |
|------|---------|-------|
| **CodeQL** | Static analysis for security vulnerabilities | Source code analysis |
| **Trivy** | Container/dependency vulnerability scanning | Dependencies, containers |
| **Safety** | Python dependency vulnerability checking | Python packages |
| **Bandit** | Python security linting | Python security issues |

## Security Tab Integration

CodeQL results will appear in the repository's **Security** tab under:
- **Code scanning alerts** - for ongoing security issues
- **Security advisories** - for dependency vulnerabilities

## Benefits

1. **Native GitHub Integration** - Results appear directly in PRs and Security tab
2. **Comprehensive Analysis** - Covers both Python and JavaScript code
3. **Automated Scanning** - Runs on every change and weekly
4. **Security-First Queries** - Focuses on security and quality issues
5. **SARIF Integration** - Works with other security tools

## Usage

The CodeQL workflow runs automatically. No manual intervention required.

To view results:
1. Go to repository **Security** tab
2. Click **Code scanning**
3. Review any alerts or findings

For more information, see the [GitHub Code Scanning documentation](https://docs.github.com/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning).