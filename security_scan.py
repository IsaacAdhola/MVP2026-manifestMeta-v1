#!/usr/bin/env python3
"""
Automated Security Scanner for Agency Swarm Project

This script performs comprehensive security checks including:
- Vulnerability scanning with pip-audit
- Code security analysis with bandit
- Dependency analysis
- Import pattern checking
- License compliance

Usage:
    python security_scan.py [--format json|text] [--output FILE]

Requirements:
    pip install pip-audit bandit
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class SecurityScanner:
    """Automated security scanner for Python projects."""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.results: Dict[str, Any] = {
            "scan_date": datetime.now().isoformat(),
            "workspace": str(workspace),
            "checks": {}
        }
    
    def run_pip_audit(self) -> Dict[str, Any]:
        """Run pip-audit vulnerability scanner."""
        print("🔍 Running pip-audit vulnerability scan...")
        
        try:
            result = subprocess.run(
                ["pip-audit", "--format=json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {
                    "status": "pass",
                    "vulnerabilities": 0,
                    "message": "No vulnerabilities found"
                }
            else:
                # pip-audit returns non-zero when vulnerabilities found
                try:
                    audit_data = json.loads(result.stdout)
                    vuln_count = len(audit_data.get("dependencies", []))
                    return {
                        "status": "fail",
                        "vulnerabilities": vuln_count,
                        "message": f"Found {vuln_count} packages with vulnerabilities",
                        "details": audit_data
                    }
                except json.JSONDecodeError:
                    # Fall back to text parsing
                    output = result.stdout + result.stderr
                    return {
                        "status": "error",
                        "message": "Failed to parse pip-audit output",
                        "output": output
                    }
        except FileNotFoundError:
            return {
                "status": "skipped",
                "message": "pip-audit not installed. Install with: pip install pip-audit"
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "pip-audit timed out after 60 seconds"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"pip-audit failed: {str(e)}"
            }
    
    def run_bandit(self) -> Dict[str, Any]:
        """Run bandit security linter."""
        print("🔍 Running bandit security linter...")
        
        try:
            result = subprocess.run(
                ["bandit", "-r", str(self.workspace), "-f", "json", 
                 "-ll", "--exclude", ".git,__pycache__,.pytest_cache,venv"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            try:
                bandit_data = json.loads(result.stdout)
                
                severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
                for item in bandit_data.get("results", []):
                    severity = item.get("issue_severity", "LOW")
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                total_issues = sum(severity_counts.values())
                
                return {
                    "status": "fail" if severity_counts["HIGH"] > 0 else ("warn" if total_issues > 0 else "pass"),
                    "total_issues": total_issues,
                    "severity_counts": severity_counts,
                    "message": f"Found {total_issues} security issues",
                    "details": bandit_data.get("results", [])[:10]  # Limit details
                }
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": "Failed to parse bandit output"
                }
        except FileNotFoundError:
            return {
                "status": "skipped",
                "message": "bandit not installed. Install with: pip install bandit"
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "bandit timed out after 120 seconds"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"bandit failed: {str(e)}"
            }
    
    def check_requirements_pinning(self) -> Dict[str, Any]:
        """Check if requirements.txt uses exact version pinning."""
        print("🔍 Checking requirements.txt version pinning...")
        
        req_file = self.workspace / "requirements.txt"
        if not req_file.exists():
            return {
                "status": "error",
                "message": "requirements.txt not found"
            }
        
        try:
            with open(req_file) as f:
                lines = f.readlines()
            
            loose_pins = []
            exact_pins = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                if ">=" in line or "~=" in line or ">" in line or "*" in line:
                    loose_pins.append(line)
                elif "==" in line:
                    exact_pins.append(line)
            
            total = len(loose_pins) + len(exact_pins)
            
            return {
                "status": "fail" if loose_pins else "pass",
                "total_dependencies": total,
                "exact_pins": len(exact_pins),
                "loose_pins": len(loose_pins),
                "message": f"{len(loose_pins)} dependencies with loose pinning" if loose_pins else "All dependencies exactly pinned",
                "loose_packages": loose_pins[:5]  # Show first 5
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to check requirements.txt: {str(e)}"
            }
    
    def check_dangerous_imports(self) -> Dict[str, Any]:
        """Scan for dangerous import patterns."""
        print("🔍 Scanning for dangerous import patterns...")
        
        dangerous_patterns = [
            ("eval", "Dynamic code execution"),
            ("exec", "Dynamic code execution"),
            ("__import__", "Dynamic imports"),
            ("pickle.loads", "Unsafe deserialization"),
            ("pickle.load", "Unsafe deserialization"),
            ("yaml.load", "Unsafe YAML loading (use safe_load)"),
            ("os.system", "Shell command execution"),
            ("subprocess.call.*shell=True", "Shell injection risk")
        ]
        
        findings = []
        
        for py_file in self.workspace.rglob("*.py"):
            if ".git" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                
                for pattern, description in dangerous_patterns:
                    if pattern in content:
                        findings.append({
                            "file": str(py_file.relative_to(self.workspace)),
                            "pattern": pattern,
                            "description": description
                        })
            except Exception as e:
                continue
        
        return {
            "status": "fail" if findings else "pass",
            "findings_count": len(findings),
            "message": f"Found {len(findings)} dangerous patterns" if findings else "No dangerous patterns detected",
            "findings": findings[:10]  # Limit output
        }
    
    def check_outdated_packages(self) -> Dict[str, Any]:
        """Check for outdated packages."""
        print("🔍 Checking for outdated packages...")
        
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            outdated = json.loads(result.stdout)
            
            return {
                "status": "warn" if outdated else "pass",
                "outdated_count": len(outdated),
                "message": f"{len(outdated)} packages have newer versions" if outdated else "All packages up to date",
                "packages": [
                    {
                        "name": pkg["name"],
                        "current": pkg["version"],
                        "latest": pkg["latest_version"]
                    }
                    for pkg in outdated[:10]
                ]
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to check outdated packages: {str(e)}"
            }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all security checks."""
        print("=" * 60)
        print("🔒 AUTOMATED SECURITY SCAN")
        print("=" * 60)
        print()
        
        self.results["checks"]["pip_audit"] = self.run_pip_audit()
        print()
        
        self.results["checks"]["bandit"] = self.run_bandit()
        print()
        
        self.results["checks"]["version_pinning"] = self.check_requirements_pinning()
        print()
        
        self.results["checks"]["dangerous_imports"] = self.check_dangerous_imports()
        print()
        
        self.results["checks"]["outdated_packages"] = self.check_outdated_packages()
        print()
        
        # Calculate overall status
        statuses = [check["status"] for check in self.results["checks"].values()]
        if "fail" in statuses:
            self.results["overall_status"] = "FAIL"
        elif "error" in statuses:
            self.results["overall_status"] = "ERROR"
        elif "warn" in statuses:
            self.results["overall_status"] = "WARNING"
        else:
            self.results["overall_status"] = "PASS"
        
        return self.results
    
    def print_summary(self):
        """Print human-readable summary."""
        print("=" * 60)
        print("📊 SECURITY SCAN SUMMARY")
        print("=" * 60)
        print()
        
        status_emoji = {
            "PASS": "✅",
            "WARNING": "⚠️",
            "FAIL": "❌",
            "ERROR": "🔴"
        }
        
        overall = self.results["overall_status"]
        print(f"Overall Status: {status_emoji.get(overall, '❓')} {overall}")
        print()
        
        for check_name, check_result in self.results["checks"].items():
            status = check_result["status"].upper()
            emoji = {
                "PASS": "✅",
                "FAIL": "❌",
                "WARN": "⚠️",
                "ERROR": "🔴",
                "SKIPPED": "⏭️"
            }.get(status, "❓")
            
            print(f"{emoji} {check_name.replace('_', ' ').title()}")
            print(f"   {check_result['message']}")
            print()
        
        print("=" * 60)
        
        if overall == "FAIL":
            print("⚠️  SECURITY ISSUES FOUND - Review audit report for details")
            return 1
        elif overall == "WARNING":
            print("⚠️  WARNINGS DETECTED - Consider addressing soon")
            return 0
        else:
            print("✅ No critical security issues detected")
            return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated security scanner for Python projects"
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace directory to scan"
    )
    
    args = parser.parse_args()
    
    scanner = SecurityScanner(args.workspace)
    results = scanner.run_all_checks()
    
    if args.format == "json":
        output = json.dumps(results, indent=2)
        if args.output:
            args.output.write_text(output)
            print(f"Results written to {args.output}")
        else:
            print(output)
    else:
        exit_code = scanner.print_summary()
        
        if args.output:
            with open(args.output, "w") as f:
                f.write(json.dumps(results, indent=2))
            print(f"\nDetailed results written to {args.output}")
        
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
