window.BENCHMARK_DATA = {
  "lastUpdate": 1793493782808,
  "repoUrl": "https://github.com/stormsia/mailtmapi",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "name": "stormsia",
            "username": "stormsia",
            "email": "sf_root@outlook.com"
          },
          "committer": {
            "name": "stormsia",
            "username": "stormsia",
            "email": "sf_root@outlook.com"
          },
          "id": "08d964c7738b092473eb403f6ee73978e619be0f",
          "message": "fix(tests): enhance resource management and suppress warnings in test cases",
          "timestamp": "2026-10-31T21:06:26Z",
          "url": "https://github.com/stormsia/mailtmapi/commit/08d964c7738b092473eb403f6ee73978e619be0f"
        },
        "date": 1793481411827,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 61360.87065944241,
            "unit": "iter/sec",
            "range": "stddev: 0.00000355434065469528",
            "extra": "mean: 16.297030815453674 usec\nrounds: 649"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 58453.98538760537,
            "unit": "iter/sec",
            "range": "stddev: 0.000004083033709967025",
            "extra": "mean: 17.107473397563083 usec\nrounds: 15976"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73736.70462999864,
            "unit": "iter/sec",
            "range": "stddev: 0.000002518948477362371",
            "extra": "mean: 13.56176689774614 usec\nrounds: 27696"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49298.97515932694,
            "unit": "iter/sec",
            "range": "stddev: 0.0000030973248600759254",
            "extra": "mean: 20.28439732810163 usec\nrounds: 31961"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 270.549340182835,
            "unit": "iter/sec",
            "range": "stddev: 0.0004535338108059398",
            "extra": "mean: 3.69618347368435 msec\nrounds: 57"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 184.54564664050585,
            "unit": "iter/sec",
            "range": "stddev: 0.00009559032937254939",
            "extra": "mean: 5.418713571434149 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 185.15708923020557,
            "unit": "iter/sec",
            "range": "stddev: 0.0006570530541665629",
            "extra": "mean: 5.400819402365422 msec\nrounds: 169"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "157276367+stormsia@users.noreply.github.com",
            "name": "stormsia",
            "username": "stormsia"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "2b3c80f8b548a6453f3c83c49aa82a13e70910c6",
          "message": "Merge pull request #22 from stormsia/dependabot/pip/dev-dependencies-6fc60bd542\n\ndeps: update mypy requirement from >=2.4.0 to >=2.4.1 in the dev-dependencies group",
          "timestamp": "2026-11-01T03:07:17+03:00",
          "tree_id": "8d1245f30ac0b427aff21a928e7d8940b1d307eb",
          "url": "https://github.com/stormsia/mailtmapi/commit/2b3c80f8b548a6453f3c83c49aa82a13e70910c6"
        },
        "date": 1793491674393,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 62277.748021812855,
            "unit": "iter/sec",
            "range": "stddev: 0.000003422991411431",
            "extra": "mean: 16.05709955423804 usec\nrounds: 673"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 56108.191263887,
            "unit": "iter/sec",
            "range": "stddev: 0.000004755081188456081",
            "extra": "mean: 17.822709616441184 usec\nrounds: 14288"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 72261.60729797094,
            "unit": "iter/sec",
            "range": "stddev: 0.00000304439393143624",
            "extra": "mean: 13.838607213322797 usec\nrounds: 19769"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 48271.80027688127,
            "unit": "iter/sec",
            "range": "stddev: 0.000005848046561688943",
            "extra": "mean: 20.71602870131463 usec\nrounds: 32333"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 262.1245487695711,
            "unit": "iter/sec",
            "range": "stddev: 0.0005193108667221925",
            "extra": "mean: 3.814980339285512 msec\nrounds: 56"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 177.321573839411,
            "unit": "iter/sec",
            "range": "stddev: 0.00024344959840622992",
            "extra": "mean: 5.639471714285804 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 191.74769185212708,
            "unit": "iter/sec",
            "range": "stddev: 0.00037603709273814596",
            "extra": "mean: 5.215186635838021 msec\nrounds: 173"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "157276367+stormsia@users.noreply.github.com",
            "name": "stormsia",
            "username": "stormsia"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "5e329872b771b25f8c3cdfd1b0a23ec645f4d322",
          "message": "Merge pull request #23 from stormsia/dependabot/pip/fastapi-stack-f24027b879\n\ndeps: bump the fastapi-stack group with 2 updates",
          "timestamp": "2026-11-01T03:09:12+03:00",
          "tree_id": "e16bce3a154de2ef0cba7f690a9ab6e5f94a967f",
          "url": "https://github.com/stormsia/mailtmapi/commit/5e329872b771b25f8c3cdfd1b0a23ec645f4d322"
        },
        "date": 1793491789858,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 69634.1489750425,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024775634740276875",
            "extra": "mean: 14.360770034805897 usec\nrounds: 574"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 65992.29742340013,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018673495607049276",
            "extra": "mean: 15.153283626179853 usec\nrounds: 14230"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 69074.64031533671,
            "unit": "iter/sec",
            "range": "stddev: 0.000002133091402300602",
            "extra": "mean: 14.477093118905014 usec\nrounds: 27481"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 45662.168712768194,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028565328879859096",
            "extra": "mean: 21.89996726371818 usec\nrounds: 30150"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 297.8825919211316,
            "unit": "iter/sec",
            "range": "stddev: 0.0004070505101143504",
            "extra": "mean: 3.357027322579372 msec\nrounds: 62"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 209.85917072426014,
            "unit": "iter/sec",
            "range": "stddev: 0.00012039218699404767",
            "extra": "mean: 4.765100312503989 msec\nrounds: 16"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 193.33772693319958,
            "unit": "iter/sec",
            "range": "stddev: 0.000769894069612913",
            "extra": "mean: 5.17229624999942 msec\nrounds: 180"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "sf_root@outlook.com",
            "name": "stormsia",
            "username": "stormsia"
          },
          "committer": {
            "email": "sf_root@outlook.com",
            "name": "stormsia",
            "username": "stormsia"
          },
          "distinct": true,
          "id": "e2601d046a02cf8db36b06e66f7cc8fa79786be5",
          "message": "ci(workflows): add cache-suffix to prevent UV cache collisions and enable direct merge fallback for Dependabot",
          "timestamp": "2026-11-01T03:12:45+03:00",
          "tree_id": "449e788b7aa60ff7c796e9cce03bcc68ee398172",
          "url": "https://github.com/stormsia/mailtmapi/commit/e2601d046a02cf8db36b06e66f7cc8fa79786be5"
        },
        "date": 1793492006007,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 89485.43841743613,
            "unit": "iter/sec",
            "range": "stddev: 0.00000148592159868097",
            "extra": "mean: 11.175002522032134 usec\nrounds: 793"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 85623.78703888335,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018813467560301665",
            "extra": "mean: 11.67899756110859 usec\nrounds: 20091"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 102833.60766719443,
            "unit": "iter/sec",
            "range": "stddev: 0.0000034733473173219965",
            "extra": "mean: 9.72444731528189 usec\nrounds: 31698"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 71417.9140435688,
            "unit": "iter/sec",
            "range": "stddev: 0.000002029535281574236",
            "extra": "mean: 14.002089159170147 usec\nrounds: 46703"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 379.38961190925346,
            "unit": "iter/sec",
            "range": "stddev: 0.0010696159969701136",
            "extra": "mean: 2.635812812500493 msec\nrounds: 80"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 268.53305150831295,
            "unit": "iter/sec",
            "range": "stddev: 0.00012531763652655714",
            "extra": "mean: 3.7239363809525066 msec\nrounds: 21"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 260.83796549458077,
            "unit": "iter/sec",
            "range": "stddev: 0.00021883181127745608",
            "extra": "mean: 3.83379772995805 msec\nrounds: 237"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "sf_root@outlook.com",
            "name": "stormsia",
            "username": "stormsia"
          },
          "committer": {
            "email": "sf_root@outlook.com",
            "name": "stormsia",
            "username": "stormsia"
          },
          "distinct": true,
          "id": "23abdb2ac107e5f790c200a134786f7f28183e15",
          "message": "fix(mutation-test): fix mutmut export CLI command and eliminate surviving mutants in crypto module",
          "timestamp": "2026-11-01T03:28:06+03:00",
          "tree_id": "3c6f8e336d54e6d9441b46a51bfbb59808cc375f",
          "url": "https://github.com/stormsia/mailtmapi/commit/23abdb2ac107e5f790c200a134786f7f28183e15"
        },
        "date": 1793492914694,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 62502.26858480179,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032942133227203206",
            "extra": "mean: 15.999419263369946 usec\nrounds: 706"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 58509.9108074285,
            "unit": "iter/sec",
            "range": "stddev: 0.0000042172289448963345",
            "extra": "mean: 17.09112159290864 usec\nrounds: 16950"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73902.94091081942,
            "unit": "iter/sec",
            "range": "stddev: 0.000003192833083057095",
            "extra": "mean: 13.531261241778262 usec\nrounds: 25463"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49282.89159249089,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032229217728786517",
            "extra": "mean: 20.291017180338653 usec\nrounds: 32188"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 269.9085124967992,
            "unit": "iter/sec",
            "range": "stddev: 0.0004133871262199899",
            "extra": "mean: 3.7049591016950933 msec\nrounds: 59"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 179.76755233686973,
            "unit": "iter/sec",
            "range": "stddev: 0.0006274388861711946",
            "extra": "mean: 5.562739142857558 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 190.02492956266673,
            "unit": "iter/sec",
            "range": "stddev: 0.0005824731206855748",
            "extra": "mean: 5.262467415730411 msec\nrounds: 178"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "sf_root@outlook.com",
            "name": "stormsia",
            "username": "stormsia"
          },
          "committer": {
            "email": "sf_root@outlook.com",
            "name": "stormsia",
            "username": "stormsia"
          },
          "distinct": true,
          "id": "d621d3ce336858e5045a2ecc737c534b39b29b52",
          "message": "feat(ci): add Semantic PR Title Gate, OpenAPI Breaking Changes Gate, .trivyignore, typos spellchecker, pre-commit config, and concurrency cancellation",
          "timestamp": "2026-11-01T03:42:22+03:00",
          "tree_id": "1a5a2e91c56fdf8cedbf1e9ac631255ae6d12b37",
          "url": "https://github.com/stormsia/mailtmapi/commit/d621d3ce336858e5045a2ecc737c534b39b29b52"
        },
        "date": 1793493781940,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 60040.441404428326,
            "unit": "iter/sec",
            "range": "stddev: 0.0000046252175594226805",
            "extra": "mean: 16.655440509906782 usec\nrounds: 706"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 55791.46289980736,
            "unit": "iter/sec",
            "range": "stddev: 0.000004859150221530195",
            "extra": "mean: 17.92388921215136 usec\nrounds: 16157"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73961.58835377585,
            "unit": "iter/sec",
            "range": "stddev: 0.000002539688015122271",
            "extra": "mean: 13.520531701087359 usec\nrounds: 24873"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49607.71015600005,
            "unit": "iter/sec",
            "range": "stddev: 0.000003488542049994232",
            "extra": "mean: 20.15815680375745 usec\nrounds: 35892"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 256.8746931232673,
            "unit": "iter/sec",
            "range": "stddev: 0.00039311818019831517",
            "extra": "mean: 3.8929486896559586 msec\nrounds: 58"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 175.29709131910042,
            "unit": "iter/sec",
            "range": "stddev: 0.00029917123274664453",
            "extra": "mean: 5.70460121428746 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 182.79697067576802,
            "unit": "iter/sec",
            "range": "stddev: 0.000796537439745175",
            "extra": "mean: 5.470550175438778 msec\nrounds: 171"
          }
        ]
      }
    ]
  }
}