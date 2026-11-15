import json
from pathlib import Path

# 1. Load provider health
provider_health_path = Path(".github/provider_health_state.json")
provider_health = {}
if provider_health_path.exists():
    try:
        raw = json.loads(provider_health_path.read_text(encoding="utf-8"))
        provider_health = raw.get("providers", {})
    except Exception as e:
        print("Error loading provider health:", e)

# 2. Load benchmark data
bench_path = Path("public/dev/bench/data.js")
bench_entries = []
bench_meta = {}
if bench_path.exists():
    try:
        text = bench_path.read_text(encoding="utf-8")
        json_str = text.split("=", 1)[1].strip().rstrip(";")
        data = json.loads(json_str)
        bench_entries = data.get("entries", {}).get("Benchmark", [])
        bench_meta = {
            "lastUpdate": data.get("lastUpdate"),
            "repoUrl": data.get("repoUrl"),
            "totalRuns": len(bench_entries),
        }
    except Exception as e:
        print("Error loading benchmarks:", e)

latest_benches = []
last_commit = {}
if bench_entries:
    latest = bench_entries[-1]
    last_commit = latest.get("commit", {})
    for b in latest.get("benches", []):
        short_name = b["name"].split("::")[-1].replace("test_benchmark_", "")
        # extract extra mean if available
        mean_str = ""
        if "extra" in b and "mean:" in b["extra"]:
            for line in b["extra"].splitlines():
                if line.startswith("mean:"):
                    mean_str = line.replace("mean:", "").strip()
        latest_benches.append(
            {
                "name": short_name,
                "fullName": b["name"],
                "opsPerSec": round(b["value"], 1),
                "unit": b.get("unit", "iter/sec"),
                "mean": mean_str,
            }
        )

output_file = Path("site/src/data/repoAnalytics.ts")
content = f"""// Generated from repository real data (.github/provider_health_state.json and public/dev/bench/data.js)

export interface RepoProviderHealth {{
  consecutive_failures: number;
  issue_number: number | null;
  last_status: string;
}}

export interface RepoBenchmarkItem {{
  name: string;
  fullName: string;
  opsPerSec: number;
  unit: string;
  mean: string;
}}

export interface RepoAnalyticsData {{
  lastUpdated: string;
  providers: Record<string, RepoProviderHealth>;
  benchmarkMeta: {{
    totalRuns: number;
    repoUrl: string;
    lastCommitMessage: string;
    lastCommitSha: string;
    lastCommitDate: string;
  }};
  latestBenchmarks: RepoBenchmarkItem[];
}}

export const REPO_ANALYTICS: RepoAnalyticsData = {{
  lastUpdated: {json.dumps(str(last_commit.get("timestamp", "")))},
  providers: {json.dumps(provider_health, indent=2)},
  benchmarkMeta: {{
    totalRuns: {bench_meta.get("totalRuns", 0)},
    repoUrl: {json.dumps(bench_meta.get("repoUrl", "https://github.com/stormsia/maily"))},
    lastCommitMessage: {json.dumps(last_commit.get("message", "Continuous benchmark update"))},
    lastCommitSha: {json.dumps(last_commit.get("id", ""))},
    lastCommitDate: {json.dumps(last_commit.get("timestamp", ""))},
  }},
  latestBenchmarks: {json.dumps(latest_benches, indent=2)},
}};
"""

output_file.write_text(content, encoding="utf-8")
print("Successfully generated site/src/data/repoAnalytics.ts with real repository data!")
