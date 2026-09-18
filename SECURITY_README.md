# Security Tools & Documentation

This directory contains security audit reports and tools for maintaining the security posture of the Agency Swarm project.

## 📋 Files

### Reports
- **`DEPENDENCY_SECURITY_AUDIT.md`** - Comprehensive dependency and supply chain security audit
  - Lists all vulnerabilities (CVEs) 
  - Supply chain risk assessment
  - Recommendations for remediation
  - Security score: 6.5/10

### Configuration
- **`requirements-secure.txt`** - Recommended secure dependency specification with:
  - Exact version pinning (no `>=` wildcards)
  - Extensive documentation and security notes
  - Optional security tools commented out

### Scripts
- **`security_scan.py`** - Automated security scanner
  - Vulnerability scanning (pip-audit)
  - Code security analysis (bandit)
  - Version pinning checks
  - Dangerous import pattern detection

---

## 🚀 Quick Start

### 1. Install Security Tools

```bash
# Install vulnerability scanner
pip install pip-audit

# Install security linter
pip install bandit

# Install dependency management
pip install pip-tools

# Install SBOM generator (optional)
pip install cyclonedx-bom
```

### 2. Run Security Scan

```bash
# Basic scan with text output
python security_scan.py

# JSON output for CI/CD
python security_scan.py --format json --output security-report.json

# Scan specific directory
python security_scan.py --workspace /path/to/project
```

### 3. Fix Critical Issues

```bash
# Update system packages with known CVEs
pip install --upgrade pip setuptools urllib3 wheel idna

# Upgrade to secure requirements
pip install -r requirements-secure.txt

# Verify no vulnerabilities
pip-audit
```

---

## 🔍 Security Checks

### Vulnerability Scanning

```bash
# Scan current environment
pip-audit

# Scan requirements file
pip-audit -r requirements.txt

# Generate detailed report
pip-audit --format json --output audit-report.json

# Check specific packages
pip-audit --package openai --package requests
```

### Code Security Analysis

```bash
# Scan entire project
bandit -r . -ll

# JSON output for automation
bandit -r . -f json -o bandit-report.json

# Exclude directories
bandit -r . --exclude .git,__pycache__,venv

# Only show high severity
bandit -r . -lll
```

### Dependency Analysis

```bash
# List outdated packages
pip list --outdated

# Show dependency tree
pip install pipdeptree
pipdeptree

# Generate frozen requirements
pip freeze > requirements-frozen.txt

# Compile with hashes
pip-compile requirements.in --generate-hashes -o requirements.txt
```

### License Compliance

```bash
# Install license checker
pip install pip-licenses

# List all licenses
pip-licenses

# Export to CSV
pip-licenses --format=csv --output-file=licenses.csv

# Check for GPL conflicts
pip-licenses | grep GPL
```

### SBOM Generation

```bash
# Generate CycloneDX SBOM
cyclonedx-py requirements -o sbom.json

# Generate SPDX SBOM
pip install spdx-tools
spdx-tool requirements -o sbom.spdx
```

---

## 🛠️ Remediation Guide

### Priority 1: System Package Vulnerabilities (37 CVEs)

**Issue:** System packages (pip, setuptools, urllib3, wheel, etc.) have known vulnerabilities.

**Solution:**
```bash
# Upgrade all system packages
pip install --upgrade pip setuptools wheel urllib3 idna

# Verify versions
pip list | grep -E "pip|setuptools|wheel|urllib3|idna"

# Expected versions:
# pip >= 26.2
# setuptools >= 83.0.0
# wheel >= 0.46.2
# urllib3 >= 2.7.0
# idna >= 3.15
```

**Verification:**
```bash
pip-audit  # Should report fewer vulnerabilities
```

### Priority 2: Version Pinning

**Issue:** Requirements use `>=` allowing automatic breaking changes.

**Solution:**
```bash
# Option A: Manual exact pinning
cp requirements-secure.txt requirements.txt
pip install -r requirements.txt

# Option B: Auto-generate from current environment
pip freeze | grep -E "agency-swarm|facebook-business|openai|python-dotenv|requests" > requirements.txt

# Option C: Use pip-tools for hash verification
echo "agency-swarm==1.11.0" > requirements.in
echo "facebook-business==26.0.1" >> requirements.in
echo "openai==2.44.0" >> requirements.in
echo "python-dotenv==1.2.3" >> requirements.in
echo "requests==2.33.1" >> requirements.in

pip-compile requirements.in --generate-hashes -o requirements.txt
```

**Verification:**
```bash
# Check no >= in requirements
grep ">=" requirements.txt  # Should return nothing
```

### Priority 3: Remove Unused Packages

**Issue:** ansible, ansible-core, httplib2 have vulnerabilities and may not be needed.

**Solution:**
```bash
# Check if packages are used
pip show ansible ansible-core httplib2

# If not needed, uninstall
pip uninstall -y ansible ansible-core httplib2

# Verify removal
pip-audit  # Should report fewer vulnerabilities
```

### Priority 4: OpenAI Version Upgrade (Blocked)

**Issue:** OpenAI 2.44.0 is outdated (latest: 3.13.0) but blocked by agency-swarm.

**Monitoring:**
```bash
# Check agency-swarm releases for openai 3.x support
pip install --upgrade agency-swarm

# Or check GitHub
# https://github.com/VRSEN/agency-swarm/releases
```

**Workaround:**
- Monitor agency-swarm releases monthly
- Test with openai 3.x in separate branch
- Consider forking agency-swarm if urgent

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Security Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pip-audit bandit
      
      - name: Run security scan
        run: |
          python security_scan.py --format json --output security-report.json
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: security-report.json
      
      - name: Fail on critical issues
        run: |
          if grep -q '"overall_status": "FAIL"' security-report.json; then
            echo "Security scan failed!"
            exit 1
          fi
```

### Pre-commit Hook

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: '1.8.0'
    hooks:
      - id: bandit
        args: ['-ll', '-r', '.']
  
  - repo: local
    hooks:
      - id: security-scan
        name: Security Scan
        entry: python security_scan.py
        language: system
        pass_filenames: false
        always_run: true
EOF

# Install hooks
pre-commit install
```

---

## 📊 Security Monitoring Schedule

### Daily
- Run automated security scan in CI/CD
- Review any new vulnerability alerts

### Weekly
- Run manual `pip-audit` scan
- Check for package updates
- Review security logs

### Monthly
- Full security audit
- Update dependencies (with testing)
- Review and update security policies
- Generate and archive SBOM

### Quarterly
- Comprehensive security review
- Penetration testing consideration
- Supply chain risk assessment
- Update security documentation

---

## 🎯 Security Score Goals

**Current Score:** 6.5/10

**Target Score:** 8.5/10

### Improvement Roadmap

#### Phase 1: Immediate (Score: 7.5/10)
- [x] ~~Create security audit~~ (DONE)
- [ ] Fix environment vulnerabilities
- [ ] Implement exact version pinning
- [ ] Remove unused packages

#### Phase 2: Short-term (Score: 8.0/10)
- [ ] Add pip-audit to CI/CD
- [ ] Implement hash verification
- [ ] Add bandit security scanning
- [ ] Generate and track SBOM

#### Phase 3: Medium-term (Score: 8.5/10)
- [ ] Set up automated alerts
- [ ] Implement pre-commit hooks
- [ ] Establish security policy
- [ ] Regular dependency reviews

#### Phase 4: Long-term (Score: 9.0/10)
- [ ] Full SCA integration (Snyk/Dependabot)
- [ ] Security dashboard
- [ ] Evaluate agency-swarm alternatives
- [ ] Compliance certifications

---

## 🆘 Troubleshooting

### pip-audit fails with "package not found"

```bash
# Use local environment scan instead of requirements file
pip-audit  # No -r flag
```

### bandit shows false positives

```bash
# Create .bandit config file
cat > .bandit << 'EOF'
[bandit]
exclude_dirs = ['.git', '__pycache__', 'venv', 'tests']
skips = B101,B601  # Skip specific test IDs
EOF

# Run with config
bandit -r . -c .bandit
```

### security_scan.py errors

```bash
# Ensure tools are installed
pip install pip-audit bandit

# Run with verbose output
python security_scan.py --format json --output debug.json
cat debug.json | jq  # Pretty print JSON
```

---

## 📚 Additional Resources

### Documentation
- [pip-audit Documentation](https://pypi.org/project/pip-audit/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

### Vulnerability Databases
- [National Vulnerability Database (NVD)](https://nvd.nist.gov/)
- [Snyk Vulnerability DB](https://security.snyk.io/)
- [GitHub Advisory Database](https://github.com/advisories)
- [PyPI Advisory Database](https://github.com/pypa/advisory-database)

### Tools
- [pip-audit](https://pypi.org/project/pip-audit/) - Vulnerability scanning
- [bandit](https://pypi.org/project/bandit/) - Security linting
- [safety](https://pypi.org/project/safety/) - Alternative vulnerability scanner
- [pip-tools](https://pypi.org/project/pip-tools/) - Dependency management
- [cyclonedx-bom](https://pypi.org/project/cyclonedx-bom/) - SBOM generation

---

## 📞 Support

For security issues or questions:

1. Review `DEPENDENCY_SECURITY_AUDIT.md` for detailed findings
2. Run `python security_scan.py` for current status
3. Check GitHub Security Advisories
4. Consult OWASP guidelines

**Security Disclosure:** For security vulnerabilities in this project, please follow responsible disclosure practices.

---

**Last Updated:** 2026-09-14  
**Next Audit Due:** 2026-10-14  
**Audit Frequency:** Monthly or upon major dependency update
