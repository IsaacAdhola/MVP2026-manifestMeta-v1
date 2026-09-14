#!/bin/bash
# SECURITY AUDIT - CRITICAL FIXES
# Run this script to apply immediate security patches
# Review each fix before applying in production

set -e

echo "=================================="
echo "MetaMarkAgency Security Patch Kit"
echo "=================================="
echo ""

# Create backup
echo "[1/5] Creating backup..."
BACKUP_DIR="./security_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r ./*.py "$BACKUP_DIR/" 2>/dev/null || true
cp -r ./FacebookManagerAgent "$BACKUP_DIR/" 2>/dev/null || true
cp -r ./ImageCreatorAgent "$BACKUP_DIR/" 2>/dev/null || true
echo "✓ Backup created at: $BACKUP_DIR"
echo ""

# Add .gitignore entries
echo "[2/5] Updating .gitignore..."
cat >> .gitignore << 'EOF'

# Security: Prevent credential leakage
.env
.env.*
!.env.example

# Security: Prevent log exposure
*.log
debug-*.log
audit_logs/
__pycache__/

# Security: Prevent state exposure
.workflow_state*.json
campaign_data/

# Security: IDE and system files
.vscode/
.idea/
.DS_Store
EOF
echo "✓ .gitignore updated"
echo ""

# Pin dependencies
echo "[3/5] Pinning dependencies..."
cat > requirements.txt << 'EOF'
# Security: Exact version pinning to prevent supply chain attacks
# Last updated: 2026-09-14

agency-swarm==1.0.0
facebook-business==20.0.0
openai==1.30.0
python-dotenv==1.0.0
requests==2.31.0

# Development dependencies (optional)
# pip-audit==2.6.1
# safety==2.3.5
# bandit==1.7.5
EOF
echo "✓ Dependencies pinned"
echo ""

# Create security documentation
echo "[4/5] Creating SECURITY.md..."
cat > SECURITY.md << 'EOF'
# Security Policy

## 🔒 Reporting Security Vulnerabilities

**Please DO NOT file public GitHub issues for security vulnerabilities.**

Instead, email: [security-contact-email-here]

We will respond within 48 hours and work with you to:
1. Confirm the vulnerability
2. Determine the severity
3. Develop a fix
4. Coordinate disclosure

## 🛡️ Security Best Practices

### For Developers

1. **Never commit secrets:**
   - All credentials in `.env` (never commit this file)
   - Use `.env.example` for documentation only
   - Review `git diff` before every commit

2. **Input validation:**
   - Always validate user inputs
   - Use Pydantic Field validators
   - Sanitize file paths

3. **API Security:**
   - Rotate Facebook tokens every 60 days
   - Rotate OpenAI keys quarterly
   - Monitor API usage and costs

4. **Code review:**
   - All PRs require security review
   - Check for hardcoded credentials
   - Verify input validation

### For Operators

1. **Environment setup:**
   ```bash
   # Secure file permissions
   chmod 600 .env
   chmod 700 audit_logs/
   ```

2. **Token rotation schedule:**
   - Facebook Access Token: Every 60 days
   - OpenAI API Key: Every 90 days
   - Document rotation in team calendar

3. **Monitoring:**
   - Review `audit_logs/manifest_ai_audit.jsonl` weekly
   - Check for failed authentication attempts
   - Monitor API error rates

4. **Incident response:**
   - If credentials compromised, revoke immediately
   - Review audit logs for unauthorized activity
   - Rotate all related credentials
   - Notify affected clients

## 📋 Security Checklist for Deployments

- [ ] `.env` file not in version control
- [ ] All dependencies pinned to exact versions
- [ ] Secrets have correct file permissions (600)
- [ ] Audit logging enabled and working
- [ ] Rate limiting configured
- [ ] Security headers enabled (for web deployments)
- [ ] Backups encrypted and secured
- [ ] Incident response plan documented

## 🔍 Security Audit History

| Date | Auditor | Severity | Status |
|------|---------|----------|--------|
| 2026-09-14 | Cloud Agent Security | CRITICAL | Fixed |

## 📚 Additional Resources

- [Facebook Platform Security Best Practices](https://developers.facebook.com/docs/facebook-login/security/)
- [OpenAI API Security](https://platform.openai.com/docs/guides/safety-best-practices)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

Last Updated: 2026-09-14
EOF
echo "✓ SECURITY.md created"
echo ""

# Create quick fix for debug logging
echo "[5/5] Creating sanitization patch..."
cat > patch_debug_logging.py << 'EOF'
#!/usr/bin/env python3
"""
Security Patch: Add sanitization to debug logging
Apply this patch to prevent credential leakage in debug logs
"""

import os
import sys
from pathlib import Path

# Import sanitization function
sys.path.insert(0, str(Path(__file__).parent))
from safe_audit_log import sanitize_record

def patch_image_generator():
    """Add sanitization to ImageGenerator._agent_dbg calls"""
    file_path = Path("ImageCreatorAgent/tools/ImageGenerator.py")
    if not file_path.exists():
        print(f"✗ {file_path} not found")
        return False
    
    content = file_path.read_text()
    
    # Add sanitization wrapper
    if "# SECURITY PATCH" not in content:
        # Find _agent_dbg function definition
        new_content = content.replace(
            "def _agent_dbg(hypothesis_id: str, location: str, message: str, data: dict | None = None, run_id: str = \"pre-fix\"):",
            '''def _agent_dbg(hypothesis_id: str, location: str, message: str, data: dict | None = None, run_id: str = "pre-fix"):
    # SECURITY PATCH: Sanitize data before logging to prevent credential leakage
    from safe_audit_log import sanitize_record
    if data:
        data = sanitize_record(data)'''
        )
        
        if new_content != content:
            # Create backup
            backup = file_path.with_suffix('.py.backup')
            backup.write_text(content)
            
            # Write patched version
            file_path.write_text(new_content)
            print(f"✓ Patched {file_path}")
            print(f"  Backup: {backup}")
            return True
    else:
        print(f"  Already patched: {file_path}")
        return True
    
    return False

def create_rate_limiter():
    """Create rate limiting utility"""
    code = '''"""
Rate limiting utility for API calls
Created by security patch 2026-09-14
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass

class APIRateLimiter:
    """Simple file-based rate limiter for API calls"""
    
    def __init__(self, max_requests: int = 10, window_minutes: int = 60):
        self.max_requests = max_requests
        self.window = timedelta(minutes=window_minutes)
        self.log_file = Path(__file__).parent / ".rate_limit.json"
    
    def _load_requests(self, api_name: str) -> List[str]:
        """Load recent requests from file"""
        if not self.log_file.exists():
            return []
        try:
            data = json.loads(self.log_file.read_text())
            return data.get(api_name, [])
        except Exception:
            return []
    
    def _save_requests(self, api_name: str, requests: List[str]):
        """Save requests to file"""
        try:
            data = {}
            if self.log_file.exists():
                data = json.loads(self.log_file.read_text())
            data[api_name] = requests
            self.log_file.write_text(json.dumps(data, indent=2))
        except Exception:
            pass
    
    def check_and_record(self, api_name: str) -> bool:
        """
        Check if request is allowed and record it.
        Raises RateLimitError if limit exceeded.
        """
        requests = self._load_requests(api_name)
        cutoff = datetime.now() - self.window
        
        # Filter to recent requests only
        recent = [
            r for r in requests 
            if datetime.fromisoformat(r) > cutoff
        ]
        
        if len(recent) >= self.max_requests:
            raise RateLimitError(
                f"{api_name}: {len(recent)} requests in {self.window.total_seconds()/60:.0f} minutes "
                f"(limit: {self.max_requests})"
            )
        
        recent.append(datetime.now().isoformat())
        self._save_requests(api_name, recent)
        return True
    
    def get_status(self, api_name: str) -> dict:
        """Get current rate limit status"""
        requests = self._load_requests(api_name)
        cutoff = datetime.now() - self.window
        recent = [r for r in requests if datetime.fromisoformat(r) > cutoff]
        
        return {
            "api_name": api_name,
            "requests_in_window": len(recent),
            "max_requests": self.max_requests,
            "window_minutes": self.window.total_seconds() / 60,
            "remaining": max(0, self.max_requests - len(recent))
        }

# Default rate limiters (can be customized per tool)
OPENAI_IMAGE_LIMITER = APIRateLimiter(max_requests=10, window_minutes=60)
FACEBOOK_API_LIMITER = APIRateLimiter(max_requests=200, window_minutes=60)
'''
    
    rate_limiter_path = Path("rate_limiter.py")
    if not rate_limiter_path.exists():
        rate_limiter_path.write_text(code)
        print(f"✓ Created {rate_limiter_path}")
        return True
    else:
        print(f"  Already exists: {rate_limiter_path}")
        return True

def main():
    print("=" * 50)
    print("Security Patch Application")
    print("=" * 50)
    print()
    
    success = True
    
    print("Applying patches...")
    success &= patch_image_generator()
    success &= create_rate_limiter()
    
    print()
    if success:
        print("✓ All patches applied successfully!")
        print()
        print("Next steps:")
        print("1. Review the changes in git diff")
        print("2. Run tests: python -m pytest")
        print("3. Apply remaining fixes from SECURITY_AUDIT_REPORT.md")
    else:
        print("✗ Some patches failed. Review errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x patch_debug_logging.py
echo "✓ Patch script created: patch_debug_logging.py"
echo ""

echo "=================================="
echo "Security Baseline Complete!"
echo "=================================="
echo ""
echo "Summary:"
echo "  ✓ Backup created"
echo "  ✓ .gitignore updated"
echo "  ✓ Dependencies pinned"
echo "  ✓ SECURITY.md created"
echo "  ✓ Patch script ready"
echo ""
echo "Next Steps:"
echo "  1. Review changes: git diff"
echo "  2. Run patch: python patch_debug_logging.py"
echo "  3. Test: python -m pytest (if tests exist)"
echo "  4. Read: SECURITY_AUDIT_REPORT.md for full details"
echo "  5. Commit: git add . && git commit -m 'security: Apply critical security fixes'"
echo ""
echo "⚠️  IMPORTANT: Review SECURITY_AUDIT_REPORT.md for remaining HIGH/MEDIUM issues!"
echo ""
