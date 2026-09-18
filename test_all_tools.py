"""
Comprehensive Tool Testing Script for MetaMarkAgency
Tests all tools across all agents and generates a detailed report.
"""
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
import traceback

# Tool files organized by agent
TOOL_STRUCTURE = {
    "AdCopyAgent": [
        "tools/AdCopyGenerator.py"
    ],
    "ImageCreatorAgent": [
        "tools/ImageGenerator.py",
        "tools/ImageSelector.py"
    ],
    "FacebookManagerAgent": [
        "tools/AdCampaignStarter.py",
        "tools/AdCreator.py",
        "tools/AdPerformanceMonitor.py",
        "tools/AdSetCreator.py",
        "tools/CampaignLifecycle.py",
        "tools/FacebookPagePostPublisher.py",
        "tools/FacebookPhotoPostPublisher.py",
        "tools/FacebookTokenDiagnostics.py"
    ],
    "ResearchAgent": [
        "tools/AdLibraryPatternAnalyzer.py",
        "tools/CompetitorResearchPlanBuilder.py",
        "tools/MetaAdLibraryKeywordSearch.py",
        "tools/MetaAdLibraryPageSearch.py",
        "tools/ScrapeCreatorsFacebookAdDetails.py",
        "tools/ScrapeCreatorsFacebookAdSearch.py",
        "tools/ScrapeCreatorsFacebookAdTranscript.py",
        "tools/ScrapeCreatorsFacebookCompanyAds.py",
        "tools/ScrapeCreatorsFacebookCompanySearch.py"
    ],
    "FacebookPolicyAgent": [
        "tools/FacebookPolicyChecklist.py"
    ],
    "ClientApprovalAgent": [
        "tools/ClientApprovalChecklist.py"
    ],
    "CampaignOpsAgent": [
        "tools/BudgetManager.py",
        "tools/CampaignDashboard.py",
        "tools/CampaignScheduler.py",
        "tools/PostTracker.py"
    ],
    "SearchVisibilityAgent": [
        "tools/ContentVisibilityChecklist.py",
        "tools/KnowledgeDocumentLookup.py",
        "tools/SearchVisibilityBriefBuilder.py"
    ]
}

class ToolTestResult:
    def __init__(self, agent_name, tool_name, tool_path):
        self.agent_name = agent_name
        self.tool_name = tool_name
        self.tool_path = tool_path
        self.status = "UNKNOWN"  # PASS, FAIL, NEEDS_CONFIG, SKIP
        self.output = ""
        self.error = ""
        self.execution_time = 0
        self.independence_score = 0
        self.dependencies = []
        self.notes = []

def test_tool(tool_path: Path) -> ToolTestResult:
    """Test a single tool by running it as a module."""
    agent_name = tool_path.parts[-3]
    tool_name = tool_path.stem
    
    result = ToolTestResult(agent_name, tool_name, str(tool_path))
    
    # Check if file exists
    if not tool_path.exists():
        result.status = "SKIP"
        result.error = "File not found"
        return result
    
    # Skip __init__ files
    if tool_name == "__init__":
        result.status = "SKIP"
        result.notes.append("Skipped __init__.py file")
        return result
    
    # Check if tool has test block
    content = tool_path.read_text()
    if 'if __name__ == "__main__"' not in content:
        result.status = "SKIP"
        result.notes.append("No test block found")
        return result
    
    # Analyze dependencies
    if "OPENAI_API_KEY" in content:
        result.dependencies.append("OPENAI_API_KEY")
    if "FACEBOOK_ACCESS_TOKEN" in content or "facebook_business" in content:
        result.dependencies.append("Facebook API")
    if "workflow_state" in content or "shared_state" in content:
        result.dependencies.append("Shared State")
    
    # Try to run the tool
    start_time = datetime.now()
    try:
        # Run the tool as a subprocess with workspace root in PYTHONPATH
        import os
        env = os.environ.copy()
        pythonpath = str(Path("/workspace"))
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{pythonpath}:{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = pythonpath
        
        process = subprocess.run(
            [sys.executable, str(tool_path)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=tool_path.parent.parent,  # Run from agent directory
            env=env  # Include workspace root in Python path
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        result.execution_time = execution_time
        result.output = process.stdout
        result.error = process.stderr
        
        # Determine status based on output
        if process.returncode == 0:
            if "error" in result.output.lower() and "error_type" not in result.output.lower():
                result.status = "FAIL"
                result.notes.append("Tool ran but returned error in output")
            else:
                result.status = "PASS"
                result.notes.append("Tool executed successfully")
        else:
            # Check for common error types
            if "Missing" in result.error or "not found" in result.error.lower():
                result.status = "NEEDS_CONFIG"
                result.notes.append("Missing environment variables or configuration")
            elif "ModuleNotFoundError" in result.error or "ImportError" in result.error:
                result.status = "NEEDS_CONFIG"
                result.notes.append("Missing Python dependencies")
            else:
                result.status = "FAIL"
                result.notes.append("Tool execution failed")
    
    except subprocess.TimeoutExpired:
        result.status = "FAIL"
        result.error = "Tool execution timeout (30s)"
        result.notes.append("Tool took too long to execute")
    except Exception as e:
        result.status = "FAIL"
        result.error = f"{type(e).__name__}: {str(e)}"
        result.notes.append("Unexpected error during testing")
    
    # Calculate independence score (1-10)
    independence_score = 10
    if "Shared State" in result.dependencies:
        independence_score -= 2
    if "OPENAI_API_KEY" in result.dependencies:
        independence_score -= 1
    if "Facebook API" in result.dependencies:
        independence_score -= 2
    if result.status == "FAIL":
        independence_score -= 3
    elif result.status == "NEEDS_CONFIG":
        independence_score -= 1
    
    result.independence_score = max(1, independence_score)
    
    return result

def generate_markdown_report(results: list[ToolTestResult], output_path: Path):
    """Generate a comprehensive markdown report."""
    
    # Calculate statistics
    total = len(results)
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    needs_config = sum(1 for r in results if r.status == "NEEDS_CONFIG")
    skipped = sum(1 for r in results if r.status == "SKIP")
    
    avg_independence = sum(r.independence_score for r in results) / total if total > 0 else 0
    
    # Group by agent
    by_agent = {}
    for r in results:
        if r.agent_name not in by_agent:
            by_agent[r.agent_name] = []
        by_agent[r.agent_name].append(r)
    
    # Generate report
    report = [
        "# MetaMarkAgency Tool Testing Report",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n## Executive Summary",
        f"\n- **Total Tools Tested:** {total}",
        f"- **Passed:** {passed} ({passed/total*100:.1f}%)" if total > 0 else "- **Passed:** 0",
        f"- **Failed:** {failed} ({failed/total*100:.1f}%)" if total > 0 else "- **Failed:** 0",
        f"- **Needs Configuration:** {needs_config} ({needs_config/total*100:.1f}%)" if total > 0 else "- **Needs Configuration:** 0",
        f"- **Skipped:** {skipped} ({skipped/total*100:.1f}%)" if total > 0 else "- **Skipped:** 0",
        f"- **Average Independence Score:** {avg_independence:.1f}/10",
        "\n## Tool Status Overview",
        "\n| Agent | Tool | Status | Independence | Dependencies |",
        "|-------|------|--------|--------------|--------------|"
    ]
    
    for agent_name in sorted(by_agent.keys()):
        for result in sorted(by_agent[agent_name], key=lambda r: r.tool_name):
            if result.status == "SKIP":
                continue
            status_emoji = {
                "PASS": "✅",
                "FAIL": "❌",
                "NEEDS_CONFIG": "⚠️",
                "SKIP": "⏭️"
            }[result.status]
            deps = ", ".join(result.dependencies) if result.dependencies else "None"
            report.append(
                f"| {agent_name} | {result.tool_name} | {status_emoji} {result.status} | "
                f"{result.independence_score}/10 | {deps} |"
            )
    
    # Detailed results by agent
    report.append("\n## Detailed Test Results by Agent")
    
    for agent_name in sorted(by_agent.keys()):
        report.append(f"\n### {agent_name}")
        
        agent_results = by_agent[agent_name]
        agent_passed = sum(1 for r in agent_results if r.status == "PASS")
        agent_total = len([r for r in agent_results if r.status != "SKIP"])
        
        report.append(f"\n**Status:** {agent_passed}/{agent_total} tools passing\n")
        
        for result in sorted(agent_results, key=lambda r: r.tool_name):
            if result.status == "SKIP":
                continue
                
            report.append(f"\n#### {result.tool_name}")
            report.append(f"\n- **Status:** {result.status}")
            report.append(f"- **Independence Score:** {result.independence_score}/10")
            report.append(f"- **Execution Time:** {result.execution_time:.2f}s")
            report.append(f"- **Dependencies:** {', '.join(result.dependencies) if result.dependencies else 'None'}")
            
            if result.notes:
                report.append(f"- **Notes:**")
                for note in result.notes:
                    report.append(f"  - {note}")
            
            if result.output:
                output_preview = result.output[:500]
                if len(result.output) > 500:
                    output_preview += "... (truncated)"
                report.append(f"\n**Output:**")
                report.append("```")
                report.append(output_preview)
                report.append("```")
            
            if result.error:
                error_preview = result.error[:500]
                if len(result.error) > 500:
                    error_preview += "... (truncated)"
                report.append(f"\n**Error:**")
                report.append("```")
                report.append(error_preview)
                report.append("```")
    
    # Dependencies Analysis
    report.append("\n## Dependencies Analysis")
    
    all_deps = {}
    for result in results:
        for dep in result.dependencies:
            if dep not in all_deps:
                all_deps[dep] = []
            all_deps[dep].append(f"{result.agent_name}/{result.tool_name}")
    
    report.append("\n| Dependency | Tool Count | Tools |")
    report.append("|------------|------------|-------|")
    for dep in sorted(all_deps.keys(), key=lambda d: len(all_deps[d]), reverse=True):
        tools = all_deps[dep]
        report.append(f"| {dep} | {len(tools)} | {', '.join(tools[:3])}{'...' if len(tools) > 3 else ''} |")
    
    # Recommendations
    report.append("\n## Recommendations")
    
    if needs_config > 0:
        report.append(f"\n### Configuration Required ({needs_config} tools)")
        report.append("\n1. **Environment Variables**: Ensure `.env` file contains:")
        report.append("   - `OPENAI_API_KEY` for OpenAI-dependent tools")
        report.append("   - `FACEBOOK_ACCESS_TOKEN`, `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`, `FACEBOOK_PAGE_ID` for Facebook API tools")
        report.append("\n2. **Missing Dependencies**: Run `pip install -r requirements.txt` if any import errors occurred")
    
    if failed > 0:
        report.append(f"\n### Failed Tools ({failed} tools)")
        report.append("\nTools that failed require investigation:")
        for result in results:
            if result.status == "FAIL":
                report.append(f"- **{result.agent_name}/{result.tool_name}**: {result.notes[0] if result.notes else 'Unknown error'}")
    
    report.append("\n### Tool Independence Improvements")
    low_independence = [r for r in results if r.independence_score < 7 and r.status != "SKIP"]
    if low_independence:
        report.append("\nTools with low independence scores (< 7/10):")
        for result in sorted(low_independence, key=lambda r: r.independence_score):
            report.append(f"- **{result.agent_name}/{result.tool_name}** ({result.independence_score}/10)")
            report.append(f"  - Dependencies: {', '.join(result.dependencies)}")
            report.append(f"  - Recommendation: Consider adding mock mode or better error handling for missing dependencies")
    
    # Write report
    output_path.write_text("\n".join(report))
    print(f"\n✅ Report generated: {output_path}")

def main():
    """Main test execution."""
    print("=" * 80)
    print("MetaMarkAgency Comprehensive Tool Testing")
    print("=" * 80)
    
    workspace = Path("/workspace")
    results = []
    
    total_tools = sum(len(tools) for tools in TOOL_STRUCTURE.values())
    current = 0
    
    for agent_name, tool_files in TOOL_STRUCTURE.items():
        print(f"\n📁 Testing {agent_name} ({len(tool_files)} tools)")
        
        for tool_file in tool_files:
            current += 1
            tool_path = workspace / agent_name / tool_file
            print(f"  [{current}/{total_tools}] Testing {tool_file}...", end=" ")
            
            result = test_tool(tool_path)
            results.append(result)
            
            status_symbols = {
                "PASS": "✅",
                "FAIL": "❌",
                "NEEDS_CONFIG": "⚠️",
                "SKIP": "⏭️"
            }
            print(f"{status_symbols.get(result.status, '?')} {result.status}")
    
    # Generate report
    print("\n" + "=" * 80)
    print("Generating comprehensive report...")
    report_path = workspace / "TOOL_TEST_RESULTS.md"
    generate_markdown_report(results, report_path)
    
    # Print summary
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    needs_config = sum(1 for r in results if r.status == "NEEDS_CONFIG")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Needs Config: {needs_config}")
    print("=" * 80)

if __name__ == "__main__":
    main()
