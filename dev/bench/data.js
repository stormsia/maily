window.BENCHMARK_DATA = {
  "lastUpdate": 1793641659566,
  "repoUrl": "https://github.com/stormsia/maily",
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
          "id": "fe84f7112bd1c4b0fe7e01c9b26434e1f0b6b871",
          "message": "feat(ci): add PR performance regression gate, zizmor audit, semver check, and clean commit lint",
          "timestamp": "2026-11-01T04:24:37+03:00",
          "tree_id": "05c3d6c2d27d506f3aa95ef89f243623da7573a3",
          "url": "https://github.com/stormsia/mailtmapi/commit/fe84f7112bd1c4b0fe7e01c9b26434e1f0b6b871"
        },
        "date": 1793496306433,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 62088.08901628811,
            "unit": "iter/sec",
            "range": "stddev: 0.000003914936422926325",
            "extra": "mean: 16.106148793493407 usec\nrounds: 746"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59576.77423541466,
            "unit": "iter/sec",
            "range": "stddev: 0.000003362392742400289",
            "extra": "mean: 16.785064529485094 usec\nrounds: 16938"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 72988.87442622708,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025711819994100356",
            "extra": "mean: 13.700718196589564 usec\nrounds: 26483"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 48647.280732300336,
            "unit": "iter/sec",
            "range": "stddev: 0.000003186698762505049",
            "extra": "mean: 20.55613355868481 usec\nrounds: 36980"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 257.54047609139644,
            "unit": "iter/sec",
            "range": "stddev: 0.0005948986890298578",
            "extra": "mean: 3.8828847999998186 msec\nrounds: 55"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 181.09339899813926,
            "unit": "iter/sec",
            "range": "stddev: 0.00015016352275996054",
            "extra": "mean: 5.522012428571595 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 189.36959801064233,
            "unit": "iter/sec",
            "range": "stddev: 0.0004403397963191514",
            "extra": "mean: 5.280678686046539 msec\nrounds: 172"
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
          "id": "487b59aa30681f5bf26cbeb55956f5363b955dbd",
          "message": "feat(test-sender): add autonomous test email dispatcher with primary and fallback providers",
          "timestamp": "2026-11-01T04:29:18+03:00",
          "tree_id": "c3971cff89d9c3b31ac8e255a935f293273ee2a2",
          "url": "https://github.com/stormsia/mailtmapi/commit/487b59aa30681f5bf26cbeb55956f5363b955dbd"
        },
        "date": 1793496588332,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 98736.85573015954,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017320985799555558",
            "extra": "mean: 10.127930372149233 usec\nrounds: 833"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 94211.30801817818,
            "unit": "iter/sec",
            "range": "stddev: 0.000004100267207548413",
            "extra": "mean: 10.614437067438324 usec\nrounds: 23406"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 103150.57563969074,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019447440608938086",
            "extra": "mean: 9.694565384618326 usec\nrounds: 40560"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 67106.22801421248,
            "unit": "iter/sec",
            "range": "stddev: 0.000003057208386794211",
            "extra": "mean: 14.901746523261735 usec\nrounds: 34587"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 339.9884183207002,
            "unit": "iter/sec",
            "range": "stddev: 0.00035678939176486994",
            "extra": "mean: 2.9412766615383115 msec\nrounds: 65"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 222.50768722338412,
            "unit": "iter/sec",
            "range": "stddev: 0.0008082466355594212",
            "extra": "mean: 4.494226750000152 msec\nrounds: 20"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 239.13543818694555,
            "unit": "iter/sec",
            "range": "stddev: 0.00039690845489279137",
            "extra": "mean: 4.181730686098662 msec\nrounds: 223"
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
          "id": "177bb4896caf25d0575577b2a1ef712a60e17788",
          "message": "fix(ci): grant issues:write and map env in pr-benchmark workflow",
          "timestamp": "2026-11-01T04:33:41+03:00",
          "tree_id": "374602800c96bb4b7f22766689d9d7a4f13698db",
          "url": "https://github.com/stormsia/mailtmapi/commit/177bb4896caf25d0575577b2a1ef712a60e17788"
        },
        "date": 1793496851522,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 63502.43811320765,
            "unit": "iter/sec",
            "range": "stddev: 0.000004232750189768899",
            "extra": "mean: 15.74742686599325 usec\nrounds: 670"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 58969.84081729016,
            "unit": "iter/sec",
            "range": "stddev: 0.000004094409885548951",
            "extra": "mean: 16.957820915582268 usec\nrounds: 15596"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73819.55468730441,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023530766168175154",
            "extra": "mean: 13.54654609115356 usec\nrounds: 23703"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 47914.72808981526,
            "unit": "iter/sec",
            "range": "stddev: 0.000004623022639191489",
            "extra": "mean: 20.870409576894996 usec\nrounds: 35356"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 271.6920413057553,
            "unit": "iter/sec",
            "range": "stddev: 0.00039967422786941413",
            "extra": "mean: 3.6806378103458153 msec\nrounds: 58"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 184.95470373432443,
            "unit": "iter/sec",
            "range": "stddev: 0.00016337856882500226",
            "extra": "mean: 5.406729214286088 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 188.66850605517917,
            "unit": "iter/sec",
            "range": "stddev: 0.000466009178524528",
            "extra": "mean: 5.30030168208113 msec\nrounds: 173"
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
          "id": "f7cafcd8e67f15622d82a24e651481a3381e70a1",
          "message": "fix(ci): allow credential persistence for git fetch in commit-lint and pr-benchmark",
          "timestamp": "2026-11-01T04:40:46+03:00",
          "tree_id": "1de393ee12ba288d0bed888d900129ed82a004c5",
          "url": "https://github.com/stormsia/mailtmapi/commit/f7cafcd8e67f15622d82a24e651481a3381e70a1"
        },
        "date": 1793497282961,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 89600.49683516531,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015591696593614662",
            "extra": "mean: 11.160652399502457 usec\nrounds: 771"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 85828.02721383113,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013996020562574798",
            "extra": "mean: 11.651205701240336 usec\nrounds: 19645"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 103409.63104912465,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016142485706747006",
            "extra": "mean: 9.67027915924921 usec\nrounds: 27024"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 68797.81886082608,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023413351459366476",
            "extra": "mean: 14.5353445292058 usec\nrounds: 46922"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 398.797147035535,
            "unit": "iter/sec",
            "range": "stddev: 0.000261240963317285",
            "extra": "mean: 2.5075405063288847 msec\nrounds: 79"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 270.95759238852236,
            "unit": "iter/sec",
            "range": "stddev: 0.00008535764241200145",
            "extra": "mean: 3.6906144285712204 msec\nrounds: 21"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 257.65056499522495,
            "unit": "iter/sec",
            "range": "stddev: 0.0002670253518590802",
            "extra": "mean: 3.881225721428296 msec\nrounds: 140"
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
          "id": "d776d91e5655323ab60be6a6158857a8a5f97065",
          "message": "fix(ci): checkout PR head ref in commit-lint workflow",
          "timestamp": "2026-11-01T04:42:55+03:00",
          "tree_id": "1af272397ab3940bd8caf24d49f8051ac8468eda",
          "url": "https://github.com/stormsia/mailtmapi/commit/d776d91e5655323ab60be6a6158857a8a5f97065"
        },
        "date": 1793497409386,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 59647.97413982264,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036571145135854676",
            "extra": "mean: 16.765028727645795 usec\nrounds: 731"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 57753.98618297915,
            "unit": "iter/sec",
            "range": "stddev: 0.0000041276573762416245",
            "extra": "mean: 17.31482216364683 usec\nrounds: 15548"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 71290.85048556118,
            "unit": "iter/sec",
            "range": "stddev: 0.000007978968179428316",
            "extra": "mean: 14.027045450980191 usec\nrounds: 25522"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 48686.949233270665,
            "unit": "iter/sec",
            "range": "stddev: 0.000004140702670304225",
            "extra": "mean: 20.539385107264863 usec\nrounds: 32996"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 253.27243877993493,
            "unit": "iter/sec",
            "range": "stddev: 0.00046102494215084593",
            "extra": "mean: 3.9483174909090155 msec\nrounds: 55"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 169.43306107701832,
            "unit": "iter/sec",
            "range": "stddev: 0.00016009775743216852",
            "extra": "mean: 5.902035846153042 msec\nrounds: 13"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 187.83172738455642,
            "unit": "iter/sec",
            "range": "stddev: 0.0005218029905140201",
            "extra": "mean: 5.3239141966290635 msec\nrounds: 178"
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
          "id": "d3b22d5023de48eca70046c6e5c0df67c2304300",
          "message": "perf(ci): ignore sub-millisecond jitter in PR benchmark comparisons",
          "timestamp": "2026-11-01T04:45:07+03:00",
          "tree_id": "1b3e390f1fb3253f111d5c63c9391efbf4c774c1",
          "url": "https://github.com/stormsia/mailtmapi/commit/d3b22d5023de48eca70046c6e5c0df67c2304300"
        },
        "date": 1793497544253,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 62469.69161133457,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036261197845255247",
            "extra": "mean: 16.00776271190298 usec\nrounds: 708"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59225.44746609396,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036213781728889066",
            "extra": "mean: 16.884633933285034 usec\nrounds: 17057"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 72967.13433453659,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025519911518619548",
            "extra": "mean: 13.704800238080379 usec\nrounds: 27718"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 48547.616528362596,
            "unit": "iter/sec",
            "range": "stddev: 0.000004077246778577108",
            "extra": "mean: 20.598333584837842 usec\nrounds: 37106"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 268.236264047112,
            "unit": "iter/sec",
            "range": "stddev: 0.0003426699657414151",
            "extra": "mean: 3.728056694915657 msec\nrounds: 59"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 184.06783434717815,
            "unit": "iter/sec",
            "range": "stddev: 0.00012686707652808372",
            "extra": "mean: 5.43277973333384 msec\nrounds: 15"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 185.49768750256322,
            "unit": "iter/sec",
            "range": "stddev: 0.0008085732944764109",
            "extra": "mean: 5.390902784090945 msec\nrounds: 176"
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
          "id": "b14b506d94b03ded050cc87f470befe7f84b76fe",
          "message": "feat(ci): add PR diff coverage gate, PR size labeler, lychee link checker, and smart path filtering",
          "timestamp": "2026-11-01T05:02:56+03:00",
          "tree_id": "efa342f68cbf17396b3d198e284e7529e1bba8d1",
          "url": "https://github.com/stormsia/mailtmapi/commit/b14b506d94b03ded050cc87f470befe7f84b76fe"
        },
        "date": 1793498615105,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 80762.17865856763,
            "unit": "iter/sec",
            "range": "stddev: 0.000002702036412002755",
            "extra": "mean: 12.382033479156462 usec\nrounds: 687"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 80777.4080986441,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020988299121430886",
            "extra": "mean: 12.37969902152364 usec\nrounds: 20440"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 85547.25620700659,
            "unit": "iter/sec",
            "range": "stddev: 0.0000031381185787496605",
            "extra": "mean: 11.689445627340843 usec\nrounds: 28461"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 59743.023675409575,
            "unit": "iter/sec",
            "range": "stddev: 0.000002585181354047111",
            "extra": "mean: 16.738356020162456 usec\nrounds: 37981"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 303.66138844166,
            "unit": "iter/sec",
            "range": "stddev: 0.0003118973880793907",
            "extra": "mean: 3.293141762710875 msec\nrounds: 59"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 213.1381527802507,
            "unit": "iter/sec",
            "range": "stddev: 0.00010774932036924472",
            "extra": "mean: 4.691792562502961 msec\nrounds: 16"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 211.38263526255741,
            "unit": "iter/sec",
            "range": "stddev: 0.00039080121662024304",
            "extra": "mean: 4.7307575608464925 msec\nrounds: 189"
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
          "id": "e3c00600717aceda0ffb2d7022ea8344e15e0026",
          "message": "fix(ci): use native git diff for change detection without external actions",
          "timestamp": "2026-11-01T05:05:58+03:00",
          "tree_id": "0c34f1923f908323cc72dca2d4a2b5a20c779c5e",
          "url": "https://github.com/stormsia/mailtmapi/commit/e3c00600717aceda0ffb2d7022ea8344e15e0026"
        },
        "date": 1793498792965,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 128165.83207955242,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015501091883426935",
            "extra": "mean: 7.80239150930102 usec\nrounds: 848"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 128974.05929606908,
            "unit": "iter/sec",
            "range": "stddev: 7.012267769296996e-7",
            "extra": "mean: 7.753497140881867 usec\nrounds: 25882"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 149974.47363592422,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012420863998959546",
            "extra": "mean: 6.667801364834824 usec\nrounds: 30040"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 100740.70561036358,
            "unit": "iter/sec",
            "range": "stddev: 0.00000159116765230226",
            "extra": "mean: 9.926474049801833 usec\nrounds: 52832"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 582.7966662491247,
            "unit": "iter/sec",
            "range": "stddev: 0.00025466607174036",
            "extra": "mean: 1.7158643106797318 msec\nrounds: 103"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 379.1429687603189,
            "unit": "iter/sec",
            "range": "stddev: 0.0005496921524715954",
            "extra": "mean: 2.63752748275853 msec\nrounds: 29"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 361.83658393066247,
            "unit": "iter/sec",
            "range": "stddev: 0.00018017587102755288",
            "extra": "mean: 2.7636785344834744 msec\nrounds: 290"
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
          "id": "54f2972a0327d7bf35a37f951ac19ceeb79d7ef8",
          "message": "fix(ci): pass --yes to npx biome and htmlhint to prevent non-interactive prompts",
          "timestamp": "2026-11-01T05:10:12+03:00",
          "tree_id": "44be040ed538f087cda1c9b155835127b6e17952",
          "url": "https://github.com/stormsia/mailtmapi/commit/54f2972a0327d7bf35a37f951ac19ceeb79d7ef8"
        },
        "date": 1793499052814,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 60264.55623613708,
            "unit": "iter/sec",
            "range": "stddev: 0.0000034692478901748806",
            "extra": "mean: 16.593501428628446 usec\nrounds: 700"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 57353.86130122924,
            "unit": "iter/sec",
            "range": "stddev: 0.0000030720065837861336",
            "extra": "mean: 17.435617712779305 usec\nrounds: 17016"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 70505.28055737667,
            "unit": "iter/sec",
            "range": "stddev: 0.000005500211199427348",
            "extra": "mean: 14.18333480974106 usec\nrounds: 30931"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 48078.29226922716,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037284033612926355",
            "extra": "mean: 20.799407649511227 usec\nrounds: 34878"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 268.9895326142632,
            "unit": "iter/sec",
            "range": "stddev: 0.000348607593956538",
            "extra": "mean: 3.717616779661168 msec\nrounds: 59"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 186.2654657546767,
            "unit": "iter/sec",
            "range": "stddev: 0.00010448126112247162",
            "extra": "mean: 5.368681714285474 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 189.0720575517683,
            "unit": "iter/sec",
            "range": "stddev: 0.0005047331068836719",
            "extra": "mean: 5.288988827586002 msec\nrounds: 174"
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
          "id": "362a2966dc3b69e6c40693f0515a9df221c9372a",
          "message": "fix(ci): check existing static JS files with node --check",
          "timestamp": "2026-11-01T05:13:47+03:00",
          "tree_id": "de6e1b465cd88a474cb3a2e201269ffd13c5b4c2",
          "url": "https://github.com/stormsia/mailtmapi/commit/362a2966dc3b69e6c40693f0515a9df221c9372a"
        },
        "date": 1793499258447,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 120144.08091841203,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016474379713412606",
            "extra": "mean: 8.323339713082365 usec\nrounds: 836"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 114644.44098073925,
            "unit": "iter/sec",
            "range": "stddev: 0.000005714519503538985",
            "extra": "mean: 8.72262092645211 usec\nrounds: 23444"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 144172.41125581056,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013014922246613507",
            "extra": "mean: 6.936139801571759 usec\nrounds: 29735"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 98991.55847745188,
            "unit": "iter/sec",
            "range": "stddev: 0.000001546007959645035",
            "extra": "mean: 10.101871466421839 usec\nrounds: 41919"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 558.3052910454296,
            "unit": "iter/sec",
            "range": "stddev: 0.00015690616863922404",
            "extra": "mean: 1.7911347358494394 msec\nrounds: 106"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 355.5623094161083,
            "unit": "iter/sec",
            "range": "stddev: 0.0006586111973743131",
            "extra": "mean: 2.812446576922521 msec\nrounds: 26"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 339.58527810777736,
            "unit": "iter/sec",
            "range": "stddev: 0.00015248284755364828",
            "extra": "mean: 2.9447684115523427 msec\nrounds: 277"
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
          "id": "54304bd775dbe39e446a2645ce7b7abbbf833afe",
          "message": "feat(ci): publish executive test & quality dashboard and openapi changes to PR",
          "timestamp": "2026-11-01T05:23:15+03:00",
          "tree_id": "28ae6a353ffc27223ef9502c85ff50c668e9386f",
          "url": "https://github.com/stormsia/mailtmapi/commit/54304bd775dbe39e446a2645ce7b7abbbf833afe"
        },
        "date": 1793499836676,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 63291.96957895688,
            "unit": "iter/sec",
            "range": "stddev: 0.0000035191646649462237",
            "extra": "mean: 15.799792717028621 usec\nrounds: 714"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59567.733107390835,
            "unit": "iter/sec",
            "range": "stddev: 0.000003263610680421688",
            "extra": "mean: 16.787612148966023 usec\nrounds: 17022"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73778.85740540242,
            "unit": "iter/sec",
            "range": "stddev: 0.00000243444477814342",
            "extra": "mean: 13.554018524645457 usec\nrounds: 27153"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49581.73527207273,
            "unit": "iter/sec",
            "range": "stddev: 0.000007562175196509221",
            "extra": "mean: 20.168717260754228 usec\nrounds: 30636"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 268.6199635939514,
            "unit": "iter/sec",
            "range": "stddev: 0.00023065023065318058",
            "extra": "mean: 3.722731499999791 msec\nrounds: 60"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 173.03904368934616,
            "unit": "iter/sec",
            "range": "stddev: 0.0008235853032597881",
            "extra": "mean: 5.779042571428456 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 188.3099866685032,
            "unit": "iter/sec",
            "range": "stddev: 0.0005750851920051555",
            "extra": "mean: 5.310392813952976 msec\nrounds: 172"
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
          "id": "4625f2b7a4f6b6fb737e79ad8105d8b4bce5873d",
          "message": "fix(openapi): update existing sticky comment even when schema changes are resolved",
          "timestamp": "2026-11-01T05:28:41+03:00",
          "tree_id": "559fb5594e43633fa05e915276fdb2155b48c684",
          "url": "https://github.com/stormsia/mailtmapi/commit/4625f2b7a4f6b6fb737e79ad8105d8b4bce5873d"
        },
        "date": 1793500168068,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 125186.3747744107,
            "unit": "iter/sec",
            "range": "stddev: 0.000002685727043158344",
            "extra": "mean: 7.988089772565326 usec\nrounds: 880"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 101489.84540134201,
            "unit": "iter/sec",
            "range": "stddev: 0.000010260740116682867",
            "extra": "mean: 9.85320251543882 usec\nrounds: 8587"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 148017.75016732092,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012061082355714805",
            "extra": "mean: 6.755946492022671 usec\nrounds: 36574"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 98869.59162575183,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019249237542137614",
            "extra": "mean: 10.11433327028669 usec\nrounds: 52885"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 575.7848978175145,
            "unit": "iter/sec",
            "range": "stddev: 0.00020244703485294773",
            "extra": "mean: 1.7367596888880774 msec\nrounds: 135"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 375.030498273616,
            "unit": "iter/sec",
            "range": "stddev: 0.00020369645117717807",
            "extra": "mean: 2.6664498076911514 msec\nrounds: 26"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 355.9582691630311,
            "unit": "iter/sec",
            "range": "stddev: 0.0001804941519659551",
            "extra": "mean: 2.8093180763894368 msec\nrounds: 288"
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
          "id": "6539dd55dbcf20e3a3392429ab1c9fe38d484481",
          "message": "feat(health): add live provider & email delivery verification suite with automated alerting",
          "timestamp": "2026-11-01T05:45:41+03:00",
          "tree_id": "7029765d13c925a329c318d5459bdb62f20ecf88",
          "url": "https://github.com/stormsia/mailtmapi/commit/6539dd55dbcf20e3a3392429ab1c9fe38d484481"
        },
        "date": 1793501186959,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 92683.50498228364,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021676964310198882",
            "extra": "mean: 10.789406380252332 usec\nrounds: 721"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 87019.00515091156,
            "unit": "iter/sec",
            "range": "stddev: 0.000006960293240868152",
            "extra": "mean: 11.491742502293185 usec\nrounds: 22307"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 99095.60774281574,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018038994617915593",
            "extra": "mean: 10.091264615837611 usec\nrounds: 30720"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 64801.84366198997,
            "unit": "iter/sec",
            "range": "stddev: 0.000002675790011941942",
            "extra": "mean: 15.431659710425148 usec\nrounds: 34741"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 329.20445767587097,
            "unit": "iter/sec",
            "range": "stddev: 0.0004404987198885672",
            "extra": "mean: 3.037625939392907 msec\nrounds: 66"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 208.6299452309772,
            "unit": "iter/sec",
            "range": "stddev: 0.000718212999732712",
            "extra": "mean: 4.793175777776702 msec\nrounds: 18"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 230.96910901087585,
            "unit": "iter/sec",
            "range": "stddev: 0.0003610249038322042",
            "extra": "mean: 4.329583312168867 msec\nrounds: 189"
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
          "id": "9b21f9ab040ec8df31289ad850f80d8291ca22d9",
          "message": "feat(health): enable e2e email delivery testing for all 7 public providers",
          "timestamp": "2026-11-01T05:56:10+03:00",
          "tree_id": "86dcad97a2699c4caa0eebe01ebc79220a5cda5b",
          "url": "https://github.com/stormsia/mailtmapi/commit/9b21f9ab040ec8df31289ad850f80d8291ca22d9"
        },
        "date": 1793501812571,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 80433.9850007886,
            "unit": "iter/sec",
            "range": "stddev: 0.000003145544525152943",
            "extra": "mean: 12.432555716221144 usec\nrounds: 691"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 77742.7542838647,
            "unit": "iter/sec",
            "range": "stddev: 0.000002378744546871968",
            "extra": "mean: 12.86293506335866 usec\nrounds: 16493"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 86689.00879375523,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020812129680677005",
            "extra": "mean: 11.535487761535421 usec\nrounds: 25330"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 57802.69563578743,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025795556712046716",
            "extra": "mean: 17.300231226255637 usec\nrounds: 33491"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 301.9930748993787,
            "unit": "iter/sec",
            "range": "stddev: 0.0005046533911368103",
            "extra": "mean: 3.311334209677459 msec\nrounds: 62"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 206.90987201931043,
            "unit": "iter/sec",
            "range": "stddev: 0.00030517510112015763",
            "extra": "mean: 4.833022176470499 msec\nrounds: 17"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 205.1771843172843,
            "unit": "iter/sec",
            "range": "stddev: 0.00040416057275203935",
            "extra": "mean: 4.873836256830625 msec\nrounds: 183"
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
          "id": "198cdd686879338f86f64c657794f37723a868a6",
          "message": "feat(health): treat delivery failures as degradation for automated issue alerting and status tracking",
          "timestamp": "2026-11-01T06:01:25+03:00",
          "tree_id": "c2f19e074b40e9395b101075d426b76731cc09bd",
          "url": "https://github.com/stormsia/mailtmapi/commit/198cdd686879338f86f64c657794f37723a868a6"
        },
        "date": 1793502122299,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 89950.1494852222,
            "unit": "iter/sec",
            "range": "stddev: 0.00000178343813867025",
            "extra": "mean: 11.117268906421204 usec\nrounds: 833"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 86147.4638735097,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012826190308891142",
            "extra": "mean: 11.608002778448588 usec\nrounds: 21595"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 103625.84320191546,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017109867362309323",
            "extra": "mean: 9.650102417516596 usec\nrounds: 36361"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 69147.60152639875,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019994707336127548",
            "extra": "mean: 14.461817589120948 usec\nrounds: 31155"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 378.8427108975928,
            "unit": "iter/sec",
            "range": "stddev: 0.00046770809209133705",
            "extra": "mean: 2.6396178974400697 msec\nrounds: 78"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 259.38651236114475,
            "unit": "iter/sec",
            "range": "stddev: 0.00011777260529535814",
            "extra": "mean: 3.85525057142407 msec\nrounds: 21"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 259.374899657882,
            "unit": "iter/sec",
            "range": "stddev: 0.00021685220591821224",
            "extra": "mean: 3.8554231782605393 msec\nrounds: 230"
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
          "id": "dc152bfeea9050318836ed2b0e694be959a15741",
          "message": "feat(providers): centralize public provider registry and automate live health testing discovery",
          "timestamp": "2026-11-01T06:10:14+03:00",
          "tree_id": "071b86031d575508235621699b44022af22ee803",
          "url": "https://github.com/stormsia/mailtmapi/commit/dc152bfeea9050318836ed2b0e694be959a15741"
        },
        "date": 1793502658912,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 89329.79815927902,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019925226915785585",
            "extra": "mean: 11.194472847872726 usec\nrounds: 755"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 84776.7074870666,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013340697156116639",
            "extra": "mean: 11.795692822259683 usec\nrounds: 17192"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 104070.24880701394,
            "unit": "iter/sec",
            "range": "stddev: 0.000001745568432395865",
            "extra": "mean: 9.608894102428664 usec\nrounds: 29368"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 67733.33895755441,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020547082197065393",
            "extra": "mean: 14.763778301652266 usec\nrounds: 41570"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 330.89177484120626,
            "unit": "iter/sec",
            "range": "stddev: 0.0004877996754194035",
            "extra": "mean: 3.0221361666662654 msec\nrounds: 66"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 216.2420717547819,
            "unit": "iter/sec",
            "range": "stddev: 0.00026446831970856275",
            "extra": "mean: 4.624446999999141 msec\nrounds: 19"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 225.3641077891866,
            "unit": "iter/sec",
            "range": "stddev: 0.0007222039946680621",
            "extra": "mean: 4.437263811926231 msec\nrounds: 218"
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
          "id": "b9d98c194ed4093829072cd6d0808238c1f4e319",
          "message": "docs(providers): enhance guide with live test suite, factories, and issue automation details",
          "timestamp": "2026-11-01T06:12:10+03:00",
          "tree_id": "a4c7885c516f5fea4b99fcaa444012266ca4607a",
          "url": "https://github.com/stormsia/mailtmapi/commit/b9d98c194ed4093829072cd6d0808238c1f4e319"
        },
        "date": 1793502772842,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 62174.1440930666,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036113723676415043",
            "extra": "mean: 16.083856313375705 usec\nrounds: 689"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 58665.495673796315,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033912782755848243",
            "extra": "mean: 17.045794781320883 usec\nrounds: 16441"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73011.50275917613,
            "unit": "iter/sec",
            "range": "stddev: 0.000007589506659654255",
            "extra": "mean: 13.696471955911347 usec\nrounds: 21591"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49000.84229174462,
            "unit": "iter/sec",
            "range": "stddev: 0.0000030234695043488965",
            "extra": "mean: 20.407812462613 usec\nrounds: 28421"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 245.98543936150458,
            "unit": "iter/sec",
            "range": "stddev: 0.0005224597973829849",
            "extra": "mean: 4.06528127272762 msec\nrounds: 55"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 169.84273593842428,
            "unit": "iter/sec",
            "range": "stddev: 0.0003809630434083571",
            "extra": "mean: 5.887799642856351 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 177.08792564187073,
            "unit": "iter/sec",
            "range": "stddev: 0.0004062339372171949",
            "extra": "mean: 5.646912381944801 msec\nrounds: 144"
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
          "id": "1b8d3cd5e7578879a4d6e14fadcf5c13dac6e025",
          "message": "feat(health): add fault injection simulation parameters for e2e alert testing",
          "timestamp": "2026-11-01T06:30:36+03:00",
          "tree_id": "1191cad60a33e295ed2de55fbb3402174c8b4a58",
          "url": "https://github.com/stormsia/mailtmapi/commit/1b8d3cd5e7578879a4d6e14fadcf5c13dac6e025"
        },
        "date": 1793503882907,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 61713.416917843395,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037739197737897668",
            "extra": "mean: 16.203931818120846 usec\nrounds: 616"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59216.63580070801,
            "unit": "iter/sec",
            "range": "stddev: 0.0000042742150728920385",
            "extra": "mean: 16.887146432388917 usec\nrounds: 15024"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 74871.96836350765,
            "unit": "iter/sec",
            "range": "stddev: 0.000002529479350236879",
            "extra": "mean: 13.35613343494515 usec\nrounds: 26897"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 50081.39595051666,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032527925825241148",
            "extra": "mean: 19.96749453605603 usec\nrounds: 37793"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 227.96334531780496,
            "unit": "iter/sec",
            "range": "stddev: 0.0009025901449544476",
            "extra": "mean: 4.38667014035039 msec\nrounds: 57"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 156.18110774639564,
            "unit": "iter/sec",
            "range": "stddev: 0.00027603661060645197",
            "extra": "mean: 6.402823071429253 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 181.7272226792326,
            "unit": "iter/sec",
            "range": "stddev: 0.00045681241746059963",
            "extra": "mean: 5.502752891156565 msec\nrounds: 147"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "name": "github-actions[bot]",
            "username": "github-actions[bot]",
            "email": "github-actions[bot]@users.noreply.github.com"
          },
          "committer": {
            "name": "github-actions[bot]",
            "username": "github-actions[bot]",
            "email": "github-actions[bot]@users.noreply.github.com"
          },
          "id": "54d38d8e9bf6a06006e1dcb277b972485be2b285",
          "message": "chore(health): update live provider operational status [skip ci]",
          "timestamp": "2026-11-01T03:36:55Z",
          "url": "https://github.com/stormsia/mailtmapi/commit/54d38d8e9bf6a06006e1dcb277b972485be2b285"
        },
        "date": 1793523312473,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 62517.93498494458,
            "unit": "iter/sec",
            "range": "stddev: 0.000003869731661786965",
            "extra": "mean: 15.99540996101067 usec\nrounds: 522"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 60596.33907879234,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033800170858038083",
            "extra": "mean: 16.50264711040906 usec\nrounds: 18238"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 74827.46719137504,
            "unit": "iter/sec",
            "range": "stddev: 0.000002557218552474662",
            "extra": "mean: 13.364076555504003 usec\nrounds: 30553"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49922.00384490172,
            "unit": "iter/sec",
            "range": "stddev: 0.000003390788802871423",
            "extra": "mean: 20.031247205276696 usec\nrounds: 39360"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 262.16153162709304,
            "unit": "iter/sec",
            "range": "stddev: 0.0005500436387739004",
            "extra": "mean: 3.8144421639343795 msec\nrounds: 61"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 185.30689210449506,
            "unit": "iter/sec",
            "range": "stddev: 0.00011725308671587023",
            "extra": "mean: 5.396453357148191 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 192.47610419537207,
            "unit": "iter/sec",
            "range": "stddev: 0.0005030845803864914",
            "extra": "mean: 5.19545012707112 msec\nrounds: 181"
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
          "id": "551b3412ccc9d1444beb2e8c7243660909060bb3",
          "message": "feat(ci): expand performance benchmarks and smart diff-mutation testing",
          "timestamp": "2026-11-01T18:00:32+03:00",
          "tree_id": "ec300e5c1affbd321a6352229fcf2be46242755f",
          "url": "https://github.com/stormsia/mailtmapi/commit/551b3412ccc9d1444beb2e8c7243660909060bb3"
        },
        "date": 1793545275288,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 60527.641881122494,
            "unit": "iter/sec",
            "range": "stddev: 0.000005380807721082351",
            "extra": "mean: 16.521377157960657 usec\nrounds: 753"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 60290.70499065737,
            "unit": "iter/sec",
            "range": "stddev: 0.0000030376493694272538",
            "extra": "mean: 16.586304641071283 usec\nrounds: 17496"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 76440.07444253768,
            "unit": "iter/sec",
            "range": "stddev: 0.000002393466756712954",
            "extra": "mean: 13.082143199006566 usec\nrounds: 25489"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 50957.54166120702,
            "unit": "iter/sec",
            "range": "stddev: 0.0000034887433331541453",
            "extra": "mean: 19.624180590353724 usec\nrounds: 37909"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 395157.6991812212,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013987352060377788",
            "extra": "mean: 2.5306352427702423 usec\nrounds: 31388"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4776.746071583636,
            "unit": "iter/sec",
            "range": "stddev: 0.000016846675223959053",
            "extra": "mean: 209.34753177458936 usec\nrounds: 3336"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 96481.10953462089,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014882216023083096",
            "extra": "mean: 10.364723258506515 usec\nrounds: 48034"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 102067.4300524114,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014274482651587155",
            "extra": "mean: 9.79744468422985 usec\nrounds: 45412"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 194341.92315471882,
            "unit": "iter/sec",
            "range": "stddev: 0.000001712902868967128",
            "extra": "mean: 5.145570156799794 usec\nrounds: 24488"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1175835.6516951271,
            "unit": "iter/sec",
            "range": "stddev: 4.987572981959358e-7",
            "extra": "mean: 850.4589893650221 nsec\nrounds: 30931"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 272.14099213992625,
            "unit": "iter/sec",
            "range": "stddev: 0.0004953567392094963",
            "extra": "mean: 3.674565864321652 msec\nrounds: 199"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 172.33857307560584,
            "unit": "iter/sec",
            "range": "stddev: 0.0014564316712007731",
            "extra": "mean: 5.802531506172416 msec\nrounds: 162"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 221.0949868480648,
            "unit": "iter/sec",
            "range": "stddev: 0.0016359332567329253",
            "extra": "mean: 4.522942895522069 msec\nrounds: 134"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 212.71190548151802,
            "unit": "iter/sec",
            "range": "stddev: 0.0010007626130182346",
            "extra": "mean: 4.701194311321175 msec\nrounds: 106"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 191.68390531718194,
            "unit": "iter/sec",
            "range": "stddev: 0.00039116975143505206",
            "extra": "mean: 5.216922090278192 msec\nrounds: 144"
          }
        ]
      },
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
          "id": "551b3412ccc9d1444beb2e8c7243660909060bb3",
          "message": "feat(ci): expand performance benchmarks and smart diff-mutation testing",
          "timestamp": "2026-11-01T15:00:32Z",
          "url": "https://github.com/stormsia/mailtmapi/commit/551b3412ccc9d1444beb2e8c7243660909060bb3"
        },
        "date": 1793545326105,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 56083.711465586915,
            "unit": "iter/sec",
            "range": "stddev: 0.000007789409597887454",
            "extra": "mean: 17.83048899346831 usec\nrounds: 636"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 58878.93015009794,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032938922272511938",
            "extra": "mean: 16.98400425161829 usec\nrounds: 15994"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73260.90831689973,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024882078836631134",
            "extra": "mean: 13.649844411897924 usec\nrounds: 26583"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 48960.6604715858,
            "unit": "iter/sec",
            "range": "stddev: 0.000003398964953290108",
            "extra": "mean: 20.424561073483634 usec\nrounds: 32641"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 464860.9091797281,
            "unit": "iter/sec",
            "range": "stddev: 7.324409778196814e-7",
            "extra": "mean: 2.1511810957917574 usec\nrounds: 31718"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4574.886720726121,
            "unit": "iter/sec",
            "range": "stddev: 0.00001499511055027819",
            "extra": "mean: 218.58464723718473 usec\nrounds: 2968"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 96600.61552173582,
            "unit": "iter/sec",
            "range": "stddev: 0.000004784145619007563",
            "extra": "mean: 10.351900912836243 usec\nrounds: 47554"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 101959.71991554352,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015017059209195297",
            "extra": "mean: 9.807794694104023 usec\nrounds: 47758"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 181416.92865364053,
            "unit": "iter/sec",
            "range": "stddev: 0.000014618398796590099",
            "extra": "mean: 5.512164754531758 usec\nrounds: 25626"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1193820.4624203239,
            "unit": "iter/sec",
            "range": "stddev: 4.787835051259992e-7",
            "extra": "mean: 837.6468920398828 nsec\nrounds: 37051"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 261.1626743482683,
            "unit": "iter/sec",
            "range": "stddev: 0.0007365991430826784",
            "extra": "mean: 3.829031091427981 msec\nrounds: 175"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 178.4188032282128,
            "unit": "iter/sec",
            "range": "stddev: 0.0002815077399446985",
            "extra": "mean: 5.6047904251488285 msec\nrounds: 167"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 229.83054039085775,
            "unit": "iter/sec",
            "range": "stddev: 0.0008131423357170672",
            "extra": "mean: 4.351031844155113 msec\nrounds: 154"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 206.0362906340453,
            "unit": "iter/sec",
            "range": "stddev: 0.0007166504225190085",
            "extra": "mean: 4.853513897588878 msec\nrounds: 166"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 179.88913093883147,
            "unit": "iter/sec",
            "range": "stddev: 0.0010343228788818018",
            "extra": "mean: 5.558979549131484 msec\nrounds: 173"
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
          "id": "549c3366af05d56850d974b530b9ed0320d7f719",
          "message": "fix(mutmut): resolve alembic directory in mutation sandbox and harden quality gate",
          "timestamp": "2026-11-01T18:05:11+03:00",
          "tree_id": "b9955f3f7c63db729d89ca17cf350ddc033f92d6",
          "url": "https://github.com/stormsia/mailtmapi/commit/549c3366af05d56850d974b530b9ed0320d7f719"
        },
        "date": 1793545551924,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 61097.479566420014,
            "unit": "iter/sec",
            "range": "stddev: 0.00000420434959560076",
            "extra": "mean: 16.367287277585397 usec\nrounds: 731"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 58049.26387512949,
            "unit": "iter/sec",
            "range": "stddev: 0.000003414783675272619",
            "extra": "mean: 17.226747304687837 usec\nrounds: 15861"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 74116.63451894849,
            "unit": "iter/sec",
            "range": "stddev: 0.000002286460608545871",
            "extra": "mean: 13.492247813064722 usec\nrounds: 26407"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49050.60423319315,
            "unit": "iter/sec",
            "range": "stddev: 0.0000030760688815019582",
            "extra": "mean: 20.38710869382701 usec\nrounds: 35853"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 464078.17657482025,
            "unit": "iter/sec",
            "range": "stddev: 6.296390984992561e-7",
            "extra": "mean: 2.1548093628978835 usec\nrounds: 29884"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4617.050495641179,
            "unit": "iter/sec",
            "range": "stddev: 0.00003604154071168285",
            "extra": "mean: 216.58849106027117 usec\nrounds: 3132"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 95731.18574409773,
            "unit": "iter/sec",
            "range": "stddev: 0.000006184778294605189",
            "extra": "mean: 10.445916784872319 usec\nrounds: 49366"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 102584.02419823052,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012748246537453816",
            "extra": "mean: 9.748106567428353 usec\nrounds: 48786"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 214110.70124610138,
            "unit": "iter/sec",
            "range": "stddev: 0.000001243598891699473",
            "extra": "mean: 4.6704811771672645 usec\nrounds: 25554"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1193829.7614045234,
            "unit": "iter/sec",
            "range": "stddev: 4.4618603796766825e-7",
            "extra": "mean: 837.6403674369069 nsec\nrounds: 38214"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 264.5860276340219,
            "unit": "iter/sec",
            "range": "stddev: 0.0006804019473785854",
            "extra": "mean: 3.7794890718235896 msec\nrounds: 181"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 175.87245338253354,
            "unit": "iter/sec",
            "range": "stddev: 0.0007047991457152955",
            "extra": "mean: 5.685938762819995 msec\nrounds: 156"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 249.10733550377566,
            "unit": "iter/sec",
            "range": "stddev: 0.0005616363729439992",
            "extra": "mean: 4.014333813083731 msec\nrounds: 107"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 217.06390976217546,
            "unit": "iter/sec",
            "range": "stddev: 0.00026111208613330576",
            "extra": "mean: 4.606938118343317 msec\nrounds: 169"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 191.9457555256124,
            "unit": "iter/sec",
            "range": "stddev: 0.0001994463664936239",
            "extra": "mean: 5.209805224719149 msec\nrounds: 178"
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
          "id": "7cd3e589c42481d210cc567337bc85cf103c80f9",
          "message": "feat(ci): add ratchet protection and score thresholds to mutation profiles",
          "timestamp": "2026-11-01T18:25:30+03:00",
          "tree_id": "9a68e873895a676d168a5e3b78ad5ec68c721da9",
          "url": "https://github.com/stormsia/mailtmapi/commit/7cd3e589c42481d210cc567337bc85cf103c80f9"
        },
        "date": 1793546763729,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 61953.78037711112,
            "unit": "iter/sec",
            "range": "stddev: 0.000003441434603029764",
            "extra": "mean: 16.14106506355262 usec\nrounds: 707"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 58200.338982251975,
            "unit": "iter/sec",
            "range": "stddev: 0.00000433777469281514",
            "extra": "mean: 17.182030508532726 usec\nrounds: 15340"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 71414.08434248032,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026618998129974483",
            "extra": "mean: 14.002840044889506 usec\nrounds: 25826"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 47402.770831425216,
            "unit": "iter/sec",
            "range": "stddev: 0.0000034057037104795777",
            "extra": "mean: 21.09581322906676 usec\nrounds: 33517"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 461915.2691170117,
            "unit": "iter/sec",
            "range": "stddev: 7.265621458862763e-7",
            "extra": "mean: 2.16489920740568 usec\nrounds: 31163"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4730.526741586558,
            "unit": "iter/sec",
            "range": "stddev: 0.000014650408036503998",
            "extra": "mean: 211.39294937472707 usec\nrounds: 3279"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 93387.3469425684,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024228622311824505",
            "extra": "mean: 10.708088758694288 usec\nrounds: 50181"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 101954.31728931385,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014361631182356771",
            "extra": "mean: 9.80831441558594 usec\nrounds: 47962"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 213778.50160509936,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010356551702026517",
            "extra": "mean: 4.677738839461238 usec\nrounds: 27642"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1194902.8379959909,
            "unit": "iter/sec",
            "range": "stddev: 4.157224036389553e-7",
            "extra": "mean: 836.8881286424355 nsec\nrounds: 38732"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 267.420549084081,
            "unit": "iter/sec",
            "range": "stddev: 0.0007564233819133374",
            "extra": "mean: 3.7394284150003188 msec\nrounds: 200"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 180.51946416933902,
            "unit": "iter/sec",
            "range": "stddev: 0.0005991196345538915",
            "extra": "mean: 5.539568847057594 msec\nrounds: 170"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 250.3215266582704,
            "unit": "iter/sec",
            "range": "stddev: 0.00047111608843965495",
            "extra": "mean: 3.994862181250447 msec\nrounds: 160"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 209.41963937133593,
            "unit": "iter/sec",
            "range": "stddev: 0.0007807871345377238",
            "extra": "mean: 4.775101337209512 msec\nrounds: 172"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 188.24466701159992,
            "unit": "iter/sec",
            "range": "stddev: 0.00046942327692167397",
            "extra": "mean: 5.312235485207018 msec\nrounds: 169"
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
          "id": "2876360faba4520e4db0fce3700ea8e17b376722",
          "message": "feat(benchmarks): add macro load testing, memory profiling, and property tests",
          "timestamp": "2026-11-01T19:38:48+03:00",
          "tree_id": "b79849ecc2293acba52dc673fc35859a5331859a",
          "url": "https://github.com/stormsia/mailtmapi/commit/2876360faba4520e4db0fce3700ea8e17b376722"
        },
        "date": 1793551181498,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 61276.187123359385,
            "unit": "iter/sec",
            "range": "stddev: 0.0000041221716393449925",
            "extra": "mean: 16.319553270944063 usec\nrounds: 535"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59297.595643128916,
            "unit": "iter/sec",
            "range": "stddev: 0.00000365401727610257",
            "extra": "mean: 16.86409017354272 usec\nrounds: 14461"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 70424.37165809661,
            "unit": "iter/sec",
            "range": "stddev: 0.000003582446318157687",
            "extra": "mean: 14.19962970851769 usec\nrounds: 13619"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 48357.18874341526,
            "unit": "iter/sec",
            "range": "stddev: 0.000003232645836759895",
            "extra": "mean: 20.679448619439626 usec\nrounds: 30712"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 466881.28707591636,
            "unit": "iter/sec",
            "range": "stddev: 6.617234344249518e-7",
            "extra": "mean: 2.141872094002767 usec\nrounds: 23486"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4700.903251772076,
            "unit": "iter/sec",
            "range": "stddev: 0.000025129069025952156",
            "extra": "mean: 212.72507568051628 usec\nrounds: 3343"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 96105.56796961695,
            "unit": "iter/sec",
            "range": "stddev: 0.000001462487998916453",
            "extra": "mean: 10.405224391537256 usec\nrounds: 40924"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 101193.40946276438,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016298432937991172",
            "extra": "mean: 9.882066483469606 usec\nrounds: 32023"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 213318.98246875944,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010788869840330783",
            "extra": "mean: 4.687815347827519 usec\nrounds: 22583"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1199113.572610422,
            "unit": "iter/sec",
            "range": "stddev: 4.221577573704483e-7",
            "extra": "mean: 833.9493629640436 nsec\nrounds: 34066"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 243.93886341213047,
            "unit": "iter/sec",
            "range": "stddev: 0.000841634189819651",
            "extra": "mean: 4.099387797468407 msec\nrounds: 158"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 162.39186273432375,
            "unit": "iter/sec",
            "range": "stddev: 0.0007010642851953659",
            "extra": "mean: 6.157944019867667 msec\nrounds: 151"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 218.63285643959034,
            "unit": "iter/sec",
            "range": "stddev: 0.0008033745846282923",
            "extra": "mean: 4.573877944444761 msec\nrounds: 144"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 193.21487057495094,
            "unit": "iter/sec",
            "range": "stddev: 0.0008943182493005308",
            "extra": "mean: 5.175585072848133 msec\nrounds: 151"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 184.15114587052935,
            "unit": "iter/sec",
            "range": "stddev: 0.00032804751701198936",
            "extra": "mean: 5.430321898203487 msec\nrounds: 167"
          }
        ]
      },
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
          "id": "2876360faba4520e4db0fce3700ea8e17b376722",
          "message": "feat(benchmarks): add macro load testing, memory profiling, and property tests",
          "timestamp": "2026-11-01T16:38:48Z",
          "url": "https://github.com/stormsia/mailtmapi/commit/2876360faba4520e4db0fce3700ea8e17b376722"
        },
        "date": 1793551252915,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 61799.99041322297,
            "unit": "iter/sec",
            "range": "stddev: 0.0000035618170361660264",
            "extra": "mean: 16.181232283590063 usec\nrounds: 762"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59859.456113474494,
            "unit": "iter/sec",
            "range": "stddev: 0.000003762106735757584",
            "extra": "mean: 16.70579829700287 usec\nrounds: 16559"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73255.65142206236,
            "unit": "iter/sec",
            "range": "stddev: 0.00000243272412539115",
            "extra": "mean: 13.650823937644086 usec\nrounds: 26803"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 47924.82294009557,
            "unit": "iter/sec",
            "range": "stddev: 0.000021260631374683966",
            "extra": "mean: 20.866013448812666 usec\nrounds: 35096"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 467463.17439828604,
            "unit": "iter/sec",
            "range": "stddev: 6.171244292844273e-7",
            "extra": "mean: 2.139205941274818 usec\nrounds: 33461"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4812.24771955458,
            "unit": "iter/sec",
            "range": "stddev: 0.000014009205894012544",
            "extra": "mean: 207.80310122783115 usec\nrounds: 3665"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 95321.10200110843,
            "unit": "iter/sec",
            "range": "stddev: 0.000002546726937100636",
            "extra": "mean: 10.490856473610341 usec\nrounds: 50590"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 102362.03923911808,
            "unit": "iter/sec",
            "range": "stddev: 0.000001813268136363186",
            "extra": "mean: 9.769246562819998 usec\nrounds: 53605"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 211593.80448274533,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010852412037164822",
            "extra": "mean: 4.726036296027496 usec\nrounds: 26091"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1185100.632748918,
            "unit": "iter/sec",
            "range": "stddev: 4.011237085919391e-7",
            "extra": "mean: 843.8101983630158 nsec\nrounds: 40026"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 269.25544726525925,
            "unit": "iter/sec",
            "range": "stddev: 0.0004905784924963382",
            "extra": "mean: 3.7139452893402067 msec\nrounds: 197"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 181.27122535225485,
            "unit": "iter/sec",
            "range": "stddev: 0.0005288414066306598",
            "extra": "mean: 5.51659535625002 msec\nrounds: 160"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 250.18066612623338,
            "unit": "iter/sec",
            "range": "stddev: 0.0006072804636372156",
            "extra": "mean: 3.9971114294476737 msec\nrounds: 163"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 215.06870855177908,
            "unit": "iter/sec",
            "range": "stddev: 0.0008423648941590699",
            "extra": "mean: 4.649676871794876 msec\nrounds: 156"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 193.0637580080637,
            "unit": "iter/sec",
            "range": "stddev: 0.0002777099730561822",
            "extra": "mean: 5.179636045198254 msec\nrounds: 177"
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
          "id": "b55763b030071dc7dea377f13ad989a602433bcf",
          "message": "feat(mutation): expand targeted tests and ratchet quality gate thresholds",
          "timestamp": "2026-11-01T20:10:34+03:00",
          "tree_id": "7b00d7d9c629d74d331d38bae7b7f32b8f6c4639",
          "url": "https://github.com/stormsia/mailtmapi/commit/b55763b030071dc7dea377f13ad989a602433bcf"
        },
        "date": 1793553077867,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 63056.42793572868,
            "unit": "iter/sec",
            "range": "stddev: 0.000003363927609995587",
            "extra": "mean: 15.858811428697908 usec\nrounds: 700"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 60964.026044064856,
            "unit": "iter/sec",
            "range": "stddev: 0.0000031881226991062466",
            "extra": "mean: 16.40311614717176 usec\nrounds: 16040"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73817.43297320696,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032833701609443765",
            "extra": "mean: 13.546935455788116 usec\nrounds: 28740"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49935.46137720196,
            "unit": "iter/sec",
            "range": "stddev: 0.000005384206353272458",
            "extra": "mean: 20.02584881405642 usec\nrounds: 33138"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 473857.14334426867,
            "unit": "iter/sec",
            "range": "stddev: 5.4154857549042e-7",
            "extra": "mean: 2.110340667110036 usec\nrounds: 29680"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4864.118824876751,
            "unit": "iter/sec",
            "range": "stddev: 0.000014986380184580912",
            "extra": "mean: 205.5870828824455 usec\nrounds: 3511"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 97405.35116266887,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012848475296196305",
            "extra": "mean: 10.26637641632214 usec\nrounds: 47923"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 101792.96803992904,
            "unit": "iter/sec",
            "range": "stddev: 0.0000027393503226951358",
            "extra": "mean: 9.823861306487721 usec\nrounds: 46491"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 213924.26385802333,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011330457106830908",
            "extra": "mean: 4.6745515537390245 usec\nrounds: 26710"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1250239.2887962381,
            "unit": "iter/sec",
            "range": "stddev: 4.7672017099348603e-7",
            "extra": "mean: 799.8468844814702 nsec\nrounds: 30637"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 279.9937877378387,
            "unit": "iter/sec",
            "range": "stddev: 0.0005647178529707251",
            "extra": "mean: 3.571507811224408 msec\nrounds: 196"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 187.81301483825868,
            "unit": "iter/sec",
            "range": "stddev: 0.0006258996654282877",
            "extra": "mean: 5.324444639053277 msec\nrounds: 169"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 265.3312340278778,
            "unit": "iter/sec",
            "range": "stddev: 0.0004490342040583792",
            "extra": "mean: 3.768874040268218 msec\nrounds: 149"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 226.01788349114855,
            "unit": "iter/sec",
            "range": "stddev: 0.0007438214884247869",
            "extra": "mean: 4.4244286538466 msec\nrounds: 130"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 192.8744244209472,
            "unit": "iter/sec",
            "range": "stddev: 0.0004064055652907265",
            "extra": "mean: 5.184720592179222 msec\nrounds: 179"
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
          "id": "a55b0edbe22b76b3404c39df06e8aa4ff5bd088f",
          "message": "chore(mutation): ratchet quality gate to 90% score for auth_security and 65% for retention_retry",
          "timestamp": "2026-11-01T20:24:42+03:00",
          "tree_id": "c56f4cbbd8c0849ad793f2c3a178cce9d4db5478",
          "url": "https://github.com/stormsia/mailtmapi/commit/a55b0edbe22b76b3404c39df06e8aa4ff5bd088f"
        },
        "date": 1793553916673,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 89229.04277109599,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018119382353676795",
            "extra": "mean: 11.207113389811356 usec\nrounds: 829"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 85434.73604897647,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013799277783736617",
            "extra": "mean: 11.704840984429778 usec\nrounds: 20803"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 103315.03534535595,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015908645052100254",
            "extra": "mean: 9.67913330966063 usec\nrounds: 28175"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 69266.18307283502,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019904989999865517",
            "extra": "mean: 14.437059408174354 usec\nrounds: 49505"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 565650.3835939497,
            "unit": "iter/sec",
            "range": "stddev: 3.8964698434590456e-7",
            "extra": "mean: 1.7678764639852993 usec\nrounds: 31165"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 6082.985036555156,
            "unit": "iter/sec",
            "range": "stddev: 0.000007424886818133337",
            "extra": "mean: 164.39297384270867 usec\nrounds: 3823"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 124902.91217259598,
            "unit": "iter/sec",
            "range": "stddev: 9.049913756618228e-7",
            "extra": "mean: 8.006218450840914 usec\nrounds: 54328"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 132118.16388141343,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010168745690269493",
            "extra": "mean: 7.568981967517953 usec\nrounds: 54180"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 274439.40149463975,
            "unit": "iter/sec",
            "range": "stddev: 6.699440118364224e-7",
            "extra": "mean: 3.643791651467844 usec\nrounds: 24699"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1632164.8300491248,
            "unit": "iter/sec",
            "range": "stddev: 2.997072263703023e-7",
            "extra": "mean: 612.6832177666163 nsec\nrounds: 32868"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 397.7813843448527,
            "unit": "iter/sec",
            "range": "stddev: 0.0005351108785720215",
            "extra": "mean: 2.5139436870506233 msec\nrounds: 278"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 265.7120294525158,
            "unit": "iter/sec",
            "range": "stddev: 0.00042142029221124114",
            "extra": "mean: 3.7634728170208995 msec\nrounds: 235"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 371.35828637513293,
            "unit": "iter/sec",
            "range": "stddev: 0.0002448441321238958",
            "extra": "mean: 2.6928172513965007 msec\nrounds: 179"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 316.08354721374934,
            "unit": "iter/sec",
            "range": "stddev: 0.0005155083943983361",
            "extra": "mean: 3.1637205062234917 msec\nrounds: 241"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 258.5205193013044,
            "unit": "iter/sec",
            "range": "stddev: 0.00022922880787448635",
            "extra": "mean: 3.868164905063126 msec\nrounds: 158"
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
          "id": "5d7c109c8bd35cea9f4cf2beeec7367023e87972",
          "message": "feat(client): modernize mailtmapi-client packaging, documentation, and facades\n\n- Implement SyncMailTMAPI synchronous facade and client-side retry policy with HTTP 429 Retry-After support.\n- Enhance ExtractedConfirmation with Mapping dual access (attribute and dict indexing).\n- Cover all 16 MailTMAPI flat facade shortcut methods and format FastAPI 422 validation errors into readable strings.\n- Create PEP 561 py.typed marker and package metadata in client/pyproject.toml and client/MANIFEST.in.\n- Add comprehensive client documentation in client/README.md and integration cookbook in docs/CLIENT_GUIDE.md.\n- Update root README.md with Python Client SDK section and demarcation between attribute access and dict indexing.\n- Elevate test coverage on mailtmapi.standalone_client to >98% and verify strict twine validation on packages.",
          "timestamp": "2026-11-02T01:41:47+03:00",
          "tree_id": "2944dee2374a13517633b6c71a16f4aae2897d9f",
          "url": "https://github.com/stormsia/mailtmapi/commit/5d7c109c8bd35cea9f4cf2beeec7367023e87972"
        },
        "date": 1793574283821,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 78186.85235991064,
            "unit": "iter/sec",
            "range": "stddev: 0.000003431649271678068",
            "extra": "mean: 12.789874126109954 usec\nrounds: 715"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 80682.34331817846,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026727668254652175",
            "extra": "mean: 12.394285526095906 usec\nrounds: 10633"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 97655.64954995898,
            "unit": "iter/sec",
            "range": "stddev: 0.000002046456849559688",
            "extra": "mean: 10.240062962137351 usec\nrounds: 29621"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 64075.61000691924,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023344830278109733",
            "extra": "mean: 15.606562308060967 usec\nrounds: 26706"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 557624.7427317993,
            "unit": "iter/sec",
            "range": "stddev: 4.237515279915511e-7",
            "extra": "mean: 1.7933207108081466 usec\nrounds: 29154"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 5433.94728477972,
            "unit": "iter/sec",
            "range": "stddev: 0.000027531520792677522",
            "extra": "mean: 184.02828507390237 usec\nrounds: 3571"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 104183.83993819436,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014535824304782208",
            "extra": "mean: 9.598417572180448 usec\nrounds: 47302"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 118016.10879937955,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012589921855809156",
            "extra": "mean: 8.473419520210934 usec\nrounds: 42346"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 249127.32407689627,
            "unit": "iter/sec",
            "range": "stddev: 6.501564378243872e-7",
            "extra": "mean: 4.01401172555178 usec\nrounds: 24050"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1568987.7112393212,
            "unit": "iter/sec",
            "range": "stddev: 3.5200566257754235e-7",
            "extra": "mean: 637.3536215972744 nsec\nrounds: 31381"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 359.2730167757803,
            "unit": "iter/sec",
            "range": "stddev: 0.0003165565069548966",
            "extra": "mean: 2.783398566845594 msec\nrounds: 187"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 239.02607676401078,
            "unit": "iter/sec",
            "range": "stddev: 0.00038505810935495193",
            "extra": "mean: 4.183643950225961 msec\nrounds: 221"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 309.91554759399713,
            "unit": "iter/sec",
            "range": "stddev: 0.0006603788795783398",
            "extra": "mean: 3.226685488235148 msec\nrounds: 170"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 269.9766492035799,
            "unit": "iter/sec",
            "range": "stddev: 0.0005333153730393242",
            "extra": "mean: 3.7040240441162573 msec\nrounds: 204"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 220.71975294671157,
            "unit": "iter/sec",
            "range": "stddev: 0.0003658593108096105",
            "extra": "mean: 4.53063210994727 msec\nrounds: 191"
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
          "id": "29c5b2752dab080e287e812ebfed2c0922ca7c8f",
          "message": "Rename project MailTMAPI--->Maily",
          "timestamp": "2026-11-02T04:24:37+03:00",
          "tree_id": "abc0b5a5df1435f5961aa2fdd88f7594910af4db",
          "url": "https://github.com/stormsia/maily/commit/29c5b2752dab080e287e812ebfed2c0922ca7c8f"
        },
        "date": 1793582739283,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 62765.873351596405,
            "unit": "iter/sec",
            "range": "stddev: 0.000005246571662559275",
            "extra": "mean: 15.932224736176089 usec\nrounds: 663"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 61648.17886917496,
            "unit": "iter/sec",
            "range": "stddev: 0.0000035369011114559175",
            "extra": "mean: 16.221079330212227 usec\nrounds: 16841"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 75742.21996048836,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023517434898872293",
            "extra": "mean: 13.202676136528071 usec\nrounds: 29849"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 48702.49523004011,
            "unit": "iter/sec",
            "range": "stddev: 0.000004601050188580104",
            "extra": "mean: 20.532828867938406 usec\nrounds: 35458"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 463889.8766744398,
            "unit": "iter/sec",
            "range": "stddev: 0.000004365890584089143",
            "extra": "mean: 2.155684032531292 usec\nrounds: 34301"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4887.961271207099,
            "unit": "iter/sec",
            "range": "stddev: 0.000014088481090115854",
            "extra": "mean: 204.58427236127557 usec\nrounds: 3477"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 97615.65116748543,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012830532288249006",
            "extra": "mean: 10.244258866687636 usec\nrounds: 51795"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 103091.76730609406,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013903319380090256",
            "extra": "mean: 9.700095615112101 usec\nrounds: 54186"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 213922.19299953137,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012339668201315045",
            "extra": "mean: 4.674596805401068 usec\nrounds: 26357"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1237786.1807167812,
            "unit": "iter/sec",
            "range": "stddev: 4.1645190715645417e-7",
            "extra": "mean: 807.8939768263666 nsec\nrounds: 39265"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 276.24874215261246,
            "unit": "iter/sec",
            "range": "stddev: 0.0004929557197517547",
            "extra": "mean: 3.6199259848486625 msec\nrounds: 198"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 174.95516198742118,
            "unit": "iter/sec",
            "range": "stddev: 0.0014760261939062342",
            "extra": "mean: 5.71575018787898 msec\nrounds: 165"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 201.22013016704489,
            "unit": "iter/sec",
            "range": "stddev: 0.0016524348752427556",
            "extra": "mean: 4.969681707142521 msec\nrounds: 140"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 224.09766548610125,
            "unit": "iter/sec",
            "range": "stddev: 0.00043727986815435396",
            "extra": "mean: 4.462340104395335 msec\nrounds: 182"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 192.65106433118862,
            "unit": "iter/sec",
            "range": "stddev: 0.0003879728826015872",
            "extra": "mean: 5.190731769230657 msec\nrounds: 182"
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
          "id": "4c4647161bb90f599172150c5a74644a2419a2f2",
          "message": "Refactor test cases for improved readability and consistency\n\n- Consolidated multi-line key creation calls into single lines for brevity.\n- Streamlined assertions and response handling in various test cases.\n- Enhanced clarity by removing unnecessary line breaks and aligning code style.\n- Ensured consistent formatting across multiple test files, including test_keys_service.py, test_mailbox_ownership.py, test_mailtm.py, and others.",
          "timestamp": "2026-11-02T04:31:49+03:00",
          "tree_id": "9f6f0fc8a275b15c75dfe819bdd8c72414902d9d",
          "url": "https://github.com/stormsia/maily/commit/4c4647161bb90f599172150c5a74644a2419a2f2"
        },
        "date": 1793583165286,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 90720.61610483685,
            "unit": "iter/sec",
            "range": "stddev: 0.000002281850707637671",
            "extra": "mean: 11.022852830324684 usec\nrounds: 795"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 86271.78541580451,
            "unit": "iter/sec",
            "range": "stddev: 0.000001935607117083515",
            "extra": "mean: 11.591275121759628 usec\nrounds: 14579"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 102813.00246791415,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015127696048699607",
            "extra": "mean: 9.726396233901248 usec\nrounds: 27721"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 68313.50318561916,
            "unit": "iter/sec",
            "range": "stddev: 0.000006301660064744786",
            "extra": "mean: 14.638394363744359 usec\nrounds: 34562"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 554846.1070974289,
            "unit": "iter/sec",
            "range": "stddev: 4.6181772580446387e-7",
            "extra": "mean: 1.802301552102994 usec\nrounds: 27060"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 6111.971147316104,
            "unit": "iter/sec",
            "range": "stddev: 0.000007533841988354562",
            "extra": "mean: 163.61333780823247 usec\nrounds: 3650"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 119727.31542463123,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036279250231314534",
            "extra": "mean: 8.352312890783086 usec\nrounds: 51021"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 136307.66101477153,
            "unit": "iter/sec",
            "range": "stddev: 9.752258761703765e-7",
            "extra": "mean: 7.33634479936994 usec\nrounds: 51311"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 270317.0019440626,
            "unit": "iter/sec",
            "range": "stddev: 7.087413635429599e-7",
            "extra": "mean: 3.69936035398518 usec\nrounds: 19664"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1690816.838481883,
            "unit": "iter/sec",
            "range": "stddev: 3.339392141078424e-7",
            "extra": "mean: 591.4301166398723 nsec\nrounds: 34207"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 387.33655647772605,
            "unit": "iter/sec",
            "range": "stddev: 0.0005584751974374508",
            "extra": "mean: 2.5817341102362628 msec\nrounds: 254"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 257.1329782902125,
            "unit": "iter/sec",
            "range": "stddev: 0.0003461506429366961",
            "extra": "mean: 3.8890382970299218 msec\nrounds: 202"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 360.72718125191653,
            "unit": "iter/sec",
            "range": "stddev: 0.0002973282509771049",
            "extra": "mean: 2.77217812234017 msec\nrounds: 188"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 309.51640544596927,
            "unit": "iter/sec",
            "range": "stddev: 0.0004482945679166945",
            "extra": "mean: 3.2308465154185986 msec\nrounds: 227"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 254.84920151397318,
            "unit": "iter/sec",
            "range": "stddev: 0.00045785867381796297",
            "extra": "mean: 3.9238890844442014 msec\nrounds: 225"
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
          "id": "b5efb86521a8ac127ee59900278ed3ec80a18038",
          "message": "Env MAILTM_--->MAILY_",
          "timestamp": "2026-11-02T04:34:15+03:00",
          "tree_id": "a2a209f79c9f6a493a66a5c2c24bf2449302a37d",
          "url": "https://github.com/stormsia/maily/commit/b5efb86521a8ac127ee59900278ed3ec80a18038"
        },
        "date": 1793583310969,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 125677.79891048578,
            "unit": "iter/sec",
            "range": "stddev: 0.000002369481894651805",
            "extra": "mean: 7.956854819778088 usec\nrounds: 861"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 122225.88045645058,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013209705757208657",
            "extra": "mean: 8.181573299087853 usec\nrounds: 23752"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 144470.97481537255,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015266229652709143",
            "extra": "mean: 6.921805582595088 usec\nrounds: 29807"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 94738.63481017148,
            "unit": "iter/sec",
            "range": "stddev: 0.000001663868006514039",
            "extra": "mean: 10.555355816596972 usec\nrounds: 47502"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 805370.7130797498,
            "unit": "iter/sec",
            "range": "stddev: 2.6856408281822875e-7",
            "extra": "mean: 1.24166422215179 usec\nrounds: 29454"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 8790.952048179102,
            "unit": "iter/sec",
            "range": "stddev: 0.00000598425373806843",
            "extra": "mean: 113.75332211112826 usec\nrounds: 4604"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 146526.99258388754,
            "unit": "iter/sec",
            "range": "stddev: 8.091370821522434e-7",
            "extra": "mean: 6.82468112097158 usec\nrounds: 64087"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 189050.10860678274,
            "unit": "iter/sec",
            "range": "stddev: 6.964330620214718e-7",
            "extra": "mean: 5.289602885550111 usec\nrounds: 65777"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 370736.6649739529,
            "unit": "iter/sec",
            "range": "stddev: 4.497737524080121e-7",
            "extra": "mean: 2.697332350632915 usec\nrounds: 25100"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 2078699.0350544418,
            "unit": "iter/sec",
            "range": "stddev: 2.3665961524509407e-7",
            "extra": "mean: 481.0701227721548 nsec\nrounds: 30304"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 561.6063645565368,
            "unit": "iter/sec",
            "range": "stddev: 0.00030691577592791653",
            "extra": "mean: 1.780606601190557 msec\nrounds: 336"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 377.04622311994757,
            "unit": "iter/sec",
            "range": "stddev: 0.00025101373322566206",
            "extra": "mean: 2.652194714285404 msec\nrounds: 266"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 517.2836048872396,
            "unit": "iter/sec",
            "range": "stddev: 0.0002027804378271071",
            "extra": "mean: 1.933175516393924 msec\nrounds: 244"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 435.3440160213998,
            "unit": "iter/sec",
            "range": "stddev: 0.0003081376983638894",
            "extra": "mean: 2.2970339850745622 msec\nrounds: 268"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 355.45745009198805,
            "unit": "iter/sec",
            "range": "stddev: 0.00024859181219978143",
            "extra": "mean: 2.8132762437282217 msec\nrounds: 279"
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
          "id": "fd9b0fc9af22a85111e4d63594821ed037fc7c65",
          "message": "mailtm-->maily",
          "timestamp": "2026-11-02T04:58:41+03:00",
          "tree_id": "1b55c1b2adcb0d149adadd638fd04b94c8ebdaf8",
          "url": "https://github.com/stormsia/maily/commit/fd9b0fc9af22a85111e4d63594821ed037fc7c65"
        },
        "date": 1793584778070,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 61947.455113377844,
            "unit": "iter/sec",
            "range": "stddev: 0.000004631518806447021",
            "extra": "mean: 16.142713177963063 usec\nrounds: 516"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 57247.44628480898,
            "unit": "iter/sec",
            "range": "stddev: 0.000005095039192331931",
            "extra": "mean: 17.46802809377642 usec\nrounds: 14416"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 71986.00512299479,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024764532320959096",
            "extra": "mean: 13.891589042778621 usec\nrounds: 24404"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 47999.878779821745,
            "unit": "iter/sec",
            "range": "stddev: 0.00000318796115531373",
            "extra": "mean: 20.833385946390795 usec\nrounds: 30284"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 456014.82359434094,
            "unit": "iter/sec",
            "range": "stddev: 8.293197032980738e-7",
            "extra": "mean: 2.1929111692421084 usec\nrounds: 28650"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4664.929919050351,
            "unit": "iter/sec",
            "range": "stddev: 0.00005633892993535502",
            "extra": "mean: 214.36549259105954 usec\nrounds: 2767"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 97487.19898050121,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014374283363924055",
            "extra": "mean: 10.257757023052983 usec\nrounds: 46169"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 102405.8963543108,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014093204037364585",
            "extra": "mean: 9.765062712210757 usec\nrounds: 46817"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 207960.3135011089,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011350621604005234",
            "extra": "mean: 4.808609792726956 usec\nrounds: 22588"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1185071.0733584927,
            "unit": "iter/sec",
            "range": "stddev: 4.47348129862494e-7",
            "extra": "mean: 843.8312456366004 nsec\nrounds: 32651"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 239.63358072941244,
            "unit": "iter/sec",
            "range": "stddev: 0.0007145152303760221",
            "extra": "mean: 4.173037839505358 msec\nrounds: 162"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 158.5936894896779,
            "unit": "iter/sec",
            "range": "stddev: 0.0008079760134845179",
            "extra": "mean: 6.3054211250005965 msec\nrounds: 152"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 228.97279747808955,
            "unit": "iter/sec",
            "range": "stddev: 0.0006118330858651868",
            "extra": "mean: 4.367331014924121 msec\nrounds: 134"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 195.94412040767273,
            "unit": "iter/sec",
            "range": "stddev: 0.0006808440022786943",
            "extra": "mean: 5.103495822785822 msec\nrounds: 158"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 181.15452237338746,
            "unit": "iter/sec",
            "range": "stddev: 0.0004972488479380696",
            "extra": "mean: 5.52014924550901 msec\nrounds: 167"
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
          "id": "40b409fdb94a4aa7f57a42ea7db035d5e74c2a13",
          "message": "Fix formatting by removing unnecessary line breaks in JSON and Python files",
          "timestamp": "2026-11-02T05:15:25+03:00",
          "tree_id": "fc5aecc97c066200e519f5eab70ad08f071615be",
          "url": "https://github.com/stormsia/maily/commit/40b409fdb94a4aa7f57a42ea7db035d5e74c2a13"
        },
        "date": 1793585793508,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 61464.037210955255,
            "unit": "iter/sec",
            "range": "stddev: 0.000003576223164425068",
            "extra": "mean: 16.26967647061364 usec\nrounds: 680"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 57949.38576479484,
            "unit": "iter/sec",
            "range": "stddev: 0.0000049055132904025994",
            "extra": "mean: 17.256438300464534 usec\nrounds: 14757"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73697.29397643519,
            "unit": "iter/sec",
            "range": "stddev: 0.000002456048053806248",
            "extra": "mean: 13.56901924132725 usec\nrounds: 21880"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49513.7588571065,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033613796428865332",
            "extra": "mean: 20.1964064753382 usec\nrounds: 29126"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 459170.30252808746,
            "unit": "iter/sec",
            "range": "stddev: 7.76903001233699e-7",
            "extra": "mean: 2.177841194202297 usec\nrounds: 23513"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4528.093973014562,
            "unit": "iter/sec",
            "range": "stddev: 0.00008651805119773144",
            "extra": "mean: 220.84347320518475 usec\nrounds: 2967"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 97776.0712131821,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014771346326142059",
            "extra": "mean: 10.227451232108624 usec\nrounds: 47439"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 102217.95063310684,
            "unit": "iter/sec",
            "range": "stddev: 0.000001529042874068496",
            "extra": "mean: 9.783017501390948 usec\nrounds: 41711"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 216778.20154739797,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012888600760288773",
            "extra": "mean: 4.613009946857377 usec\nrounds: 23525"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1190496.7647595562,
            "unit": "iter/sec",
            "range": "stddev: 5.409287728345701e-7",
            "extra": "mean: 839.9854830365452 nsec\nrounds: 36509"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 195.41316730853447,
            "unit": "iter/sec",
            "range": "stddev: 0.0005804724258234413",
            "extra": "mean: 5.117362426356446 msec\nrounds: 129"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 127.24624365047436,
            "unit": "iter/sec",
            "range": "stddev: 0.0010948664134579516",
            "extra": "mean: 7.858778155737505 msec\nrounds: 122"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 173.08215074676934,
            "unit": "iter/sec",
            "range": "stddev: 0.0006297036952491744",
            "extra": "mean: 5.777603269230611 msec\nrounds: 104"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 149.7763528301352,
            "unit": "iter/sec",
            "range": "stddev: 0.0012875519596036243",
            "extra": "mean: 6.676621383177376 msec\nrounds: 107"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 183.23899073309505,
            "unit": "iter/sec",
            "range": "stddev: 0.0005501133548203164",
            "extra": "mean: 5.457353786981914 msec\nrounds: 169"
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
          "id": "27287cd86b8a12a840997aee04663901641cfa4a",
          "message": "feat(publish): configure maily-server and maily-client OIDC trusted publishing",
          "timestamp": "2026-11-02T06:09:23+03:00",
          "tree_id": "471a96bce6353da9d3dac2abe0a4a65f36e0b0e4",
          "url": "https://github.com/stormsia/maily/commit/27287cd86b8a12a840997aee04663901641cfa4a"
        },
        "date": 1793589013687,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 66656.11200796076,
            "unit": "iter/sec",
            "range": "stddev: 0.000005225846773271884",
            "extra": "mean: 15.00237517424613 usec\nrounds: 717"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 66924.10361803707,
            "unit": "iter/sec",
            "range": "stddev: 0.000002031174399701379",
            "extra": "mean: 14.942299499555562 usec\nrounds: 13389"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 80227.05366151006,
            "unit": "iter/sec",
            "range": "stddev: 0.000002896706047166571",
            "extra": "mean: 12.464623270588367 usec\nrounds: 16046"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 54790.02798711701,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026941427686437403",
            "extra": "mean: 18.251496426231682 usec\nrounds: 36656"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 441611.8296707857,
            "unit": "iter/sec",
            "range": "stddev: 5.341772910030994e-7",
            "extra": "mean: 2.2644320935548383 usec\nrounds: 28392"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4769.776479888947,
            "unit": "iter/sec",
            "range": "stddev: 0.00002762359463908539",
            "extra": "mean: 209.6534301379428 usec\nrounds: 3192"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 96581.04756076993,
            "unit": "iter/sec",
            "range": "stddev: 0.000001980911054196663",
            "extra": "mean: 10.353998276636917 usec\nrounds: 46421"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 105783.85463159226,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013026359620585815",
            "extra": "mean: 9.45323843116368 usec\nrounds: 47347"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 211126.20422967817,
            "unit": "iter/sec",
            "range": "stddev: 8.272265320325112e-7",
            "extra": "mean: 4.736503475012171 usec\nrounds: 21151"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1290643.2520372812,
            "unit": "iter/sec",
            "range": "stddev: 4.0784650080418065e-7",
            "extra": "mean: 774.8074445990396 nsec\nrounds: 29498"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 291.66401018369174,
            "unit": "iter/sec",
            "range": "stddev: 0.0005345203915412125",
            "extra": "mean: 3.428602656084287 msec\nrounds: 189"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 196.2508956247735,
            "unit": "iter/sec",
            "range": "stddev: 0.0006435138336701034",
            "extra": "mean: 5.095518146892809 msec\nrounds: 177"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 272.2056912246973,
            "unit": "iter/sec",
            "range": "stddev: 0.0004579496004243678",
            "extra": "mean: 3.6736924768208876 msec\nrounds: 151"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 207.71738613908835,
            "unit": "iter/sec",
            "range": "stddev: 0.001124519438538159",
            "extra": "mean: 4.814233505376369 msec\nrounds: 186"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 197.34517024282204,
            "unit": "iter/sec",
            "range": "stddev: 0.0004268297732629431",
            "extra": "mean: 5.0672636111112155 msec\nrounds: 162"
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
          "id": "0567e3bdc5c8789e2d395617e5bce584461b59c7",
          "message": "docs: emphasize PyPI as preferred installation while keeping git and single-file options",
          "timestamp": "2026-11-02T06:16:54+03:00",
          "tree_id": "242b06a0fde86b3e93d3fd2bf309eef1f8cd4e75",
          "url": "https://github.com/stormsia/maily/commit/0567e3bdc5c8789e2d395617e5bce584461b59c7"
        },
        "date": 1793589455898,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 60412.79719083465,
            "unit": "iter/sec",
            "range": "stddev: 0.000004294820548758669",
            "extra": "mean: 16.552784285772354 usec\nrounds: 700"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 57584.713924200565,
            "unit": "iter/sec",
            "range": "stddev: 0.000004934399035143509",
            "extra": "mean: 17.36571968241974 usec\nrounds: 15618"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73674.4979642304,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026052144176052505",
            "extra": "mean: 13.573217702623623 usec\nrounds: 26674"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49246.0690014045,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032976225043466913",
            "extra": "mean: 20.30618931170892 usec\nrounds: 35085"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 462796.6204375988,
            "unit": "iter/sec",
            "range": "stddev: 6.500022852885229e-7",
            "extra": "mean: 2.1607763666347584 usec\nrounds: 31574"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4763.11333648604,
            "unit": "iter/sec",
            "range": "stddev: 0.000011588769920340445",
            "extra": "mean: 209.94671538463632 usec\nrounds: 3380"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 96265.33844018527,
            "unit": "iter/sec",
            "range": "stddev: 0.000001877160635942493",
            "extra": "mean: 10.387954960770774 usec\nrounds: 46404"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 97723.57609035721,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025449621246244653",
            "extra": "mean: 10.23294521145419 usec\nrounds: 45849"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 206325.32949790236,
            "unit": "iter/sec",
            "range": "stddev: 0.000001119606575717888",
            "extra": "mean: 4.846714663844347 usec\nrounds: 25314"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1206512.6739794584,
            "unit": "iter/sec",
            "range": "stddev: 3.753195649735222e-7",
            "extra": "mean: 828.8350562466 nsec\nrounds: 37146"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 260.259012425986,
            "unit": "iter/sec",
            "range": "stddev: 0.0005495434730477707",
            "extra": "mean: 3.842326114583202 msec\nrounds: 192"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 172.00899669446298,
            "unit": "iter/sec",
            "range": "stddev: 0.0007885310277813923",
            "extra": "mean: 5.81364939751544 msec\nrounds: 161"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 239.98876452600376,
            "unit": "iter/sec",
            "range": "stddev: 0.0005646220288567542",
            "extra": "mean: 4.1668617361111755 msec\nrounds: 144"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 207.97335418487032,
            "unit": "iter/sec",
            "range": "stddev: 0.000768389082361874",
            "extra": "mean: 4.80830827544901 msec\nrounds: 167"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 186.5851575555046,
            "unit": "iter/sec",
            "range": "stddev: 0.0005428464377896272",
            "extra": "mean: 5.359483107344827 msec\nrounds: 177"
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
          "id": "48aa41ae268e05adca7cb925d6cd2dd04b58bdf6",
          "message": "fix(ci): whitelist pypi-publish-client in zizmor and add LICENSE file",
          "timestamp": "2026-11-02T06:20:27+03:00",
          "tree_id": "67a30ddf553bf3a31ac504804d3723b75dff0e11",
          "url": "https://github.com/stormsia/maily/commit/48aa41ae268e05adca7cb925d6cd2dd04b58bdf6"
        },
        "date": 1793589661723,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 114470.49812799577,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016746654111382106",
            "extra": "mean: 8.735875324678371 usec\nrounds: 770"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 114482.46078007152,
            "unit": "iter/sec",
            "range": "stddev: 0.00000234401058685293",
            "extra": "mean: 8.734962484087996 usec\nrounds: 21191"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 138579.04985046788,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012435716260532833",
            "extra": "mean: 7.216097967759473 usec\nrounds: 23324"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 91684.45805725934,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016236057582568822",
            "extra": "mean: 10.906973997441026 usec\nrounds: 33689"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 831272.8265587146,
            "unit": "iter/sec",
            "range": "stddev: 2.4491874649108075e-7",
            "extra": "mean: 1.2029744844899821 usec\nrounds: 29825"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 7771.040574585701,
            "unit": "iter/sec",
            "range": "stddev: 0.0000460381166757911",
            "extra": "mean: 128.68289521874144 usec\nrounds: 4915"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 136781.01852466087,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018536576533862184",
            "extra": "mean: 7.310955941008039 usec\nrounds: 54654"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 176922.3941530227,
            "unit": "iter/sec",
            "range": "stddev: 0.00000467351493493268",
            "extra": "mean: 5.6521957256303335 usec\nrounds: 59190"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 356605.4616570023,
            "unit": "iter/sec",
            "range": "stddev: 9.540908586966676e-7",
            "extra": "mean: 2.8042195297665993 usec\nrounds: 23605"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 2162473.753657412,
            "unit": "iter/sec",
            "range": "stddev: 3.273331656023464e-7",
            "extra": "mean: 462.4333582355351 nsec\nrounds: 29456"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 523.8647353915707,
            "unit": "iter/sec",
            "range": "stddev: 0.0005000507897098074",
            "extra": "mean: 1.9088897046153235 msec\nrounds: 325"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 351.0846045601686,
            "unit": "iter/sec",
            "range": "stddev: 0.0004755093940190165",
            "extra": "mean: 2.848316294736931 msec\nrounds: 285"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 482.5328509954197,
            "unit": "iter/sec",
            "range": "stddev: 0.00020682925570663242",
            "extra": "mean: 2.072397760975433 msec\nrounds: 205"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 400.52772834383717,
            "unit": "iter/sec",
            "range": "stddev: 0.00033616866417865394",
            "extra": "mean: 2.496706043636359 msec\nrounds: 275"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 326.4189761326267,
            "unit": "iter/sec",
            "range": "stddev: 0.00022881644463642676",
            "extra": "mean: 3.0635473827161683 msec\nrounds: 243"
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
          "id": "7efdf0eb53a85af993ed9cef78046740d2c1d0b8",
          "message": "fix(docker): support workflow_dispatch, add release wheels, and modernize paths/user to maily",
          "timestamp": "2026-11-02T06:27:41+03:00",
          "tree_id": "6db293b4b73db326e2f797deba490f9e6a75c5e2",
          "url": "https://github.com/stormsia/maily/commit/7efdf0eb53a85af993ed9cef78046740d2c1d0b8"
        },
        "date": 1793590100334,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 61720.67738190628,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036353535406689917",
            "extra": "mean: 16.202025681156165 usec\nrounds: 662"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 58926.62088792262,
            "unit": "iter/sec",
            "range": "stddev: 0.000003806542790525605",
            "extra": "mean: 16.970258686680545 usec\nrounds: 15138"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73811.17632203746,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024826849644220033",
            "extra": "mean: 13.548083770363037 usec\nrounds: 27265"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49015.0542965636,
            "unit": "iter/sec",
            "range": "stddev: 0.0000034173748677304762",
            "extra": "mean: 20.40189517998982 usec\nrounds: 32780"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 459642.24351212406,
            "unit": "iter/sec",
            "range": "stddev: 7.220648974392249e-7",
            "extra": "mean: 2.175605080070546 usec\nrounds: 33779"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4655.68651213057,
            "unit": "iter/sec",
            "range": "stddev: 0.000014566294359915472",
            "extra": "mean: 214.7910941586083 usec\nrounds: 3441"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 95955.73993400486,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015223881301803915",
            "extra": "mean: 10.421471406377215 usec\nrounds: 49609"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 96611.36932668112,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036504899424331453",
            "extra": "mean: 10.350748643450087 usec\nrounds: 46993"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 206840.24175208827,
            "unit": "iter/sec",
            "range": "stddev: 0.000001098830508064199",
            "extra": "mean: 4.834649154967466 usec\nrounds: 14257"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1205324.2884501733,
            "unit": "iter/sec",
            "range": "stddev: 3.806122088054988e-7",
            "extra": "mean: 829.6522434521062 nsec\nrounds: 18096"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 239.1835305072812,
            "unit": "iter/sec",
            "range": "stddev: 0.0009442260511436545",
            "extra": "mean: 4.180889870966923 msec\nrounds: 155"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 169.1272915270691,
            "unit": "iter/sec",
            "range": "stddev: 0.0005000600839610907",
            "extra": "mean: 5.912706287500313 msec\nrounds: 160"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 220.07444904904966,
            "unit": "iter/sec",
            "range": "stddev: 0.000564584308185339",
            "extra": "mean: 4.543916862321089 msec\nrounds: 138"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 180.22736849508107,
            "unit": "iter/sec",
            "range": "stddev: 0.0012984621736273588",
            "extra": "mean: 5.548546862499926 msec\nrounds: 160"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 177.45364316425648,
            "unit": "iter/sec",
            "range": "stddev: 0.0006780080630769438",
            "extra": "mean: 5.635274554912178 msec\nrounds: 173"
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
          "id": "b218fe7d254349bb5452aa1a4e7b8414b82a4b87",
          "message": "fix(ci): fix release-please env secret expression in if condition",
          "timestamp": "2026-11-02T07:15:29+03:00",
          "tree_id": "93382c9a0c969d4109747b8485c1a15a88a2a9ef",
          "url": "https://github.com/stormsia/maily/commit/b218fe7d254349bb5452aa1a4e7b8414b82a4b87"
        },
        "date": 1793592962252,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 61045.49429869881,
            "unit": "iter/sec",
            "range": "stddev: 0.0000035438109455013195",
            "extra": "mean: 16.381225371146108 usec\nrounds: 741"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 56831.9821602783,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037846850405351252",
            "extra": "mean: 17.595726244067766 usec\nrounds: 16438"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 74407.10545032388,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021690063817345153",
            "extra": "mean: 13.439576690261468 usec\nrounds: 27422"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49780.493117416525,
            "unit": "iter/sec",
            "range": "stddev: 0.000002825963843583562",
            "extra": "mean: 20.088189918916925 usec\nrounds: 34778"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 476128.0196091567,
            "unit": "iter/sec",
            "range": "stddev: 5.44213640504192e-7",
            "extra": "mean: 2.100275469653894 usec\nrounds: 33216"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4771.380107646041,
            "unit": "iter/sec",
            "range": "stddev: 0.000010032551019383704",
            "extra": "mean: 209.58296707435235 usec\nrounds: 3189"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 95824.93187103068,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011864211200769402",
            "extra": "mean: 10.435697479502357 usec\nrounds: 49633"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 102933.07186970409,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012307101357130113",
            "extra": "mean: 9.715050584187669 usec\nrounds: 50925"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 215662.02061728272,
            "unit": "iter/sec",
            "range": "stddev: 9.231900564575369e-7",
            "extra": "mean: 4.636885053463429 usec\nrounds: 25899"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1226368.446875453,
            "unit": "iter/sec",
            "range": "stddev: 4.182397419780235e-7",
            "extra": "mean: 815.4156302274447 nsec\nrounds: 38272"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 297.6449296394103,
            "unit": "iter/sec",
            "range": "stddev: 0.0005831290868951976",
            "extra": "mean: 3.3597078277512606 msec\nrounds: 209"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 196.25293408116613,
            "unit": "iter/sec",
            "range": "stddev: 0.0007549015936087689",
            "extra": "mean: 5.0954652203386726 msec\nrounds: 177"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 265.8304001640999,
            "unit": "iter/sec",
            "range": "stddev: 0.0005619127450225208",
            "extra": "mean: 3.7617969930553072 msec\nrounds: 144"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 239.28445049424434,
            "unit": "iter/sec",
            "range": "stddev: 0.000438593006547044",
            "extra": "mean: 4.179126549738148 msec\nrounds: 191"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 195.57145750251462,
            "unit": "iter/sec",
            "range": "stddev: 0.00010629667181151817",
            "extra": "mean: 5.113220573033477 msec\nrounds: 178"
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
          "id": "167f92f52ff244bb4d47fa28485826941849ff58",
          "message": "feat(pages): unify developer portal with API docs, benchmarks, and security analytics",
          "timestamp": "2026-11-02T07:25:32+03:00",
          "tree_id": "8d4652d7e081757db7910df7289ddd9f0cd41d99",
          "url": "https://github.com/stormsia/maily/commit/167f92f52ff244bb4d47fa28485826941849ff58"
        },
        "date": 1793593565921,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 61084.246219917346,
            "unit": "iter/sec",
            "range": "stddev: 0.000004272143350916388",
            "extra": "mean: 16.370833101545852 usec\nrounds: 719"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59431.7388810988,
            "unit": "iter/sec",
            "range": "stddev: 0.0000034600677366310323",
            "extra": "mean: 16.826026275297693 usec\nrounds: 16898"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 74883.72356786889,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023804718824134857",
            "extra": "mean: 13.354036796710254 usec\nrounds: 26660"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49865.57290173417,
            "unit": "iter/sec",
            "range": "stddev: 0.000003018183853096554",
            "extra": "mean: 20.053915794181584 usec\nrounds: 33620"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 480914.6792122303,
            "unit": "iter/sec",
            "range": "stddev: 6.005549051853982e-7",
            "extra": "mean: 2.079370922172859 usec\nrounds: 30807"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4893.1202843612855,
            "unit": "iter/sec",
            "range": "stddev: 0.000009945889115902792",
            "extra": "mean: 204.3685709497193 usec\nrounds: 3580"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 98550.99733739645,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012998373741419162",
            "extra": "mean: 10.147030745680105 usec\nrounds: 49633"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 102906.11443420697,
            "unit": "iter/sec",
            "range": "stddev: 0.000001318368511554816",
            "extra": "mean: 9.717595552977079 usec\nrounds: 49831"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 221370.5456093948,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010062898222117065",
            "extra": "mean: 4.517312803504066 usec\nrounds: 24712"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1235494.9750442447,
            "unit": "iter/sec",
            "range": "stddev: 4.1153228267695837e-7",
            "extra": "mean: 809.3922032861273 nsec\nrounds: 36323"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 298.21764914003785,
            "unit": "iter/sec",
            "range": "stddev: 0.0005616138281451652",
            "extra": "mean: 3.3532555933013115 msec\nrounds: 209"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 201.4971148209132,
            "unit": "iter/sec",
            "range": "stddev: 0.0002656567696079249",
            "extra": "mean: 4.9628502169313 msec\nrounds: 189"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 265.363636240469,
            "unit": "iter/sec",
            "range": "stddev: 0.0006078172291023004",
            "extra": "mean: 3.7684138421053786 msec\nrounds: 171"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 220.10960726509407,
            "unit": "iter/sec",
            "range": "stddev: 0.0006163334670311597",
            "extra": "mean: 4.5431910602413055 msec\nrounds: 166"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 193.42950041343434,
            "unit": "iter/sec",
            "range": "stddev: 0.00037037682099474604",
            "extra": "mean: 5.169842231214006 msec\nrounds: 173"
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
          "id": "eaf794db73bc2a0db43f8b96b9412866ba4299b9",
          "message": "test(client): use dynamic __version__ and configure uv.lock for release-please",
          "timestamp": "2026-11-02T07:34:16+03:00",
          "tree_id": "1e15f100ab7c1af7aa424fa27680f5ebfeb9d72d",
          "url": "https://github.com/stormsia/maily/commit/eaf794db73bc2a0db43f8b96b9412866ba4299b9"
        },
        "date": 1793594105446,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 76590.0690391453,
            "unit": "iter/sec",
            "range": "stddev: 0.000003180903337933185",
            "extra": "mean: 13.05652302635866 usec\nrounds: 608"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 76495.31695328343,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021432299344898176",
            "extra": "mean: 13.072695686857687 usec\nrounds: 17551"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 83753.89297129099,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022260526410466908",
            "extra": "mean: 11.93974350950801 usec\nrounds: 24921"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 55283.55425018522,
            "unit": "iter/sec",
            "range": "stddev: 0.000008150132331825128",
            "extra": "mean: 18.088562024693804 usec\nrounds: 28666"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 550319.786939204,
            "unit": "iter/sec",
            "range": "stddev: 7.144480387356422e-7",
            "extra": "mean: 1.8171252855759557 usec\nrounds: 27138"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 5380.535019975098,
            "unit": "iter/sec",
            "range": "stddev: 0.000008253616767017899",
            "extra": "mean: 185.85512338225206 usec\nrounds: 3477"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 87564.1911827984,
            "unit": "iter/sec",
            "range": "stddev: 0.000001188840261381884",
            "extra": "mean: 11.42019342030359 usec\nrounds: 44075"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 105032.01472787278,
            "unit": "iter/sec",
            "range": "stddev: 0.000009634798223702319",
            "extra": "mean: 9.520906578731235 usec\nrounds: 42303"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 218862.0288510075,
            "unit": "iter/sec",
            "range": "stddev: 0.000003966666441617912",
            "extra": "mean: 4.569088595449145 usec\nrounds: 9391"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1369132.0457890707,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014594929353997854",
            "extra": "mean: 730.3897407672398 nsec\nrounds: 28891"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 271.54869640190503,
            "unit": "iter/sec",
            "range": "stddev: 0.0009873429684649367",
            "extra": "mean: 3.682580742424012 msec\nrounds: 132"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 168.2472865099754,
            "unit": "iter/sec",
            "range": "stddev: 0.0015928633163489981",
            "extra": "mean: 5.943632261437452 msec\nrounds: 153"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 252.5231549676085,
            "unit": "iter/sec",
            "range": "stddev: 0.0008074656425514209",
            "extra": "mean: 3.9600328933331737 msec\nrounds: 150"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 200.6942825397621,
            "unit": "iter/sec",
            "range": "stddev: 0.00191925754815273",
            "extra": "mean: 4.98270298159529 msec\nrounds: 163"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 203.80562018711015,
            "unit": "iter/sec",
            "range": "stddev: 0.00042429378495601003",
            "extra": "mean: 4.9066360342856035 msec\nrounds: 175"
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
          "id": "098aa43b21176afe2f288a3c864a2181f41f6e68",
          "message": "fix(ci): rename shadowed lines variable in lint_pr_commits to pass mypy",
          "timestamp": "2026-11-02T07:38:34+03:00",
          "tree_id": "be85229043d9a6ec531232496eb9aa6e61449eba",
          "url": "https://github.com/stormsia/maily/commit/098aa43b21176afe2f288a3c864a2181f41f6e68"
        },
        "date": 1793594345209,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 118882.76268098019,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019779295979230146",
            "extra": "mean: 8.411648395852664 usec\nrounds: 748"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 119925.32707936317,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012275996004753688",
            "extra": "mean: 8.338522181709193 usec\nrounds: 16207"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 142991.0497368087,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012231223112586397",
            "extra": "mean: 6.993444707487733 usec\nrounds: 29145"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 96390.2485732778,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014327521909967607",
            "extra": "mean: 10.374493424402573 usec\nrounds: 33229"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 829996.9379871159,
            "unit": "iter/sec",
            "range": "stddev: 2.4230391463067527e-7",
            "extra": "mean: 1.2048237219105535 usec\nrounds: 27814"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 8634.970530264814,
            "unit": "iter/sec",
            "range": "stddev: 0.000004282484397631831",
            "extra": "mean: 115.80815435270887 usec\nrounds: 4859"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 151201.9361266573,
            "unit": "iter/sec",
            "range": "stddev: 7.35602440093107e-7",
            "extra": "mean: 6.613671925221448 usec\nrounds: 56606"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 189510.69234031183,
            "unit": "iter/sec",
            "range": "stddev: 6.478071271972127e-7",
            "extra": "mean: 5.276747119915854 usec\nrounds: 59720"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 384026.5430866813,
            "unit": "iter/sec",
            "range": "stddev: 4.1485855871943856e-7",
            "extra": "mean: 2.603986672281356 usec\nrounds: 23785"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 2175100.4960712497,
            "unit": "iter/sec",
            "range": "stddev: 2.5141770630099104e-7",
            "extra": "mean: 459.74887220440553 nsec\nrounds: 28595"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 593.3810243110979,
            "unit": "iter/sec",
            "range": "stddev: 0.0005083399104474835",
            "extra": "mean: 1.6852578006871346 msec\nrounds: 291"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 365.8132414924654,
            "unit": "iter/sec",
            "range": "stddev: 0.00036527311389805635",
            "extra": "mean: 2.733635326922951 msec\nrounds: 312"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 542.506787268523,
            "unit": "iter/sec",
            "range": "stddev: 0.0002870765385079354",
            "extra": "mean: 1.8432949107142373 msec\nrounds: 224"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 435.5494897013304,
            "unit": "iter/sec",
            "range": "stddev: 0.00043539639316043905",
            "extra": "mean: 2.2959503423726444 msec\nrounds: 295"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 342.44149994397105,
            "unit": "iter/sec",
            "range": "stddev: 0.0002263497616794452",
            "extra": "mean: 2.9202068095240095 msec\nrounds: 273"
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
          "id": "cd848c9c6cef7a8f4652903cd60aabd009ad6484",
          "message": "fix(ci): exclude unreleased container URL in lychee, ignore changelog in typos, and whitelist pages in zizmor",
          "timestamp": "2026-11-02T07:45:58+03:00",
          "tree_id": "c7cbcffd511e62595575cb26a0254a97b089a65a",
          "url": "https://github.com/stormsia/maily/commit/cd848c9c6cef7a8f4652903cd60aabd009ad6484"
        },
        "date": 1793594795360,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 62931.397420966394,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036498320828302955",
            "extra": "mean: 15.890319315662252 usec\nrounds: 761"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59050.22060473297,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029888936826537223",
            "extra": "mean: 16.93473774964777 usec\nrounds: 15428"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73568.88408735802,
            "unit": "iter/sec",
            "range": "stddev: 0.000002259529557379624",
            "extra": "mean: 13.592703116341529 usec\nrounds: 30581"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 49041.114002130525,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029515775115191606",
            "extra": "mean: 20.391053921747297 usec\nrounds: 34550"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 466664.3247239391,
            "unit": "iter/sec",
            "range": "stddev: 5.979478576475298e-7",
            "extra": "mean: 2.142867896729758 usec\nrounds: 31271"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4728.442726604856,
            "unit": "iter/sec",
            "range": "stddev: 0.000011353568139530118",
            "extra": "mean: 211.4861187539488 usec\nrounds: 3402"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 96899.60233784061,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012839399246626348",
            "extra": "mean: 10.31995979213102 usec\nrounds: 47329"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 102288.13847841494,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014555256401127203",
            "extra": "mean: 9.776304612396697 usec\nrounds: 48478"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 211578.06623637333,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010597860631594505",
            "extra": "mean: 4.726387842503523 usec\nrounds: 25219"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1205706.3946724145,
            "unit": "iter/sec",
            "range": "stddev: 4.1612815810094827e-7",
            "extra": "mean: 829.3893143626362 nsec\nrounds: 38126"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 296.38937533984375,
            "unit": "iter/sec",
            "range": "stddev: 0.0005867666907134413",
            "extra": "mean: 3.37394010447705 msec\nrounds: 201"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 196.1625657489736,
            "unit": "iter/sec",
            "range": "stddev: 0.000526856793950344",
            "extra": "mean: 5.097812603448945 msec\nrounds: 174"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 271.4853282002389,
            "unit": "iter/sec",
            "range": "stddev: 0.00043869016708890704",
            "extra": "mean: 3.6834403045988253 msec\nrounds: 174"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 230.95571044456594,
            "unit": "iter/sec",
            "range": "stddev: 0.000521378249150866",
            "extra": "mean: 4.329834486772824 msec\nrounds: 189"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 188.36829482597756,
            "unit": "iter/sec",
            "range": "stddev: 0.000505935002545837",
            "extra": "mean: 5.308749017045791 msec\nrounds: 176"
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
          "id": "44cea5d455498f662b55475fe35f89946e25b2dc",
          "message": "fix(release): add concurrency group to release-please to avoid race conditions",
          "timestamp": "2026-11-02T07:49:43+03:00",
          "tree_id": "45b72a3078e1986c1331a2f504a9c8bc22c7587c",
          "url": "https://github.com/stormsia/maily/commit/44cea5d455498f662b55475fe35f89946e25b2dc"
        },
        "date": 1793595017860,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 89208.2499511131,
            "unit": "iter/sec",
            "range": "stddev: 0.000001537593634088541",
            "extra": "mean: 11.209725564037056 usec\nrounds: 798"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 86897.51418866223,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013678044125550003",
            "extra": "mean: 11.507809047666324 usec\nrounds: 20602"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 104990.8372045119,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014720061202858861",
            "extra": "mean: 9.52464068890219 usec\nrounds: 32284"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 70250.10903529737,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018759863119050821",
            "extra": "mean: 14.234853350868782 usec\nrounds: 40198"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 576214.1565264722,
            "unit": "iter/sec",
            "range": "stddev: 3.855085682513003e-7",
            "extra": "mean: 1.7354658657263626 usec\nrounds: 30131"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 6148.019153843843,
            "unit": "iter/sec",
            "range": "stddev: 0.000006072425558223048",
            "extra": "mean: 162.6540150537403 usec\nrounds: 3720"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 126071.10054841552,
            "unit": "iter/sec",
            "range": "stddev: 8.097252084483077e-7",
            "extra": "mean: 7.9320319696579995 usec\nrounds: 56929"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 135625.504981893,
            "unit": "iter/sec",
            "range": "stddev: 8.888114921110846e-7",
            "extra": "mean: 7.373244436092662 usec\nrounds: 53425"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 272148.6825407118,
            "unit": "iter/sec",
            "range": "stddev: 6.027132251514151e-7",
            "extra": "mean: 3.674462028124667 usec\nrounds: 24821"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1686853.6931505483,
            "unit": "iter/sec",
            "range": "stddev: 3.90181998703675e-7",
            "extra": "mean: 592.819640529875 nsec\nrounds: 31659"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 447.7153519691607,
            "unit": "iter/sec",
            "range": "stddev: 0.0003626841873647787",
            "extra": "mean: 2.2335620067566535 msec\nrounds: 296"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 297.77575119128807,
            "unit": "iter/sec",
            "range": "stddev: 0.00029627759180388347",
            "extra": "mean: 3.3582318103451287 msec\nrounds: 232"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 417.78936551864706,
            "unit": "iter/sec",
            "range": "stddev: 0.00030783810010823084",
            "extra": "mean: 2.3935506322871385 msec\nrounds: 223"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 342.0898321056828,
            "unit": "iter/sec",
            "range": "stddev: 0.00043737090436380706",
            "extra": "mean: 2.9232087777781928 msec\nrounds: 261"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 257.18088412914597,
            "unit": "iter/sec",
            "range": "stddev: 0.00022831949270806092",
            "extra": "mean: 3.888313874439594 msec\nrounds: 223"
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
          "id": "723acc9015897fc22589c1bb69fa19f59e541088",
          "message": "Merge pull request #29 from stormsia/release-please--branches--main--components--maily\n\nchore(main): release 0.4.0",
          "timestamp": "2026-11-02T08:07:39+03:00",
          "tree_id": "626f3b098df6deeec0c7a7a65abbe43818523ec7",
          "url": "https://github.com/stormsia/maily/commit/723acc9015897fc22589c1bb69fa19f59e541088"
        },
        "date": 1793596099355,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 103736.2835483961,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021402674874870875",
            "extra": "mean: 9.639828667406134 usec\nrounds: 893"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 100829.20037639332,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017899412809367488",
            "extra": "mean: 9.917761881151698 usec\nrounds: 24177"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 118177.994546367,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015433003959595782",
            "extra": "mean: 8.46181223364432 usec\nrounds: 27923"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 79558.65874164582,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018458615564155383",
            "extra": "mean: 12.569342115826034 usec\nrounds: 44900"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 731552.5109745706,
            "unit": "iter/sec",
            "range": "stddev: 3.595179842863713e-7",
            "extra": "mean: 1.3669558712440273 usec\nrounds: 29074"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 7355.192092423968,
            "unit": "iter/sec",
            "range": "stddev: 0.000005001108993916929",
            "extra": "mean: 135.95837979949223 usec\nrounds: 4089"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 119740.0820252494,
            "unit": "iter/sec",
            "range": "stddev: 9.552252884652693e-7",
            "extra": "mean: 8.351422373246175 usec\nrounds: 52527"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 152551.79419487866,
            "unit": "iter/sec",
            "range": "stddev: 8.849211825310251e-7",
            "extra": "mean: 6.555150696703974 usec\nrounds: 53465"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 334407.8990038928,
            "unit": "iter/sec",
            "range": "stddev: 6.119248440625021e-7",
            "extra": "mean: 2.9903599854510587 usec\nrounds: 27465"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1690761.5411369766,
            "unit": "iter/sec",
            "range": "stddev: 3.256633090640305e-7",
            "extra": "mean: 591.4494597076864 nsec\nrounds: 27671"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 463.7673051954578,
            "unit": "iter/sec",
            "range": "stddev: 0.0004730499235082967",
            "extra": "mean: 2.1562537695030985 msec\nrounds: 282"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 298.8475832379733,
            "unit": "iter/sec",
            "range": "stddev: 0.00048298282027904604",
            "extra": "mean: 3.34618734126987 msec\nrounds: 252"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 412.7098511188716,
            "unit": "iter/sec",
            "range": "stddev: 0.00039727703527565157",
            "extra": "mean: 2.423009766519901 msec\nrounds: 227"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 361.6528694195646,
            "unit": "iter/sec",
            "range": "stddev: 0.00026299496384508047",
            "extra": "mean: 2.7650824438499595 msec\nrounds: 187"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 271.95951532949374,
            "unit": "iter/sec",
            "range": "stddev: 0.00004515105598090356",
            "extra": "mean: 3.6770178781516267 msec\nrounds: 238"
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
          "id": "a6830dbb818f5a995290e2ae321974e3c935bf57",
          "message": "fix(ci): grant actions write and provide GH_REPO to release-please CD dispatch",
          "timestamp": "2026-11-02T08:12:58+03:00",
          "tree_id": "6aa552577ab1ddd8cbda89f7d4b7778ce869ce06",
          "url": "https://github.com/stormsia/maily/commit/a6830dbb818f5a995290e2ae321974e3c935bf57"
        },
        "date": 1793596418401,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 97828.20374755509,
            "unit": "iter/sec",
            "range": "stddev: 0.000002709895708268452",
            "extra": "mean: 10.222001035411957 usec\nrounds: 966"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 93379.6768624198,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024065341508271194",
            "extra": "mean: 10.708968306597827 usec\nrounds: 25021"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 104870.72493750574,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018399596065323405",
            "extra": "mean: 9.535549607346733 usec\nrounds: 45336"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 69551.97832416216,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024056174784186697",
            "extra": "mean: 14.37773624984874 usec\nrounds: 48254"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 644059.7816949032,
            "unit": "iter/sec",
            "range": "stddev: 4.0796642594022803e-7",
            "extra": "mean: 1.552650900462077 usec\nrounds: 45921"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 6619.1155884470345,
            "unit": "iter/sec",
            "range": "stddev: 0.00001045643282076713",
            "extra": "mean: 151.07758531145674 usec\nrounds: 4929"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 108804.71634624369,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012735291768337452",
            "extra": "mean: 9.190778061658202 usec\nrounds: 56358"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 140165.4567994971,
            "unit": "iter/sec",
            "range": "stddev: 8.717296515842706e-7",
            "extra": "mean: 7.134425434295648 usec\nrounds: 57104"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 304982.88714866113,
            "unit": "iter/sec",
            "range": "stddev: 6.330187501434299e-7",
            "extra": "mean: 3.278872494614949 usec\nrounds: 27191"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1803963.6416792634,
            "unit": "iter/sec",
            "range": "stddev: 4.4289757453251555e-7",
            "extra": "mean: 554.3348972760481 nsec\nrounds: 24724"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 350.4220823322607,
            "unit": "iter/sec",
            "range": "stddev: 0.0004050454935233849",
            "extra": "mean: 2.853701437262242 msec\nrounds: 263"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 241.52537459576314,
            "unit": "iter/sec",
            "range": "stddev: 0.0006234301423177252",
            "extra": "mean: 4.140351719456735 msec\nrounds: 221"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 323.7930331370973,
            "unit": "iter/sec",
            "range": "stddev: 0.0006312043882351719",
            "extra": "mean: 3.0883925769230176 msec\nrounds: 182"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 288.08510729297416,
            "unit": "iter/sec",
            "range": "stddev: 0.0004980008140965543",
            "extra": "mean: 3.4711964439835796 msec\nrounds: 241"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 249.75588977460424,
            "unit": "iter/sec",
            "range": "stddev: 0.0000584484156936534",
            "extra": "mean: 4.003909581081208 msec\nrounds: 222"
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
          "id": "1fc522c78fd462bbbb124fc97dc055c4d48350c0",
          "message": "fix(db): bundle alembic migrations inside package to fix standalone pip install",
          "timestamp": "2026-11-02T08:30:53+03:00",
          "tree_id": "5494e249e2836cd038c266cecb60a1f72ab1b8f1",
          "url": "https://github.com/stormsia/maily/commit/1fc522c78fd462bbbb124fc97dc055c4d48350c0"
        },
        "date": 1793597501680,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 79562.9907479404,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028395696784421895",
            "extra": "mean: 12.568657746514969 usec\nrounds: 710"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 78500.77243242683,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020569540623525436",
            "extra": "mean: 12.738728155328612 usec\nrounds: 18643"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 82802.43724601246,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025480723407673198",
            "extra": "mean: 12.076939197199263 usec\nrounds: 24489"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 55702.44443933205,
            "unit": "iter/sec",
            "range": "stddev: 0.000002626120657569494",
            "extra": "mean: 17.952533503069933 usec\nrounds: 34564"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 538491.2904964928,
            "unit": "iter/sec",
            "range": "stddev: 4.340297406861574e-7",
            "extra": "mean: 1.8570402486509912 usec\nrounds: 28473"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 5596.1420724415375,
            "unit": "iter/sec",
            "range": "stddev: 0.0000068026806534474055",
            "extra": "mean: 178.69453402988935 usec\nrounds: 3541"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 91448.6650583847,
            "unit": "iter/sec",
            "range": "stddev: 0.000001018369751403592",
            "extra": "mean: 10.935096749215067 usec\nrounds: 29685"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 114277.6761701428,
            "unit": "iter/sec",
            "range": "stddev: 0.000001523950112907589",
            "extra": "mean: 8.75061546151101 usec\nrounds: 49025"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 248467.31055588872,
            "unit": "iter/sec",
            "range": "stddev: 7.190385447174841e-7",
            "extra": "mean: 4.024674303282508 usec\nrounds: 22785"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1511929.7918432022,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010915255634675852",
            "extra": "mean: 661.4063730967919 nsec\nrounds: 31225"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 295.0336240473179,
            "unit": "iter/sec",
            "range": "stddev: 0.0004431980053674586",
            "extra": "mean: 3.389444180232211 msec\nrounds: 172"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 211.6112466510578,
            "unit": "iter/sec",
            "range": "stddev: 0.0005618386081049778",
            "extra": "mean: 4.725646749999908 msec\nrounds: 180"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 287.68736216950555,
            "unit": "iter/sec",
            "range": "stddev: 0.00042372863957606887",
            "extra": "mean: 3.4759955823530384 msec\nrounds: 170"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 252.22011388864235,
            "unit": "iter/sec",
            "range": "stddev: 0.0006333286113969917",
            "extra": "mean: 3.9647908510639636 msec\nrounds: 188"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 208.30564650282315,
            "unit": "iter/sec",
            "range": "stddev: 0.00024943928701363184",
            "extra": "mean: 4.80063798936169 msec\nrounds: 188"
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
          "id": "d0c0aa7f0d83d4b7d3b180614c26b7c39b095164",
          "message": "Merge pull request #30 from stormsia/release-please--branches--main--components--maily\n\nchore(main): release 0.4.1",
          "timestamp": "2026-11-02T08:34:14+03:00",
          "tree_id": "65b1c9ec97362e8271424e4fb575a108a1f14697",
          "url": "https://github.com/stormsia/maily/commit/d0c0aa7f0d83d4b7d3b180614c26b7c39b095164"
        },
        "date": 1793597692148,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 63321.28489317152,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032502006410897113",
            "extra": "mean: 15.792478021996654 usec\nrounds: 728"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59949.660727834016,
            "unit": "iter/sec",
            "range": "stddev: 0.000002875633331475423",
            "extra": "mean: 16.680661539352304 usec\nrounds: 17423"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 75444.16937213304,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022453439038624265",
            "extra": "mean: 13.254834778118347 usec\nrounds: 27109"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 50166.86282392353,
            "unit": "iter/sec",
            "range": "stddev: 0.0000027544629442810454",
            "extra": "mean: 19.933476875159926 usec\nrounds: 40411"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 468846.2879635782,
            "unit": "iter/sec",
            "range": "stddev: 5.521155794718837e-7",
            "extra": "mean: 2.132895206110033 usec\nrounds: 31290"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4765.464979693318,
            "unit": "iter/sec",
            "range": "stddev: 0.000008550502252787353",
            "extra": "mean: 209.8431116923988 usec\nrounds: 3250"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 97651.72291079827,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011402652994252592",
            "extra": "mean: 10.24047472171554 usec\nrounds: 51744"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 103241.94844288124,
            "unit": "iter/sec",
            "range": "stddev: 0.000001187013488660161",
            "extra": "mean: 9.685985348806657 usec\nrounds: 49757"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 217120.3786139532,
            "unit": "iter/sec",
            "range": "stddev: 9.569149419900525e-7",
            "extra": "mean: 4.605739941979519 usec\nrounds: 24110"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1230711.2634215567,
            "unit": "iter/sec",
            "range": "stddev: 4.2807149050541715e-7",
            "extra": "mean: 812.5382693092888 nsec\nrounds: 36008"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 311.4290586595779,
            "unit": "iter/sec",
            "range": "stddev: 0.00040166452240887715",
            "extra": "mean: 3.2110041506855556 msec\nrounds: 219"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 198.1869522889034,
            "unit": "iter/sec",
            "range": "stddev: 0.0004801066985132392",
            "extra": "mean: 5.04574084444403 msec\nrounds: 180"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 282.2976518210736,
            "unit": "iter/sec",
            "range": "stddev: 0.0003751857627345125",
            "extra": "mean: 3.542360319149313 msec\nrounds: 141"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 242.62962203512927,
            "unit": "iter/sec",
            "range": "stddev: 0.000644519318869306",
            "extra": "mean: 4.121508295698595 msec\nrounds: 186"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 195.77481686631856,
            "unit": "iter/sec",
            "range": "stddev: 0.00020062791634192895",
            "extra": "mean: 5.107909260274434 msec\nrounds: 146"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "name": "stormsia",
            "username": "stormsia",
            "email": "157276367+stormsia@users.noreply.github.com"
          },
          "committer": {
            "name": "GitHub",
            "username": "web-flow",
            "email": "noreply@github.com"
          },
          "id": "d0c0aa7f0d83d4b7d3b180614c26b7c39b095164",
          "message": "Merge pull request #30 from stormsia/release-please--branches--main--components--maily\n\nchore(main): release 0.4.1",
          "timestamp": "2026-11-02T05:34:14Z",
          "url": "https://github.com/stormsia/maily/commit/d0c0aa7f0d83d4b7d3b180614c26b7c39b095164"
        },
        "date": 1793610269055,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 62920.180165565,
            "unit": "iter/sec",
            "range": "stddev: 0.000003890514280475858",
            "extra": "mean: 15.893152202817127 usec\nrounds: 749"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 59871.592197779224,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028718804910749074",
            "extra": "mean: 16.70241200027903 usec\nrounds: 12233"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 73258.68055534162,
            "unit": "iter/sec",
            "range": "stddev: 0.000002247144262546287",
            "extra": "mean: 13.650259497160512 usec\nrounds: 27087"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 48974.62472800119,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028734036315938802",
            "extra": "mean: 20.41873736764441 usec\nrounds: 34950"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 462942.42492575845,
            "unit": "iter/sec",
            "range": "stddev: 5.495791215154196e-7",
            "extra": "mean: 2.160095826517453 usec\nrounds: 33665"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4669.592984087944,
            "unit": "iter/sec",
            "range": "stddev: 0.000009132351527695048",
            "extra": "mean: 214.15142677479375 usec\nrounds: 3578"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 96929.93417460738,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014094389992830048",
            "extra": "mean: 10.316730414761478 usec\nrounds: 51212"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 102747.2498917203,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012869272416796588",
            "extra": "mean: 9.732620591342787 usec\nrounds: 48059"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 212034.85943665047,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013466095794932962",
            "extra": "mean: 4.716205640227612 usec\nrounds: 26240"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1217135.6019643736,
            "unit": "iter/sec",
            "range": "stddev: 4.057281458209959e-7",
            "extra": "mean: 821.6011415540457 nsec\nrounds: 39420"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 304.2427036188226,
            "unit": "iter/sec",
            "range": "stddev: 0.00039556134584288634",
            "extra": "mean: 3.2868495714292387 msec\nrounds: 217"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 209.36418359488758,
            "unit": "iter/sec",
            "range": "stddev: 0.0005205106376354805",
            "extra": "mean: 4.776366152173217 msec\nrounds: 184"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 284.9832910634782,
            "unit": "iter/sec",
            "range": "stddev: 0.0004188977766857019",
            "extra": "mean: 3.5089776536311263 msec\nrounds: 179"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 241.51234615014656,
            "unit": "iter/sec",
            "range": "stddev: 0.0003417420145690036",
            "extra": "mean: 4.140575071794909 msec\nrounds: 195"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 191.44913938258463,
            "unit": "iter/sec",
            "range": "stddev: 0.0005067213879612444",
            "extra": "mean: 5.223319379888348 msec\nrounds: 179"
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
          "id": "ec2b44bc285a31c07a5b30ae0c9702c0a70d39e6",
          "message": "feat(dashboard): add github links, version check and manual gmail oauth callback",
          "timestamp": "2026-11-02T20:10:42+03:00",
          "tree_id": "b02d2a1373823bd52329ae472c70eb0b1bb1267f",
          "url": "https://github.com/stormsia/maily/commit/ec2b44bc285a31c07a5b30ae0c9702c0a70d39e6"
        },
        "date": 1793639496150,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 69294.48591703294,
            "unit": "iter/sec",
            "range": "stddev: 0.00000222795320343151",
            "extra": "mean: 14.431162693050515 usec\nrounds: 713"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 66925.83731671628,
            "unit": "iter/sec",
            "range": "stddev: 0.000001490942793980834",
            "extra": "mean: 14.941912422666496 usec\nrounds: 13097"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 81008.46880452771,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019428123723704967",
            "extra": "mean: 12.344388367751845 usec\nrounds: 15457"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 52650.41601762658,
            "unit": "iter/sec",
            "range": "stddev: 0.0000050081944365866104",
            "extra": "mean: 18.99320225058079 usec\nrounds: 36257"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 433575.3462351558,
            "unit": "iter/sec",
            "range": "stddev: 4.912844171556177e-7",
            "extra": "mean: 2.306404200984333 usec\nrounds: 28993"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4690.931845681482,
            "unit": "iter/sec",
            "range": "stddev: 0.0000078234843036405",
            "extra": "mean: 213.1772604883633 usec\nrounds: 3194"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 97765.90865526952,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011213959748656164",
            "extra": "mean: 10.228514353874424 usec\nrounds: 46120"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 106106.11378874685,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010588479541062692",
            "extra": "mean: 9.42452761950137 usec\nrounds: 37908"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 206522.42317979393,
            "unit": "iter/sec",
            "range": "stddev: 0.000006598699696740246",
            "extra": "mean: 4.8420892250011125 usec\nrounds: 22348"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1310053.0263230847,
            "unit": "iter/sec",
            "range": "stddev: 7.63176605686102e-7",
            "extra": "mean: 763.3278805566306 nsec\nrounds: 30810"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 360.50838481287565,
            "unit": "iter/sec",
            "range": "stddev: 0.00046879607996396736",
            "extra": "mean: 2.773860587234488 msec\nrounds: 235"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 233.18800664226563,
            "unit": "iter/sec",
            "range": "stddev: 0.0003451195849326903",
            "extra": "mean: 4.288385214999941 msec\nrounds: 200"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 334.6635098301639,
            "unit": "iter/sec",
            "range": "stddev: 0.00038651290220023394",
            "extra": "mean: 2.988075994623624 msec\nrounds: 186"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 268.41970246679205,
            "unit": "iter/sec",
            "range": "stddev: 0.000349622948885437",
            "extra": "mean: 3.7255089354840356 msec\nrounds: 217"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 201.4745293756051,
            "unit": "iter/sec",
            "range": "stddev: 0.0002724788757892175",
            "extra": "mean: 4.963406556149434 msec\nrounds: 187"
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
          "id": "1f50ac1b3c1ed13283cd0480023ed54656826560",
          "message": "feat(docker): enhance Docker setup with pre-built image instructions and new compose file",
          "timestamp": "2026-11-02T20:17:38+03:00",
          "tree_id": "0757e731be4a2106ef071c8c9363a3d100fcd2fb",
          "url": "https://github.com/stormsia/maily/commit/1f50ac1b3c1ed13283cd0480023ed54656826560"
        },
        "date": 1793639903496,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 62011.331353801,
            "unit": "iter/sec",
            "range": "stddev: 0.000003899527655619611",
            "extra": "mean: 16.126084993959815 usec\nrounds: 753"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 60118.09501039187,
            "unit": "iter/sec",
            "range": "stddev: 0.0000032171755377751173",
            "extra": "mean: 16.633926937091775 usec\nrounds: 17177"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 75203.40583839292,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022245309846666596",
            "extra": "mean: 13.297270101688385 usec\nrounds: 29015"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 48737.46608862186,
            "unit": "iter/sec",
            "range": "stddev: 0.000002948763471638305",
            "extra": "mean: 20.518095835791872 usec\nrounds: 35060"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 445293.09290152526,
            "unit": "iter/sec",
            "range": "stddev: 6.858189079172362e-7",
            "extra": "mean: 2.2457119051274974 usec\nrounds: 28324"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4760.739459773472,
            "unit": "iter/sec",
            "range": "stddev: 0.000009966862066007438",
            "extra": "mean: 210.0514024028491 usec\nrounds: 3330"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 96850.81026741971,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011449736482981573",
            "extra": "mean: 10.32515884212893 usec\nrounds: 49609"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 101983.16846996667,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016198736297223924",
            "extra": "mean: 9.805539629752658 usec\nrounds: 51691"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 215408.77095294397,
            "unit": "iter/sec",
            "range": "stddev: 9.251114287251504e-7",
            "extra": "mean: 4.642336500858871 usec\nrounds: 24098"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1192003.679341708,
            "unit": "iter/sec",
            "range": "stddev: 3.65029527717342e-7",
            "extra": "mean: 838.9235849945165 nsec\nrounds: 20899"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 299.2149443103314,
            "unit": "iter/sec",
            "range": "stddev: 0.0005401569872805727",
            "extra": "mean: 3.3420790606061708 msec\nrounds: 198"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 207.50599116243103,
            "unit": "iter/sec",
            "range": "stddev: 0.0004933770571454399",
            "extra": "mean: 4.819137965116499 msec\nrounds: 172"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 266.8084380806519,
            "unit": "iter/sec",
            "range": "stddev: 0.0005430107871039213",
            "extra": "mean: 3.748007398842896 msec\nrounds: 173"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 236.85811247869736,
            "unit": "iter/sec",
            "range": "stddev: 0.0005245473928369762",
            "extra": "mean: 4.221936878307001 msec\nrounds: 189"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 195.95621921627847,
            "unit": "iter/sec",
            "range": "stddev: 0.00007258646234201766",
            "extra": "mean: 5.103180720670528 msec\nrounds: 179"
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
          "id": "df4d6073f9636bb4f6cc0ce645346636d32b8f85",
          "message": "fix(ci): enable oidc tokenless upload for codecov coverage",
          "timestamp": "2026-11-02T20:24:59+03:00",
          "tree_id": "c1dd3373be8c4f08eddfe7425cd9b42f0498617f",
          "url": "https://github.com/stormsia/maily/commit/df4d6073f9636bb4f6cc0ce645346636d32b8f85"
        },
        "date": 1793640341754,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 70227.63697221882,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023607839509502095",
            "extra": "mean: 14.239408345685725 usec\nrounds: 671"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 67375.82973444296,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017134128653756743",
            "extra": "mean: 14.842117773412646 usec\nrounds: 15360"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 80660.19355288296,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020031270946601006",
            "extra": "mean: 12.397689070066184 usec\nrounds: 25636"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 52269.486778511826,
            "unit": "iter/sec",
            "range": "stddev: 0.000005718122322950746",
            "extra": "mean: 19.1316207912549 usec\nrounds: 27829"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 434065.7978328927,
            "unit": "iter/sec",
            "range": "stddev: 5.325483696196623e-7",
            "extra": "mean: 2.3037981914091783 usec\nrounds: 24107"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 4789.957956443447,
            "unit": "iter/sec",
            "range": "stddev: 0.000006372826542237611",
            "extra": "mean: 208.77009967379794 usec\nrounds: 2759"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 97699.79972433423,
            "unit": "iter/sec",
            "range": "stddev: 0.000001105210025880317",
            "extra": "mean: 10.235435515953556 usec\nrounds: 43755"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 105106.89916643198,
            "unit": "iter/sec",
            "range": "stddev: 0.000001142910926622369",
            "extra": "mean: 9.514123315697342 usec\nrounds: 41041"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 202232.9856364403,
            "unit": "iter/sec",
            "range": "stddev: 8.148366396848259e-7",
            "extra": "mean: 4.9447917551775005 usec\nrounds: 20716"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 1296720.6765126968,
            "unit": "iter/sec",
            "range": "stddev: 4.3117735941034773e-7",
            "extra": "mean: 771.1761045480704 nsec\nrounds: 28926"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 299.82856181259916,
            "unit": "iter/sec",
            "range": "stddev: 0.0006968050975619666",
            "extra": "mean: 3.3352392912621402 msec\nrounds: 206"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 195.38390707789782,
            "unit": "iter/sec",
            "range": "stddev: 0.0006570630931055803",
            "extra": "mean: 5.118128790419309 msec\nrounds: 167"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 264.0830488900205,
            "unit": "iter/sec",
            "range": "stddev: 0.0005754932666026877",
            "extra": "mean: 3.7866875750001583 msec\nrounds: 160"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 238.9821733127365,
            "unit": "iter/sec",
            "range": "stddev: 0.0002586597377205275",
            "extra": "mean: 4.184412528090041 msec\nrounds: 178"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 185.96426372290702,
            "unit": "iter/sec",
            "range": "stddev: 0.00008521798504348071",
            "extra": "mean: 5.377377244318476 msec\nrounds: 176"
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
          "id": "04ac7f359ce8955f338508bba8a6acdb85cc6678",
          "message": "feat(client): standalone maily-client packaging and publishing setup",
          "timestamp": "2026-11-02T20:46:41+03:00",
          "tree_id": "c201c510afbfb5e6236024a9f1f39621a5b58e00",
          "url": "https://github.com/stormsia/maily/commit/04ac7f359ce8955f338508bba8a6acdb85cc6678"
        },
        "date": 1793641658994,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_encrypt_1kb",
            "value": 120967.5729824484,
            "unit": "iter/sec",
            "range": "stddev: 0.000001352417403675186",
            "extra": "mean: 8.266678212557785 usec\nrounds: 895"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_crypto_decrypt_1kb",
            "value": 121066.36235886697,
            "unit": "iter/sec",
            "range": "stddev: 7.825920003083562e-7",
            "extra": "mean: 8.259932656073229 usec\nrounds: 19883"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_string",
            "value": 143595.46641006274,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013244802094092218",
            "extra": "mean: 6.964008161262694 usec\nrounds: 22668"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_random_password",
            "value": 97552.21194721485,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015888237381602534",
            "extra": "mean: 10.25092081501029 usec\nrounds: 46183"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_message_detail_parse",
            "value": 829091.0319337207,
            "unit": "iter/sec",
            "range": "stddev: 7.011033663552035e-7",
            "extra": "mean: 1.206140172168624 usec\nrounds: 31019"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_pydantic_batch_messages_serialize",
            "value": 8601.236276052916,
            "unit": "iter/sec",
            "range": "stddev: 0.000004537592395404814",
            "extra": "mean: 116.26235670145981 usec\nrounds: 4693"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_verification_code",
            "value": 143486.07072848565,
            "unit": "iter/sec",
            "range": "stddev: 6.035814263223184e-7",
            "extra": "mean: 6.96931761336102 usec\nrounds: 61260"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_extract_confirmation_url",
            "value": 187260.5167668628,
            "unit": "iter/sec",
            "range": "stddev: 9.21580320887647e-7",
            "extra": "mean: 5.34015401252464 usec\nrounds: 62878"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_parse_scope",
            "value": 374303.4837063957,
            "unit": "iter/sec",
            "range": "stddev: 6.401578681522792e-7",
            "extra": "mean: 2.671628888136135 usec\nrounds: 25076"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_authz_secret_sha256",
            "value": 2109584.5821016273,
            "unit": "iter/sec",
            "range": "stddev: 2.636178815503491e-7",
            "extra": "mean: 474.02697596688535 nsec\nrounds: 29656"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_health_endpoint",
            "value": 622.9495657644419,
            "unit": "iter/sec",
            "range": "stddev: 0.0002075329966515156",
            "extra": "mean: 1.6052663890581047 msec\nrounds: 329"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_domain_cache_settings",
            "value": 395.8954454832732,
            "unit": "iter/sec",
            "range": "stddev: 0.0002931102104513021",
            "extra": "mean: 2.5259194350652123 msec\nrounds: 308"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_mailboxes_list",
            "value": 542.8619715713027,
            "unit": "iter/sec",
            "range": "stddev: 0.0002734035191224416",
            "extra": "mean: 1.8420888777777542 msec\nrounds: 270"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_admin_keys_list",
            "value": 496.39718209092956,
            "unit": "iter/sec",
            "range": "stddev: 0.0002567605615905859",
            "extra": "mean: 2.014515867692458 msec\nrounds: 325"
          },
          {
            "name": "tests/test_benchmarks.py::test_benchmark_client_init",
            "value": 345.00149908763814,
            "unit": "iter/sec",
            "range": "stddev: 0.00020805150194913862",
            "extra": "mean: 2.8985381299632484 msec\nrounds: 277"
          }
        ]
      }
    ]
  }
}