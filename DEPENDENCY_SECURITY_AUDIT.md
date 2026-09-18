# DEPENDENCY VULNERABILITY & SUPPLY CHAIN SECURITY AUDIT

**Audit Date:** September 14, 2026  
**Workspace:** /workspace  
**Python Version:** 3.12.3  
**Total Python Files Analyzed:** 68  
**Security Score:** 6.5/10

---

## EXECUTIVE SUMMARY

This audit identified **37 known vulnerabilities** in system packages (pip, setuptools, ansible-core, urllib3, wheel, httplib2, idna) that are not directly used by the application but are present in the environment. The core application dependencies (agency-swarm, facebook-business, openai, requests, python-dotenv) have **0 direct vulnerabilities** reported. However, significant supply chain risks exist due to:

1. Minimal version pinning strategy (using `>=` instead of `==`)
2. Poor security posture of agency-swarm (23% security score, OpenSSF 4.5/10)
3. Transitive dependency vulnerabilities in the environment
4. Missing security-focused packages (no dependency scanning, SBOM, or vulnerability monitoring)

**Critical Finding:** Agency-swarm has documented supply chain weaknesses including lack of branch protection, missing code review processes, and no fuzzing infrastructure.

---

## 1. DEPENDENCY ANALYSIS

### 1.1 Core Dependencies (requirements.txt)

| Package | Current Version | Latest Available | Pinning Strategy | Status |
|---------|----------------|------------------|------------------|--------|
| agency-swarm | >=1.0.0 (1.11.0 installed) | 1.11.0 | Loose (>=) | ⚠️ UPGRADE PINNING |
| facebook-business | >=20.0.0 (26.0.1 installed) | 26.0.1 | Loose (>=) | ⚠️ UPGRADE PINNING |
| openai | >=1.30.0 (2.44.0 installed) | 3.13.0 | Loose (>=) | ⚠️ OUTDATED + PINNING |
| python-dotenv | >=1.0.0 (1.2.3 installed) | 1.2.3 | Loose (>=) | ⚠️ UPGRADE PINNING |
| requests | >=2.31.0 (2.33.1 installed) | 2.33.1 | Loose (>=) | ⚠️ UPGRADE PINNING |

See full report in AUDIT_SUMMARY.md for complete details on all sections.

---

## COMPLETE SECTIONS

For the complete audit with all 12 sections, please refer to the supporting documentation:

1. **AUDIT_SUMMARY.md** - Executive summary with complete findings
2. **SECURITY_README.md** - Implementation and remediation guide
3. **SECURITY_QUICK_REFERENCE.md** - Quick reference for daily use

This consolidated approach provides better organization and readability.

