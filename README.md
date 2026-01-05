# DevOps AI Analysis - Proof of Concept

This repository demonstrates how open-weight AI models can be integrated into CI/CD pipelines to provide automated analysis of test results, code changes, and deployment status.

## What This PoC Demonstrates

- **Automated Test Analysis**: LLM reviews test results and identifies patterns
- **Regression Detection**: Differentiates between new test failures and regressions
- **Change Impact Analysis**: Correlates code changes with test failures
- **Human-Readable Reports**: Generates actionable summaries for developers

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Git Push  │ ──▶ │   Run Tests │ ──▶ │ LLM Analysis│ ──▶ │   Report    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## PoC vs Production

| Component | This PoC | Production |
|-----------|----------|------------|
| CI/CD | GitHub Actions | Jenkins |
| LLM | Claude Haiku (API) | Ollama + Qwen/LLaMA (self-hosted) |
| Reports | GitHub Artifacts | Jenkins HTML Publisher |

The analysis script (`scripts/analyze.py`) works identically in both environments.

## Setup Instructions

### 1. Add API Key to GitHub Secrets

1. Go to your repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `ANTHROPIC_API_KEY`
4. Value: Your Anthropic API key

### 2. Enable GitHub Actions

Actions should be enabled by default. If not:
1. Go to repo → Settings → Actions → General
2. Select "Allow all actions"

### 3. Test the Pipeline

Make any change and push to trigger the pipeline:
```bash
git add .
git commit -m "test: initial commit"
git push
```

## Demo Scenarios

### Scenario 1: All Tests Pass
Push code without breaking anything. The LLM will report:
- ✅ Low risk assessment
- Summary of changes
- Confirmation of no regressions

### Scenario 2: Break a Test (Simulate Regression)
Edit `src/calculator.py` and introduce a bug:
```python
def add(a, b):
    return a + b + 1  # Bug!
```

The LLM will:
- ❌ Detect regression in existing tests
- Identify which commit likely caused it
- Recommend specific action

### Scenario 3: Add Failing New Test
Add a new test that fails. The LLM will:
- Differentiate it from regression
- Note it's a new test, not broken existing functionality

## Project Structure

```
.
├── src/
│   └── calculator.py         # Application code
├── tests/
│   ├── test_unit.py          # Unit tests (new features)
│   └── test_regression.py    # Regression tests (existing features)
├── scripts/
│   └── analyze.py            # LLM analysis script
└── .github/
    └── workflows/
        └── ci.yml            # GitHub Actions pipeline
```

## Adapting for Jenkins

Replace the GitHub Actions workflow with this Jenkinsfile:

```groovy
pipeline {
    agent any
    
    environment {
        ANTHROPIC_API_KEY = credentials('anthropic-api-key')
    }
    
    stages {
        stage('Test') {
            steps {
                sh 'pip install pytest pytest-json-report anthropic'
                sh 'pytest tests/ --json-report --json-report-file=test-results.json -v 2>&1 | tee test-output.txt || true'
            }
        }
        
        stage('AI Analysis') {
            steps {
                sh 'python scripts/analyze.py'
            }
        }
    }
    
    post {
        always {
            publishHTML([
                reportName: 'AI Analysis',
                reportDir: '.',
                reportFiles: 'analysis-report.html'
            ])
        }
    }
}
```

## Cost Estimate

Using Claude Haiku for this PoC:
- ~$0.25 per million input tokens
- ~$1.25 per million output tokens
- Typical analysis: ~2000 tokens = ~$0.001 per run

Production with self-hosted Ollama:
- Only compute costs (EC2/VM)
- ~$15-25/month for on-demand usage (20-30 min/day)

## License

MIT
