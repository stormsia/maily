// Generated from repository real data (.github/provider_health_state.json and public/dev/bench/data.js)

export interface RepoProviderHealth {
  consecutive_failures: number;
  issue_number: number | null;
  last_status: string;
}

export interface RepoBenchmarkItem {
  name: string;
  fullName: string;
  opsPerSec: number;
  unit: string;
  mean: string;
}

export interface RepoAnalyticsData {
  lastUpdated: string;
  providers: Record<string, RepoProviderHealth>;
  benchmarkMeta: {
    totalRuns: number;
    repoUrl: string;
    lastCommitMessage: string;
    lastCommitSha: string;
    lastCommitDate: string;
  };
  latestBenchmarks: RepoBenchmarkItem[];
}

export const REPO_ANALYTICS: RepoAnalyticsData = {
  lastUpdated: "2026-11-14T04:44:12Z",
  providers: {
  "anonymmail.net": {
    "consecutive_failures": 0,
    "issue_number": null,
    "last_status": "operational"
  },
  "dispoemail.org": {
    "consecutive_failures": 0,
    "issue_number": null,
    "last_status": "operational"
  },
  "mail.tm": {
    "consecutive_failures": 0,
    "issue_number": null,
    "last_status": "operational"
  },
  "noopmail.org": {
    "consecutive_failures": 0,
    "issue_number": null,
    "last_status": "operational"
  },
  "temp-mail.io": {
    "consecutive_failures": 0,
    "issue_number": null,
    "last_status": "operational"
  },
  "temp.tf": {
    "consecutive_failures": 0,
    "issue_number": null,
    "last_status": "operational"
  },
  "tempmail.plus": {
    "consecutive_failures": 0,
    "issue_number": null,
    "last_status": "operational"
  }
},
  benchmarkMeta: {
    totalRuns: 114,
    repoUrl: "https://github.com/stormsia/maily",
    lastCommitMessage: "chore(health): update live provider operational status [skip ci]",
    lastCommitSha: "c74cb57a96734137cd3650754863e11838585d24",
    lastCommitDate: "2026-11-14T04:44:12Z",
  },
  latestBenchmarks: [
  {
    "name": "crypto_encrypt_1kb",
    "fullName": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
    "opsPerSec": 81954.7,
    "unit": "iter/sec",
    "mean": "12.201868924872915 usec"
  },
  {
    "name": "crypto_decrypt_1kb",
    "fullName": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
    "opsPerSec": 79301.6,
    "unit": "iter/sec",
    "mean": "12.610079201417447 usec"
  },
  {
    "name": "random_string",
    "fullName": "tests/test_benchmarks.py::test_benchmark_random_string",
    "opsPerSec": 84627.0,
    "unit": "iter/sec",
    "mean": "11.816566555164695 usec"
  },
  {
    "name": "random_password",
    "fullName": "tests/test_benchmarks.py::test_benchmark_random_password",
    "opsPerSec": 55963.9,
    "unit": "iter/sec",
    "mean": "17.86864933616985 usec"
  },
  {
    "name": "pydantic_message_detail_parse",
    "fullName": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
    "opsPerSec": 557728.5,
    "unit": "iter/sec",
    "mean": "1.792987036974605 usec"
  },
  {
    "name": "pydantic_batch_messages_serialize",
    "fullName": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
    "opsPerSec": 5580.4,
    "unit": "iter/sec",
    "mean": "179.19882273229564 usec"
  },
  {
    "name": "extract_verification_code",
    "fullName": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
    "opsPerSec": 90263.4,
    "unit": "iter/sec",
    "mean": "11.078693208893366 usec"
  },
  {
    "name": "extract_confirmation_url",
    "fullName": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
    "opsPerSec": 114709.6,
    "unit": "iter/sec",
    "mean": "8.717668680748119 usec"
  },
  {
    "name": "authz_parse_scope",
    "fullName": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
    "opsPerSec": 248403.2,
    "unit": "iter/sec",
    "mean": "4.025713278489191 usec"
  },
  {
    "name": "authz_secret_sha256",
    "fullName": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
    "opsPerSec": 1318525.2,
    "unit": "iter/sec",
    "mean": "758.423114955904 nsec"
  },
  {
    "name": "health_endpoint",
    "fullName": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
    "opsPerSec": 331.1,
    "unit": "iter/sec",
    "mean": "3.020424009008753 msec"
  },
  {
    "name": "domain_cache_settings",
    "fullName": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
    "opsPerSec": 221.2,
    "unit": "iter/sec",
    "mean": "4.521516920634841 msec"
  },
  {
    "name": "mailboxes_list",
    "fullName": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
    "opsPerSec": 296.6,
    "unit": "iter/sec",
    "mean": "3.371953721311922 msec"
  },
  {
    "name": "admin_keys_list",
    "fullName": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
    "opsPerSec": 270.5,
    "unit": "iter/sec",
    "mean": "3.696450315000206 msec"
  },
  {
    "name": "client_init",
    "fullName": "tests/test_benchmarks.py::test_benchmark_client_init",
    "opsPerSec": 212.4,
    "unit": "iter/sec",
    "mean": "4.7071244791666205 msec"
  }
],
};
