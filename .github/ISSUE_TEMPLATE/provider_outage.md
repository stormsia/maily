---
name: Provider Outage Report
about: Automated or manual alert for external mail provider degradation
title: '[Provider Outage] <Provider Name> (<slug>) health checks failing'
labels: ['bug', 'provider-outage', 'automated-health']
assignees: ''
---

## 🚨 Provider Outage Alert

### 📋 Outage Summary
* **Provider:** `<Provider Name>` (`<provider.slug>`)
* **Consecutive Failures:** 3+
* **Detected At:** `YYYY-MM-DD HH:MM UTC`
* **Trigger:** Scheduled Health Suite / PR Verification

### ❌ Failure Diagnostic
* **Failed Stage:** `list_targets` / `create_mailbox` / `list_messages` / `email_delivery`
* **Error Message:** `<error message>`
* **Mailbox Tested:** `<address>`

### 🔍 Diagnostic Logs & Trace
```
<paste error logs or stack trace here>
```

### 🛠️ Recommended Actions
1. Check if the upstream provider website is currently online or undergoing DDoS/maintenance.
2. Verify if upstream HTML structure, CSRF tokens, or API signatures changed.
3. Check if IP ranges from GitHub Actions / CI runners are being blocked.
