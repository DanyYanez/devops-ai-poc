#!/usr/bin/env python3
"""
LLM Analysis Script for CI/CD Pipeline
Analyzes test results and git changes using Claude Haiku (simulating local Qwen/LLaMA)

In production, replace the API call with Ollama or vLLM endpoint.
"""
import os
import sys
import json
import subprocess
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("Installing anthropic package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic", "-q"])
    import anthropic


def get_git_diff():
    """Get the git diff for the current commit."""
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "--stat"],
            capture_output=True,
            text=True
        )
        diff_stat = result.stdout if result.returncode == 0 else "No diff available"
        
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%s%n%b"],
            capture_output=True,
            text=True
        )
        commit_msg = result.stdout if result.returncode == 0 else "No commit message"
        
        return diff_stat, commit_msg
    except Exception as e:
        return f"Error getting diff: {e}", ""


def get_changed_files():
    """Get list of changed files."""
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "--name-only"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip().split('\n') if result.returncode == 0 else []
    except:
        return []


def read_test_results():
    """Read pytest results from JSON file."""
    results_file = "test-results.json"
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            return json.load(f)
    return None


def read_test_output():
    """Read raw test output."""
    output_file = "test-output.txt"
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            return f.read()
    return "No test output available"


def analyze_with_llm(test_results, test_output, diff_stat, commit_msg, changed_files):
    """Send data to LLM for analysis."""
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Build context
    if test_results:
        summary = test_results.get("summary", {})
        tests_passed = summary.get("passed", 0)
        tests_failed = summary.get("failed", 0)
        total_tests = summary.get("total", 0)
        duration = summary.get("duration", 0)
        
        failed_tests = []
        for test in test_results.get("tests", []):
            if test.get("outcome") == "failed":
                failed_tests.append({
                    "name": test.get("nodeid", "unknown"),
                    "message": test.get("call", {}).get("longrepr", "No details")
                })
    else:
        tests_passed = 0
        tests_failed = 0
        total_tests = 0
        duration = 0
        failed_tests = []
    
    prompt = f"""You are a DevOps assistant analyzing CI/CD pipeline results. 
Provide a concise, actionable analysis for the engineering team.

## Git Changes
Commit message: {commit_msg}

Files changed:
{diff_stat}

Changed files list: {', '.join(changed_files) if changed_files else 'None detected'}

## Test Results
- Total tests: {total_tests}
- Passed: {tests_passed}
- Failed: {tests_failed}
- Duration: {duration:.2f}s

## Failed Tests Details
{json.dumps(failed_tests, indent=2) if failed_tests else 'No failures'}

## Raw Test Output (last 2000 chars)
{test_output[-2000:] if test_output else 'No output'}

---

Please provide:
1. **Summary** (2-3 sentences): What changed and overall test status
2. **Risk Assessment** (Low/Medium/High): Based on what files changed and test results
3. **Failed Tests Analysis** (if any): Why they might have failed, correlation with changes
4. **Regression Check**: Are failures in new tests or existing (regression) tests?
5. **Recommendation**: Clear next action for the developer

Keep it concise and actionable. No fluff."""

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


def generate_html_report(analysis, test_results, commit_msg):
    """Generate HTML report for Jenkins/GitHub Actions."""
    
    if test_results:
        summary = test_results.get("summary", {})
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        total = summary.get("total", 0)
        status_color = "#22c55e" if failed == 0 else "#ef4444"
        status_text = "PASSED" if failed == 0 else "FAILED"
    else:
        passed = failed = total = 0
        status_color = "#f59e0b"
        status_text = "UNKNOWN"
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CI/CD Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 40px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            color: #f8fafc;
            border-bottom: 2px solid #334155;
            padding-bottom: 16px;
        }}
        .status-badge {{
            display: inline-block;
            background: {status_color};
            color: white;
            padding: 8px 20px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 14px;
        }}
        .metrics {{
            display: flex;
            gap: 20px;
            margin: 24px 0;
        }}
        .metric {{
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            flex: 1;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #38bdf8;
        }}
        .metric-label {{
            color: #94a3b8;
            font-size: 14px;
        }}
        .analysis {{
            background: #1e293b;
            padding: 24px;
            border-radius: 8px;
            margin-top: 24px;
        }}
        .analysis h2 {{
            color: #38bdf8;
            margin-top: 0;
        }}
        .analysis-content {{
            white-space: pre-wrap;
        }}
        .commit {{
            background: #334155;
            padding: 12px 16px;
            border-radius: 6px;
            margin: 16px 0;
            font-family: monospace;
            font-size: 14px;
        }}
        .footer {{
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #334155;
            color: #64748b;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 CI/CD Analysis Report</h1>
        
        <span class="status-badge">{status_text}</span>
        
        <div class="commit">📝 {commit_msg[:100] if commit_msg else 'No commit message'}</div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{total}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: #22c55e">{passed}</div>
                <div class="metric-label">Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: {'#ef4444' if failed > 0 else '#22c55e'}">{failed}</div>
                <div class="metric-label">Failed</div>
            </div>
        </div>
        
        <div class="analysis">
            <h2>🤖 AI Analysis</h2>
            <div class="analysis-content">{analysis}</div>
        </div>
        
        <div class="footer">
            Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | 
            Model: Claude Haiku (simulating local Qwen/LLaMA 7B)
        </div>
    </div>
</body>
</html>
"""
    
    with open("analysis-report.html", "w") as f:
        f.write(html)
    
    print(f"\n📄 HTML Report saved to: analysis-report.html")


def main():
    print("=" * 60)
    print("🔍 CI/CD LLM Analysis")
    print("=" * 60)
    
    # Gather data
    print("\n📊 Gathering pipeline data...")
    diff_stat, commit_msg = get_git_diff()
    changed_files = get_changed_files()
    test_results = read_test_results()
    test_output = read_test_output()
    
    print(f"  - Commit: {commit_msg[:50]}...")
    print(f"  - Changed files: {len(changed_files)}")
    print(f"  - Test results: {'Found' if test_results else 'Not found'}")
    
    # Analyze with LLM
    print("\n🤖 Analyzing with LLM...")
    analysis = analyze_with_llm(
        test_results, 
        test_output, 
        diff_stat, 
        commit_msg, 
        changed_files
    )
    
    # Output
    print("\n" + "=" * 60)
    print("📋 ANALYSIS RESULTS")
    print("=" * 60)
    print(analysis)
    print("=" * 60)
    
    # Generate HTML report
    generate_html_report(analysis, test_results, commit_msg)
    
    # Exit with appropriate code
    if test_results:
        failed = test_results.get("summary", {}).get("failed", 0)
        if failed > 0:
            print(f"\n❌ Pipeline has {failed} failed test(s)")
            sys.exit(1)
    
    print("\n✅ Analysis complete")


if __name__ == "__main__":
    main()
