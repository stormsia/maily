import React from 'react';
import { CodeBlock } from '../../components/common/CodeBlock';
import { Callout } from '../../components/common/Callout';
import { Link } from '../../context/RouterContext';
import { ArrowRight, Server, ShieldCheck, Terminal, Layers, RefreshCw, Cpu } from 'lucide-react';
import { GithubIcon } from '../../components/common/Icons';

export const DocsDocker: React.FC = () => {
  return (
    <div className="space-y-10">
      {/* Header */}
      <section>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 text-xs font-mono mb-4">
          <span>Docker & Self-Hosting Guide</span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white font-display" id="docker-guide">
            Deploy Maily in 60 Seconds
          </h2>
          <a
            href="https://github.com/stormsia/maily#option-a--docker-pre-built-image-no-git-clone-required"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 shadow-sm transition-all self-start sm:self-auto"
          >
            <GithubIcon className="w-3.5 h-3.5" />
            <span>Docker Guide in GitHub README ↗</span>
          </a>
        </div>
        <p className="text-base leading-relaxed text-slate-300">
          Maily is packaged as an optimized, multi-stage, security-hardened container published to GitHub Container Registry as <code className="text-cyan-400 font-mono">ghcr.io/stormsia/maily:latest</code>. It runs the core <strong>Maily Gateway Server</strong> required by all SDKs, test suites, and automation scripts.
        </p>
      </section>

      {/* Core Server Role Callout */}
      <Callout type="note" title="Core Gateway Server Role">
        <p className="text-xs leading-relaxed text-cyan-200/90">
          This container runs the unified backend service. It connects to 8+ upstream disposable email providers, manages embedded SQLite WAL message stores, handles AES-GCM encryption, and serves the REST API on port <code className="font-mono text-white">8477</code>. Both <code className="font-mono text-white">maily-client</code> and Playwright/Pytest suites require this container to be running.
        </p>
      </Callout>

      {/* Option 1: Single Docker Command */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="docker-run">
          Option 1 — Single Command (<code className="font-mono text-cyan-400">docker run</code>)
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          The fastest way to spin up a local or CI instance with persistent storage:
        </p>
        <CodeBlock
          language="bash"
          code={`docker run -d \\
  --name maily \\
  -p 8477:8477 \\
  -e MAILY_API_KEY=your_secret_api_key \\
  -v maily_data:/data \\
  --restart unless-stopped \\
  ghcr.io/stormsia/maily:latest`}
        />
        <div className="mt-3 flex items-center gap-4 text-xs font-mono text-slate-400">
          <span>● Dashboard: http://127.0.0.1:8477</span>
          <span>● API Docs: http://127.0.0.1:8477/docs</span>
        </div>
      </section>

      {/* Option 2: Docker Compose */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="docker-compose">
          Option 2 — Production Docker Compose
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Download and run the official production Compose configuration:
        </p>
        <CodeBlock
          language="bash"
          code={`# Linux / macOS
curl -O https://raw.githubusercontent.com/stormsia/maily/main/docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d

# Windows PowerShell
Invoke-WebRequest -Uri https://raw.githubusercontent.com/stormsia/maily/main/docker-compose.prod.yml -OutFile docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d`}
        />
        <p className="text-xs text-slate-400 mt-4 mb-2">Production <code className="text-cyan-400 font-mono">docker-compose.prod.yml</code> specification:</p>
        <CodeBlock
          language="yaml"
          filename="docker-compose.prod.yml"
          code={`services:
  maily:
    image: ghcr.io/stormsia/maily:latest
    container_name: maily
    restart: unless-stopped
    ports:
      - "8477:8477"
    environment:
      - MAILY_HOST=0.0.0.0
      - MAILY_PORT=8477
      - MAILY_API_KEY=your_secret_api_key
      - MAILY_DB_PATH=/data/maily.db
      - MAILY_LOG_LEVEL=INFO
    volumes:
      - maily_data:/data
    healthcheck:
      test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\\"http://127.0.0.1:8477/health\\")'"]
      interval: 30s
      timeout: 5s
      retries: 3
    security_opt:
      - no-new-privileges:true
    read_only: false

volumes:
  maily_data:
    driver: local`}
        />
      </section>

      {/* Option 3: Portainer 1-Click Template */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="portainer">
          Option 3 — Portainer 1-Click App Template
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Maily includes a native Portainer V3 App Template. Add the template URL in your Portainer Settings:
        </p>
        <CodeBlock
          language="text"
          code="https://raw.githubusercontent.com/stormsia/maily/main/portainer-template.json"
        />
        <p className="text-xs text-slate-400 mt-2">
          Navigate to <strong>App Templates</strong> in Portainer, select <strong>Maily</strong>, input your <code className="text-cyan-400 font-mono">MAILY_API_KEY</code>, and click <strong>Deploy the container</strong>.
        </p>
      </section>

      {/* Option 4: Kubernetes Helm & Manifests */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="kubernetes">
          Option 4 — Kubernetes Manifests
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Deploy Maily onto a Kubernetes cluster with a persistent volume and ingress controller:
        </p>
        <CodeBlock
          language="yaml"
          filename="maily-k8s.yaml"
          code={`apiVersion: apps/v1
kind: Deployment
metadata:
  name: maily-gateway
  namespace: testing
spec:
  replicas: 1
  selector:
    matchLabels:
      app: maily
  template:
    metadata:
      labels:
        app: maily
    spec:
      securityContext:
        runAsUser: 65534
        runAsGroup: 65534
        fsGroup: 65534
      containers:
        - name: maily
          image: ghcr.io/stormsia/maily:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8477
          env:
            - name: MAILY_HOST
              value: "0.0.0.0"
            - name: MAILY_PORT
              value: "8477"
            - name: MAILY_API_KEY
              valueFrom:
                secretKeyRef:
                  name: maily-secrets
                  key: api-key
          volumeMounts:
            - name: data
              mountPath: /data
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: maily-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: maily-service
  namespace: testing
spec:
  selector:
    app: maily
  ports:
    - protocol: TCP
      port: 8477
      targetPort: 8477`}
        />
      </section>

      {/* Reverse Proxy Configuration */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="reverse-proxy">
          Reverse Proxy: Nginx & SSE Buffering
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          When proxying behind Nginx, disable proxy buffering so Server-Sent Events (SSE) stream without buffering:
        </p>
        <CodeBlock
          language="nginx"
          filename="/etc/nginx/conf.d/maily.conf"
          code={`server {
    listen 80;
    server_name mail.internal.corp;

    location / {
        proxy_pass http://127.0.0.1:8477;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Disable buffering for real-time SSE streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}`}
        />
      </section>

      {/* Environment Variables Reference */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="env-vars">
          Environment Variables Reference
        </h3>
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-mono bg-slate-950/60">
                <th className="py-2.5 px-3">Variable</th>
                <th className="py-2.5 px-3">Default</th>
                <th className="py-2.5 px-3">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono">
              <tr>
                <td className="py-2.5 px-3 text-cyan-400">MAILY_HOST</td>
                <td className="py-2.5 px-3 text-slate-400">0.0.0.0</td>
                <td className="py-2.5 px-3 text-slate-300">Listening host IP binding</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-cyan-400">MAILY_PORT</td>
                <td className="py-2.5 px-3 text-slate-400">8477</td>
                <td className="py-2.5 px-3 text-slate-300">HTTP server listening port</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-cyan-400">MAILY_API_KEY</td>
                <td className="py-2.5 px-3 text-slate-400">None</td>
                <td className="py-2.5 px-3 text-slate-300">Root master API key for X-API-Key auth</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-cyan-400">MAILY_DB_PATH</td>
                <td className="py-2.5 px-3 text-slate-400">/data/maily.db</td>
                <td className="py-2.5 px-3 text-slate-300">Path to SQLite database file</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-cyan-400">MAILY_SECRET_KEY</td>
                <td className="py-2.5 px-3 text-slate-400">Auto-generated</td>
                <td className="py-2.5 px-3 text-slate-300">Fernet symmetric 256-bit encryption key</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-cyan-400">MAILY_CLEANUP_INTERVAL</td>
                <td className="py-2.5 px-3 text-slate-400">3600</td>
                <td className="py-2.5 px-3 text-slate-300">Retention sweep interval (seconds)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-cyan-400">MAILY_LOG_LEVEL</td>
                <td className="py-2.5 px-3 text-slate-400">INFO</td>
                <td className="py-2.5 px-3 text-slate-300">Log level: DEBUG, INFO, WARNING, ERROR</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Hardened Container */}
      <Callout type="tip" title="Unprivileged Security Architecture">
        The official Docker container runs as unprivileged user <code className="font-mono">65534:65534 (nobody:nogroup)</code>. It does not require root permissions, making it safe for compliance in restricted enterprise Kubernetes clusters.
      </Callout>

      {/* Navigation */}
      <div className="pt-6 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/curl" className="text-slate-400 hover:text-white">
          ← cURL & REST API Guide
        </Link>
        <Link
          to="/docs/providers"
          className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold"
        >
          <span>Provider Matrix</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
