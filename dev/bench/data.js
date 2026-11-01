window.BENCHMARK_DATA = {
  "lastUpdate": 1793495225679,
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
          "id": "87a4fcd7fdf61be7a1a62c8ae55e5293a846b6bc",
          "message": "fix(ci): add GHSA-6v7p-g79w-8964 to .trivyignore and resolve ruff unused variable in openapi script",
          "timestamp": "2026-11-01T03:45:13+03:00",
          "tree_id": "3129bfe866906b92c786813d8a0f6a56c4ed961d",
          "url": "https://github.com/stormsia/mailtmapi/commit/87a4fcd7fdf61be7a1a62c8ae55e5293a846b6bc"
        },
        "date": 1793493938531,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 117577.35321736822,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018402269466840988",
            "extra": "mean: 8.50503921576866 usec\nrounds: 765"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 119283.41095739737,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010118125002867107",
            "extra": "mean: 8.38339541075963 usec\nrounds: 18783"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 142077.95787673094,
            "unit": "iter/sec",
            "range": "stddev: 0.00000138801135767902",
            "extra": "mean: 7.038389451427896 usec\nrounds: 22714"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 96349.25089112463,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015212604080680889",
            "extra": "mean: 10.378907887203061 usec\nrounds: 52414"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 562.7843967409838,
            "unit": "iter/sec",
            "range": "stddev: 0.00025214732900868497",
            "extra": "mean: 1.776879397849121 msec\nrounds: 93"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 359.74326408038064,
            "unit": "iter/sec",
            "range": "stddev: 0.0005534285216340733",
            "extra": "mean: 2.7797601785715744 msec\nrounds: 28"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 344.4419843951697,
            "unit": "iter/sec",
            "range": "stddev: 0.00025788674839246066",
            "extra": "mean: 2.903246541666433 msec\nrounds: 216"
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
          "id": "414961d4ba966d09ba8852f98e4402ebad3d1fa8",
          "message": "style: apply ruff format to check_openapi_breaking.py",
          "timestamp": "2026-11-01T03:46:11+03:00",
          "tree_id": "0a04aca5cb839d293ecbd3265cd3de554c059543",
          "url": "https://github.com/stormsia/mailtmapi/commit/414961d4ba966d09ba8852f98e4402ebad3d1fa8"
        },
        "date": 1793494000685,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 63023.51592353277,
            "unit": "iter/sec",
            "range": "stddev: 0.000003845240396642886",
            "extra": "mean: 15.867093184920256 usec\nrounds: 719"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 55816.80693256714,
            "unit": "iter/sec",
            "range": "stddev: 0.000005709179225416508",
            "extra": "mean: 17.915750738090594 usec\nrounds: 16597"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 74000.1820959458,
            "unit": "iter/sec",
            "range": "stddev: 0.000002586640545734221",
            "extra": "mean: 13.513480260135553 usec\nrounds: 28445"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 48919.02164883047,
            "unit": "iter/sec",
            "range": "stddev: 0.0000031589003862522514",
            "extra": "mean: 20.441946022113616 usec\nrounds: 33347"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 265.8671497515989,
            "unit": "iter/sec",
            "range": "stddev: 0.0006343769660372077",
            "extra": "mean: 3.7612770172407735 msec\nrounds: 58"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 121.66929879762085,
            "unit": "iter/sec",
            "range": "stddev: 0.002384999745594168",
            "extra": "mean: 8.21900027272578 msec\nrounds: 11"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 120.62546592874607,
            "unit": "iter/sec",
            "range": "stddev: 0.0008462610076987243",
            "extra": "mean: 8.290123418803653 msec\nrounds: 117"
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
          "id": "e24e55283f92eb7c60936a915268ee9372b13b70",
          "message": "ci(dependabot): add --delete-branch flag to auto-merge step",
          "timestamp": "2026-11-01T03:51:37+03:00",
          "tree_id": "4d4f8c6deaa9c69a04eb354346011e8df00d18e6",
          "url": "https://github.com/stormsia/mailtmapi/commit/e24e55283f92eb7c60936a915268ee9372b13b70"
        },
        "date": 1793494327794,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 60422.02207640207,
            "unit": "iter/sec",
            "range": "stddev: 0.0000048394509818649265",
            "extra": "mean: 16.55025710221227 usec\nrounds: 704"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 58616.50238175219,
            "unit": "iter/sec",
            "range": "stddev: 0.000003847210861443177",
            "extra": "mean: 17.060042127510297 usec\nrounds: 17542"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73253.6124208015,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026122153533074885",
            "extra": "mean: 13.651203905898225 usec\nrounds: 32054"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 48957.30901718911,
            "unit": "iter/sec",
            "range": "stddev: 0.0000031886986144050837",
            "extra": "mean: 20.425959270941465 usec\nrounds: 34840"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 267.6114635866201,
            "unit": "iter/sec",
            "range": "stddev: 0.0007328113188763192",
            "extra": "mean: 3.7367607000001377 msec\nrounds: 60"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 186.11744978895965,
            "unit": "iter/sec",
            "range": "stddev: 0.0005684934500448945",
            "extra": "mean: 5.37295133333231 msec\nrounds: 15"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 191.23205039851302,
            "unit": "iter/sec",
            "range": "stddev: 0.0004463141564701881",
            "extra": "mean: 5.22924895652207 msec\nrounds: 184"
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
          "id": "cddfd906c3d54f685bd1e29802cf25186cbbb842",
          "message": "feat(ci): implement executive Step Summary dashboard for pipeline results",
          "timestamp": "2026-11-01T03:58:30+03:00",
          "tree_id": "f6223e211f028d39c7c0384c0263fb42c6e0e6fd",
          "url": "https://github.com/stormsia/mailtmapi/commit/cddfd906c3d54f685bd1e29802cf25186cbbb842"
        },
        "date": 1793494737193,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 61387.59874501444,
            "unit": "iter/sec",
            "range": "stddev: 0.000004057902985670632",
            "extra": "mean: 16.289935108126617 usec\nrounds: 601"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59056.55165319657,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032553651718844656",
            "extra": "mean: 16.93292229238841 usec\nrounds: 17257"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73907.96212855859,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023186301174013064",
            "extra": "mean: 13.5303419442219 usec\nrounds: 25162"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49042.91032477519,
            "unit": "iter/sec",
            "range": "stddev: 0.000003352395374033606",
            "extra": "mean: 20.390307046986692 usec\nrounds: 42912"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 276.03177857986293,
            "unit": "iter/sec",
            "range": "stddev: 0.00019411920913876157",
            "extra": "mean: 3.6227712807012 msec\nrounds: 57"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 178.36812810713192,
            "unit": "iter/sec",
            "range": "stddev: 0.0005882523774225463",
            "extra": "mean: 5.606382769232054 msec\nrounds: 13"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 189.0288069374861,
            "unit": "iter/sec",
            "range": "stddev: 0.0006639945757121719",
            "extra": "mean: 5.290198971264263 msec\nrounds: 174"
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
          "id": "0a9daafa981a6af7f18c57e8639026bdd9fa6879",
          "message": "style(ci): translate dashboard to English, expand quality gates, and fix benchmark links",
          "timestamp": "2026-11-01T04:03:32+03:00",
          "tree_id": "1f8fbe9a0dd9c8558e5d9bc83259eca5b3311392",
          "url": "https://github.com/stormsia/mailtmapi/commit/0a9daafa981a6af7f18c57e8639026bdd9fa6879"
        },
        "date": 1793495039891,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 55719.20988177347,
            "unit": "iter/sec",
            "range": "stddev: 0.000007632682305111415",
            "extra": "mean: 17.94713173646624 usec\nrounds: 501"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59783.08261686575,
            "unit": "iter/sec",
            "range": "stddev: 0.000003442777353175944",
            "extra": "mean: 16.727140124385024 usec\nrounds: 16728"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73892.43653198406,
            "unit": "iter/sec",
            "range": "stddev: 0.000002367843151981577",
            "extra": "mean: 13.533184814756432 usec\nrounds: 15897"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49010.922625814135,
            "unit": "iter/sec",
            "range": "stddev: 0.0000035587601836296413",
            "extra": "mean: 20.4036150805555 usec\nrounds: 32386"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 271.90825522925655,
            "unit": "iter/sec",
            "range": "stddev: 0.0003175002046056462",
            "extra": "mean: 3.677711068966481 msec\nrounds: 58"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 185.11630592175982,
            "unit": "iter/sec",
            "range": "stddev: 0.0001455587126355473",
            "extra": "mean: 5.402009266664247 msec\nrounds: 15"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 190.13947912133608,
            "unit": "iter/sec",
            "range": "stddev: 0.00042741143020195944",
            "extra": "mean: 5.259297041420091 msec\nrounds: 169"
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
          "id": "8b09a54c57809686f2c61ec541d77530d6e7ea47",
          "message": "ci(pre-commit): add uv lock consistency check hook",
          "timestamp": "2026-11-01T04:06:36+03:00",
          "tree_id": "8f6b1342e8a975ed791f3aae7f8991d5b04eb8e5",
          "url": "https://github.com/stormsia/mailtmapi/commit/8b09a54c57809686f2c61ec541d77530d6e7ea47"
        },
        "date": 1793495224586,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 62566.94933239733,
            "unit": "iter/sec",
            "range": "stddev: 0.000003443669663221524",
            "extra": "mean: 15.982879310406101 usec\nrounds: 754"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59419.950376288514,
            "unit": "iter/sec",
            "range": "stddev: 0.0000035158080098141846",
            "extra": "mean: 16.829364441863436 usec\nrounds: 17380"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73451.34197308774,
            "unit": "iter/sec",
            "range": "stddev: 0.000002612757965809852",
            "extra": "mean: 13.614455136386695 usec\nrounds: 25845"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 47382.18605953655,
            "unit": "iter/sec",
            "range": "stddev: 0.0000045332187000238056",
            "extra": "mean: 21.104978118643206 usec\nrounds: 33316"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 268.63398167867905,
            "unit": "iter/sec",
            "range": "stddev: 0.0003446499986305414",
            "extra": "mean: 3.7225372372886514 msec\nrounds: 59"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 185.43515635461412,
            "unit": "iter/sec",
            "range": "stddev: 0.00010989243637346062",
            "extra": "mean: 5.392720666666169 msec\nrounds: 15"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 188.48409562949172,
            "unit": "iter/sec",
            "range": "stddev: 0.00040175307873606723",
            "extra": "mean: 5.305487429378269 msec\nrounds: 177"
          }
        ]
      }
    ]
  }
}