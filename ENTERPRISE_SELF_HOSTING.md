# Enterprise Self-Hosting Guide

**MetaMarkAgency: On-Premise Deployment for Maximum Security and Control**

---

## Why Self-Host?

### Data Sovereignty
- **Your data never leaves your infrastructure**
- Compliance with GDPR, HIPAA, SOC2, ISO 27001
- Full control over data retention and deletion policies
- No third-party data sharing

### Customization
- Add your own agents for industry-specific workflows
- Integrate with internal tools and APIs
- Custom compliance rules for your industry
- White-label for your brand

### Security
- Air-gapped deployment options
- No internet dependency (except OpenAI API)
- Your own security policies and access controls
- Audit logs stay in your control

---

## Deployment Options

### Option 1: Docker (Recommended)
**Best for:** Most enterprises, cloud or on-premise

```bash
# Pull the image
docker pull metamarkagency/agency:latest

# Run with environment variables
docker run -d \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e FACEBOOK_APP_ID=$FACEBOOK_APP_ID \
  -e FACEBOOK_APP_SECRET=$FACEBOOK_APP_SECRET \
  -e FACEBOOK_ACCESS_TOKEN=$FACEBOOK_ACCESS_TOKEN \
  -e FACEBOOK_AD_ACCOUNT_ID=$FACEBOOK_AD_ACCOUNT_ID \
  -e FACEBOOK_PAGE_ID=$FACEBOOK_PAGE_ID \
  -v /path/to/data:/workspace/.governed_memory \
  -v /path/to/audit:/workspace/.audit_logs \
  -p 8000:8000 \
  metamarkagency/agency:latest
```

**Persistent storage:**
- Governed memory: `/workspace/.governed_memory`
- Audit logs: `/workspace/.audit_logs`
- Rate limiter data: `/workspace/.rate_limiter`
- API version data: `/workspace/.api_versions`

---

### Option 2: Kubernetes
**Best for:** Large-scale deployments, auto-scaling

See `k8s/deployment.yaml` for full configuration:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metamarkagency
spec:
  replicas: 3
  selector:
    matchLabels:
      app: metamarkagency
  template:
    metadata:
      labels:
        app: metamarkagency
    spec:
      containers:
      - name: agency
        image: metamarkagency/agency:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: metamark-secrets
              key: openai-api-key
        volumeMounts:
        - name: data
          mountPath: /workspace/.governed_memory
        - name: audit
          mountPath: /workspace/.audit_logs
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: metamark-data-pvc
      - name: audit
        persistentVolumeClaim:
          claimName: metamark-audit-pvc
```

---

### Option 3: VM Deployment
**Best for:** Air-gapped environments, strict security requirements

#### System Requirements
- **OS:** Ubuntu 20.04+ or RHEL 8+
- **CPU:** 4 cores minimum (8 recommended)
- **RAM:** 8GB minimum (16GB recommended)
- **Disk:** 50GB SSD minimum
- **Network:** Outbound HTTPS (443) to OpenAI API only

#### Installation Steps

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python 3.10+
sudo apt install python3.10 python3.10-pip -y

# 3. Create service user
sudo useradd -m -s /bin/bash metamark
sudo su - metamark

# 4. Clone repository
git clone https://github.com/YourRepo/MetaMarkAgency.git
cd MetaMarkAgency

# 5. Install dependencies
pip3 install -r requirements.txt

# 6. Configure environment
cp .env.example .env
nano .env  # Add your credentials

# 7. Create systemd service
sudo nano /etc/systemd/system/metamarkagency.service
```

**Service file:**
```ini
[Unit]
Description=MetaMarkAgency
After=network.target

[Service]
Type=simple
User=metamark
WorkingDirectory=/home/metamark/MetaMarkAgency
Environment="PATH=/home/metamark/.local/bin"
ExecStart=/usr/bin/python3 agency.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 8. Start service
sudo systemctl enable metamarkagency
sudo systemctl start metamarkagency
sudo systemctl status metamarkagency
```

---

## Security Hardening

### 1. Credential Management

**Use HashiCorp Vault or AWS Secrets Manager:**

```python
# Example: AWS Secrets Manager integration
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name='us-east-1'
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        return get_secret_value_response['SecretString']
    except ClientError as e:
        raise e

# In your .env or code
OPENAI_API_KEY = get_secret("metamark/openai_api_key")
```

### 2. Network Isolation

**Whitelist only required endpoints:**
- OpenAI API: `api.openai.com` (443)
- Facebook Graph API: `graph.facebook.com` (443)
- Meta Ad Library: `graph.facebook.com` (443)

**Block all other outbound traffic.**

### 3. Data Encryption

**Encrypt data at rest:**
```bash
# Use LUKS for disk encryption
sudo cryptsetup luksFormat /dev/sdb
sudo cryptsetup luksOpen /dev/sdb metamark-data
sudo mkfs.ext4 /dev/mapper/metamark-data
sudo mount /dev/mapper/metamark-data /mnt/metamark-data
```

**Encrypt data in transit:**
- TLS 1.3 for all API calls (default with OpenAI/Facebook)
- No plaintext transmission of credentials

### 4. Access Control

**RBAC with governed memory:**
```python
from governed_memory import GovernedMemory, MemoryScope, MemoryPermission

memory = GovernedMemory()

# Grant specific permissions to each agent
memory.grant_permission(
    agent_id="research_agent",
    scope=MemoryScope.WORKFLOW,
    permissions=[MemoryPermission.READ, MemoryPermission.WRITE]
)

memory.grant_permission(
    agent_id="research_agent",
    scope=MemoryScope.GLOBAL,
    permissions=[MemoryPermission.READ]  # Read-only global access
)

# CEO has full access
memory.grant_permission(
    agent_id="ceo",
    scope=MemoryScope.GLOBAL,
    permissions=[MemoryPermission.READ, MemoryPermission.WRITE, MemoryPermission.DELETE]
)
```

### 5. Audit Logging

**Centralized logging with ELK stack:**
```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /workspace/.audit_logs/*.log
  fields:
    service: metamarkagency
    environment: production

output.elasticsearch:
  hosts: ["your-elk-server:9200"]
  index: "metamark-audit-%{+yyyy.MM.dd}"
```

---

## Compliance & Certifications

### GDPR Compliance

**Automatic data deletion:**
```python
from governed_memory import GovernedMemory

memory = GovernedMemory()

# After campaign completion
memory.cleanup_workflow("campaign_123")
# All PII, client data, and campaign data deleted
```

**Right to be forgotten:**
```python
# Delete all data for a specific client
def delete_client_data(client_id: str):
    memory = GovernedMemory()
    # Find all workflows for this client
    workflows = get_workflows_for_client(client_id)
    for workflow_id in workflows:
        memory.cleanup_workflow(workflow_id)
```

### SOC2 Type II

**Audit trail requirements:**
- ✅ All actions logged with provenance
- ✅ Immutable audit logs
- ✅ Access control with RBAC
- ✅ Encryption at rest and in transit
- ✅ Automated compliance monitoring

**Export audit logs for compliance:**
```bash
# Generate SOC2 compliance report
python generate_compliance_report.py --start 2026-01-01 --end 2026-12-31
```

### HIPAA (Healthcare)

**For healthcare marketing:**
- ✅ PHI never stored (only de-identified data)
- ✅ Encrypted storage
- ✅ Access logs
- ✅ Automatic session timeouts
- ✅ Role-based access control

---

## Customization for Enterprises

### Add Custom Agents

```python
# custom_agents/IndustrySpecificAgent.py
from agency_swarm import Agent, ModelSettings

industry_agent = Agent(
    name="IndustrySpecificAgent",
    description="Custom agent for your industry vertical",
    instructions="./instructions.md",
    tools_folder="./tools",
    model_settings=ModelSettings(
        model="gpt-4o",
        temperature=0.5,
    ),
)
```

**Integrate into agency:**
```python
# agency.py
from custom_agents.IndustrySpecificAgent import industry_agent

agency = Agency(
    ceo,
    communication_flows=[
        (ceo, industry_agent),
        (industry_agent, developer),
        # ... rest of flows
    ],
    shared_instructions="agency_manifesto.md",
)
```

### White-Label Configuration

```python
# config/white_label.py
BRANDING = {
    "company_name": "Your Agency Name",
    "logo_url": "https://yourdomain.com/logo.png",
    "primary_color": "#FF6B6B",
    "support_email": "support@youragency.com",
    "terms_url": "https://youragency.com/terms",
}
```

### Custom Integrations

**Connect to your internal APIs:**
```python
# custom_tools/InternalCRMIntegration.py
from agency_swarm.tools import BaseTool
import requests

class InternalCRMIntegration(BaseTool):
    """
    Fetch client data from your internal CRM.
    """
    client_id: str
    
    def run(self):
        response = requests.get(
            f"https://internal-crm.yourcompany.com/api/clients/{self.client_id}",
            headers={"Authorization": f"Bearer {os.getenv('CRM_API_TOKEN')}"}
        )
        return response.json()
```

---

## Scaling & Performance

### Horizontal Scaling

**Load balancing with multiple instances:**
```yaml
# docker-compose.yml
version: '3'
services:
  metamark-1:
    image: metamarkagency/agency:latest
    environment:
      - INSTANCE_ID=1
  metamark-2:
    image: metamarkagency/agency:latest
    environment:
      - INSTANCE_ID=2
  metamark-3:
    image: metamarkagency/agency:latest
    environment:
      - INSTANCE_ID=3
  
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Caching Layer

**Redis for API response caching:**
```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379)

def cache_api_response(ttl=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

---

## Monitoring & Observability

### Prometheus Metrics

```python
# metrics.py
from prometheus_client import Counter, Histogram, start_http_server

api_requests = Counter('api_requests_total', 'Total API requests', ['provider'])
request_duration = Histogram('request_duration_seconds', 'Request duration')
budget_spent = Counter('budget_spent_dollars', 'Budget spent', ['campaign_id'])

# In your code
api_requests.labels(provider='openai').inc()
budget_spent.labels(campaign_id='campaign_123').inc(0.01)
```

### Grafana Dashboards

**Key metrics to monitor:**
- API request rate (by provider)
- API error rate
- Budget utilization
- Campaign success rate
- Agent performance metrics
- Memory usage
- Audit log volume

---

## Enterprise Support

### Support Tiers

**Standard** (Included)
- Email support (24-hour response)
- Community forums
- Documentation access

**Premium** ($2,500/month)
- 4-hour response SLA
- Dedicated Slack channel
- Monthly strategy calls
- Custom agent development (4 hours/month)

**Enterprise** (Custom pricing)
- 1-hour critical issue SLA
- Dedicated support engineer
- On-site deployment assistance
- Unlimited custom development
- White-glove onboarding

### Professional Services

- **Initial deployment:** $10,000 (1-2 weeks)
- **Custom agent development:** $5,000/agent
- **Integration development:** $2,500/integration
- **Training:** $1,500/day (on-site or virtual)
- **Annual audit & optimization:** $15,000/year

---

## Migration from SaaS

**Moving from Jasper, Copy.ai, or other tools:**

### Data Export
```bash
# Export your historical campaigns
python scripts/export_campaigns.py --output campaigns.json

# Import to MetaMarkAgency
python scripts/import_campaigns.py --input campaigns.json
```

### Gradual Rollout
1. **Week 1:** Deploy parallel to existing tool
2. **Week 2-4:** Run 25% of campaigns through MetaMarkAgency
3. **Week 5-8:** Scale to 50% of campaigns
4. **Week 9-12:** Full migration, decommission old tool

### Training
- 2-day workshop for marketing team
- 1-day technical training for IT/DevOps
- 4-week support period with weekly check-ins

---

## License Options

### Community Edition (Apache 2.0)
- ✅ Free forever
- ✅ Self-host unlimited instances
- ✅ Modify source code
- ✅ Commercial use allowed
- ⚠️ No dedicated support
- ⚠️ No white-label rights

### Enterprise License ($25,000/year)
- ✅ Everything in Community
- ✅ White-label rights
- ✅ Priority support (Premium tier)
- ✅ Custom agent development (12 hours/year)
- ✅ Quarterly security audits
- ✅ Indemnification

### OEM License (Custom)
- ✅ Embed in your product
- ✅ Resell as your own
- ✅ Full source code access
- ✅ Perpetual license option

---

## Get Started

### Contact Sales
📧 **Email:** enterprise@metamarkagency.com  
📞 **Phone:** +1 (555) 123-4567  
🗓️ **Book demo:** https://calendly.com/metamark/enterprise-demo

### Trial
- 30-day free trial (up to 10 campaigns)
- Full feature access
- Dedicated onboarding engineer
- No credit card required

---

**MetaMarkAgency Enterprise** - *Your data, your infrastructure, your control.*
