# cURL & Authentication Cheat Sheet

Authenticate all requests with the `X-API-Key` HTTP header.

### List available targets (domains)
```bash
curl -X GET "${window.location.origin}/v1/targets" \
  -H "X-API-Key: ${getSavedKey() || 'YOUR_API_KEY'}" \
  -H "Accept: application/json"
```

### Create disposable mailbox
```bash
curl -X POST "${window.location.origin}/v1/mailboxes" \
  -H "X-API-Key: ${getSavedKey() || 'YOUR_API_KEY'}" \
  -H "Content-Type: application/json" \
  -d '{"provider": "mail.tm", "domain": "mail.tm"}'
```

### Fetch messages for mailbox
```bash
curl -X GET "${window.location.origin}/v1/mailboxes/1/messages" \
  -H "X-API-Key: ${getSavedKey() || 'YOUR_API_KEY'}"
```

### Inspect single message (text & HTML)
```bash
curl -X GET "${window.location.origin}/v1/mailboxes/1/messages/MESSAGE_ID" \
  -H "X-API-Key: ${getSavedKey() || 'YOUR_API_KEY'}"
```

### Create scoped API key
```bash
curl -X POST "${window.location.origin}/v1/keys" \
  -H "X-API-Key: ${getSavedKey() || 'YOUR_API_KEY'}" \
  -H "Content-Type: application/json" \
  -d '{"name": "worker", "scope": {"providers": ["mail.tm"], "actions": ["read", "write"]}}'
```

### Run retention sweep & database maintenance
```bash
curl -X POST "${window.location.origin}/v1/admin/retention/run?force_maintenance=true" \
  -H "X-API-Key: ${getSavedKey() || 'YOUR_API_KEY'}"
```
