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


def get_git_info():
    """Get branch and author info."""
    try:
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
        
        author_result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%an"],
            capture_output=True,
            text=True
        )
        author = author_result.stdout.strip() if author_result.returncode == 0 else "unknown"
        
        return branch, author
    except:
        return "unknown", "unknown"


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

Please provide your analysis in the following JSON format (respond ONLY with valid JSON, no markdown):
{{
    "summary": "2-3 sentence summary of what changed and overall test status",
    "risk_level": "LOW|MEDIUM|HIGH",
    "risk_reasons": ["reason 1", "reason 2"],
    "failed_tests_analysis": "Analysis of why tests failed and correlation with changes (or 'No failures detected' if all passed)",
    "regression_check": "Whether failures are in new tests or existing regression tests",
    "recommendations": ["recommendation 1", "recommendation 2"],
    "quick_fixes": ["file: fix description", "file: fix description"]
}}

Keep it concise and actionable. No fluff."""

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


def parse_llm_response(response_text):
    """Parse JSON response from LLM."""
    try:
        # Try to extract JSON from response
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except:
        # Return default structure if parsing fails
        return {
            "summary": response_text[:500],
            "risk_level": "MEDIUM",
            "risk_reasons": ["Unable to parse detailed analysis"],
            "failed_tests_analysis": "See raw output",
            "regression_check": "Manual review required",
            "recommendations": ["Review test output manually"],
            "quick_fixes": []
        }


def generate_html_report(analysis_data, test_results, commit_msg, branch, author):
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
    
    # Risk level colors
    risk_level = analysis_data.get("risk_level", "MEDIUM")
    risk_colors = {
        "LOW": "#22c55e",
        "MEDIUM": "#f59e0b", 
        "HIGH": "#ef4444"
    }
    risk_color = risk_colors.get(risk_level, "#f59e0b")
    
    # Build failed tests HTML
    failed_tests_html = ""
    if test_results and failed > 0:
        failed_tests_html = "<ul class='failed-list'>"
        for test in test_results.get("tests", []):
            if test.get("outcome") == "failed":
                nodeid = test.get("nodeid", "Unknown")
                parts = nodeid.split("::")
                test_name = parts[-1] if len(parts) > 1 else nodeid
                file_path = parts[0] if len(parts) > 1 else ""
                error_msg = test.get("call", {}).get("crash", {}).get("message", "")[:150]
                
                failed_tests_html += f"""
                <li>
                    <strong>{test_name}</strong>
                    <div class="test-detail">📁 {file_path}</div>
                    <div class="test-detail">💬 {error_msg}</div>
                </li>
                """
        failed_tests_html += "</ul>"
    else:
        failed_tests_html = "<p class='success-text'>✓ All tests passed successfully</p>"
    
    # Build risk reasons HTML
    risk_reasons_html = "<ul class='bullet-list'>"
    for reason in analysis_data.get("risk_reasons", []):
        risk_reasons_html += f"<li>{reason}</li>"
    risk_reasons_html += "</ul>"
    
    # Build recommendations HTML
    recommendations_html = "<ul class='bullet-list'>"
    for rec in analysis_data.get("recommendations", []):
        recommendations_html += f"<li>{rec}</li>"
    recommendations_html += "</ul>"
    
    # Build quick fixes HTML
    quick_fixes = analysis_data.get("quick_fixes", [])
    quick_fixes_html = ""
    if quick_fixes:
        quick_fixes_html = "<ul class='bullet-list'>"
        for fix in quick_fixes:
            quick_fixes_html += f"<li><code>{fix}</code></li>"
        quick_fixes_html += "</ul>"
    else:
        quick_fixes_html = "<p class='muted'>No quick fixes suggested</p>"
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Pipeline Analysis Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
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
        .header {{
            margin-bottom: 32px;
        }}
        .header h1 {{
            color: #f8fafc;
            font-size: 1.75rem;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .header-meta {{
            color: #94a3b8;
            font-size: 0.9rem;
            margin-top: 8px;
        }}
        .status-badge {{
            display: inline-block;
            background: {status_color};
            color: white;
            padding: 6px 16px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.85rem;
            margin: 16px 0;
        }}
        .commit-box {{
            background: #334155;
            padding: 12px 16px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.9rem;
            margin-bottom: 24px;
            border-left: 4px solid {status_color};
        }}
        .metrics {{
            display: flex;
            gap: 16px;
            margin-bottom: 32px;
        }}
        .metric {{
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            flex: 1;
        }}
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
        }}
        .metric-value.green {{ color: #22c55e; }}
        .metric-value.red {{ color: #ef4444; }}
        .metric-value.blue {{ color: #38bdf8; }}
        .metric-label {{
            color: #94a3b8;
            font-size: 0.85rem;
            margin-top: 4px;
        }}
        .section {{
            background: #1e293b;
            padding: 24px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .section h2 {{
            color: #f8fafc;
            font-size: 1.1rem;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .section p {{
            color: #cbd5e1;
            font-size: 0.95rem;
        }}
        .risk-badge {{
            display: inline-block;
            background: {risk_color};
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.8rem;
            margin-left: 8px;
        }}
        .bullet-list {{
            list-style: none;
            padding: 0;
            margin: 12px 0 0 0;
        }}
        .bullet-list li {{
            position: relative;
            padding-left: 20px;
            margin-bottom: 10px;
            color: #cbd5e1;
            font-size: 0.95rem;
        }}
        .bullet-list li::before {{
            content: "•";
            position: absolute;
            left: 0;
            color: #38bdf8;
            font-weight: bold;
        }}
        .failed-list {{
            list-style: none;
            padding: 0;
            margin: 12px 0 0 0;
        }}
        .failed-list li {{
            background: #334155;
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 12px;
            border-left: 4px solid #ef4444;
        }}
        .failed-list li strong {{
            color: #f8fafc;
            font-size: 0.95rem;
        }}
        .test-detail {{
            color: #94a3b8;
            font-size: 0.85rem;
            margin-top: 6px;
            padding-left: 8px;
        }}
        .success-text {{
            color: #22c55e;
            font-size: 0.95rem;
        }}
        .muted {{
            color: #64748b;
            font-size: 0.9rem;
            font-style: italic;
        }}
        code {{
            background: #334155;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.85rem;
        }}
        .footer {{
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #334155;
            color: #64748b;
            font-size: 0.8rem;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Pipeline Analysis Report</h1>
            <div class="header-meta">Branch: <strong>{branch}</strong> • Author: <strong>{author}</strong></div>
        </div>
        
        <span class="status-badge">{status_text}</span>
        
        <div class="commit-box">📝 {commit_msg[:100] if commit_msg else 'No commit message'}</div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value blue">{total}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric">
                <div class="metric-value green">{passed}</div>
                <div class="metric-label">Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value {'red' if failed > 0 else 'green'}">{failed}</div>
                <div class="metric-label">Failed</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 Summary</h2>
            <p>{analysis_data.get('summary', 'No summary available')}</p>
        </div>
        
        <div class="section">
            <h2>⚠️ Risk Assessment <span class="risk-badge">{risk_level}</span></h2>
            {risk_reasons_html}
        </div>
        
        <div class="section">
            <h2>❌ Failed Tests</h2>
            {failed_tests_html}
        </div>
        
        <div class="section">
            <h2>🔄 Regression Analysis</h2>
            <p>{analysis_data.get('regression_check', 'No regression analysis available')}</p>
        </div>
        
        <div class="section">
            <h2>💡 Recommendations</h2>
            {recommendations_html}
        </div>
        
        <div class="section">
            <h2>🔧 Quick Fixes</h2>
            {quick_fixes_html}
        </div>
        
        <div class="footer">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} • 
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
    branch, author = get_git_info()
    
    print(f"  - Branch: {branch}")
    print(f"  - Author: {author}")
    print(f"  - Commit: {commit_msg[:50]}...")
    print(f"  - Changed files: {len(changed_files)}")
    print(f"  - Test results: {'Found' if test_results else 'Not found'}")
    
    # Analyze with LLM
    print("\n🤖 Analyzing with LLM...")
    raw_analysis = analyze_with_llm(
        test_results, 
        test_output, 
        diff_stat, 
        commit_msg, 
        changed_files
    )
    
    # Parse response
    analysis_data = parse_llm_response(raw_analysis)
    
    # Output
    print("\n" + "=" * 60)
    print("📋 ANALYSIS RESULTS")
    print("=" * 60)
    print(f"\nSummary: {analysis_data.get('summary', 'N/A')}")
    print(f"\nRisk Level: {analysis_data.get('risk_level', 'N/A')}")
    print(f"\nRegression: {analysis_data.get('regression_check', 'N/A')}")
    print("=" * 60)
    
    # Generate HTML report
    generate_html_report(analysis_data, test_results, commit_msg, branch, author)
    
    # Exit with appropriate code
    if test_results:
        failed = test_results.get("summary", {}).get("failed", 0)
        if failed > 0:
            print(f"\n❌ Pipeline has {failed} failed test(s)")
            sys.exit(1)
    
    print("\n✅ Analysis complete")


if __name__ == "__main__":
    main()
