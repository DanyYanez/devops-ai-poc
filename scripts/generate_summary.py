#!/usr/bin/env python3
import json
import os
import xml.etree.ElementTree as ET

def main():
    if not os.path.exists('test-results.json'):
        print("No test results found")
        return
    
    with open('test-results.json', 'r') as f:
        data = json.load(f)
    
    summary = data.get('summary', {})
    passed = summary.get('passed', 0)
    failed = summary.get('failed', 0)
    total = summary.get('total', 0)
    
    # Check coverage
    coverage = 0
    coverage_failed = False
    if os.path.exists('coverage.xml'):
        tree = ET.parse('coverage.xml')
        coverage = float(tree.getroot().get('line-rate', 0)) * 100
        if coverage < 70:
            coverage_failed = True
    
    # Determine overall status
    if failed > 0 or coverage_failed:
        status = "❌ FAILED"
    else:
        status = "✅ PASSED"
    
    print(f"## {status} • Pipeline Analysis Report\n")
    print("| Metric | Count |")
    print("|--------|-------|")
    print(f"| 📊 Total Tests | {total} |")
    print(f"| ✅ Passed | {passed} |")
    print(f"| ❌ Failed | {failed} |")
    print(f"| 📈 Coverage | {coverage:.1f}% |")
    print()
    
    if coverage_failed:
        print(f"### ⚠️ Coverage Below Threshold\n")
        print(f"• Current: **{coverage:.1f}%**")
        print(f"• Required: **70%**")
        print()
    
    if failed > 0:
        print("### ❌ Failed Tests\n")
        for test in data.get('tests', []):
            if test.get('outcome') == 'failed':
                nodeid = test.get('nodeid', 'Unknown')
                parts = nodeid.split('::')
                test_name = parts[-1] if len(parts) > 1 else nodeid
                file_path = parts[0] if len(parts) > 1 else ''
                
                print(f"• **{test_name}**")
                print(f"  • 📁 `{file_path}`")
                
                crash = test.get('call', {}).get('crash', {})
                if crash:
                    msg = crash.get('message', '')[:150]
                    if msg:
                        print(f"  • 💬 `{msg}`")
                print()
    
    print("---")
    print("📎 Download full HTML report from **Artifacts** section above")

if __name__ == "__main__":
    main()