# Changelog

All notable changes to the **Maily** ecosystem ([`maily-server`](https://pypi.org/project/maily-server/), [`maily-client`](https://pypi.org/project/maily-client/), and [Docker container](https://github.com/stormsia/maily/pkgs/container/maily)) are documented in this file using [Conventional Commits](https://www.conventionalcommits.org/).

> 🚀 **Quick Upgrade Commands:**
> - **Python Client SDK (PyPI):** `pip install -U maily-client`
> - **Python Server Package (PyPI):** `pip install -U maily-server`
> - **Docker Container (GHCR):** `docker pull ghcr.io/stormsia/maily:latest`

## [0.7.0](https://github.com/stormsia/maily/compare/v0.6.0...v0.7.0) (2026-11-03)


### Features

* **docs:** upgrade GitHub Pages documentation portal with dark UI, live simulator, and SEO ([2b0d335](https://github.com/stormsia/maily/commit/2b0d3355895751050b3b27e2683b971925d1763e))


### Bug Fixes

* **docs:** remove simulator widget, fix ReDoc CDN loading, and overhaul benchmark visual analytics ([5400e76](https://github.com/stormsia/maily/commit/5400e7603b4f52f5423c445252fa9d163ef0eee0))
* **docs:** synchronize hero action buttons with portal tabs and harden router accessibility ([b76655e](https://github.com/stormsia/maily/commit/b76655ef6e5c948f48662f89fc7ab8e3b67eef4f))


### Documentation

* redesign README with animated carousel, WebP/AVIF assets, infographics, and SEO optimizations ([1943092](https://github.com/stormsia/maily/commit/1943092833bd4807284e924dd18f935a3853bb12))
* remove workstation guide section from README ([8be7725](https://github.com/stormsia/maily/commit/8be77255dcded7743b87e6d5c13ce558079aacae))

## [0.6.0](https://github.com/stormsia/maily/compare/v0.5.0...v0.6.0) (2026-11-02)


### Features

* **client:** remove legacy client module alias and standardize on maily_client ([ebd954e](https://github.com/stormsia/maily/commit/ebd954e60785b79a4f1232a4c33d90b3967e8463))


### Bug Fixes

* **dashboard:** stop infinite spin on version refresh and sync icons ([4a27b6d](https://github.com/stormsia/maily/commit/4a27b6ddc1b32a8b0ea2fe1d7b79195302e340a7))
* **docker:** specify name for maily_data volume in docker-compose files ([9f0e869](https://github.com/stormsia/maily/commit/9f0e869b49daa3ec697268f2e536258e1416b132))


### Documentation

* standardize api key examples and formatting across documentation and client ([a9b1513](https://github.com/stormsia/maily/commit/a9b15137277eb99014d020f6860c9aca17e6bb47))

## [0.5.0](https://github.com/stormsia/maily/compare/v0.4.1...v0.5.0) (2026-11-02)


### Features

* **client:** standalone maily-client packaging and publishing setup ([04ac7f3](https://github.com/stormsia/maily/commit/04ac7f359ce8955f338508bba8a6acdb85cc6678))
* **dashboard:** add github links, version check and manual gmail oauth callback ([ec2b44b](https://github.com/stormsia/maily/commit/ec2b44bc285a31c07a5b30ae0c9702c0a70d39e6))
* **docker:** enhance Docker setup with pre-built image instructions and new compose file ([1f50ac1](https://github.com/stormsia/maily/commit/1f50ac1b3c1ed13283cd0480023ed54656826560))
* **release:** add static files for version tracking in release process ([7c20cf2](https://github.com/stormsia/maily/commit/7c20cf237f8c81c57a33238bb072b6edbaf67d3c))


### Bug Fixes

* **ci:** enable oidc tokenless upload for codecov coverage ([df4d607](https://github.com/stormsia/maily/commit/df4d6073f9636bb4f6cc0ce645346636d32b8f85))
* **ci:** prevent test hangs with pytest-timeout, mocked api calls and stable concurrency ([2f5c63b](https://github.com/stormsia/maily/commit/2f5c63b61ca5eb297ac2b3c3959f8cc9642969c6))

## [0.4.1](https://github.com/stormsia/maily/compare/v0.4.0...v0.4.1) (2026-11-02)


### Bug Fixes

* **ci:** grant actions write and provide GH_REPO to release-please CD dispatch ([a6830db](https://github.com/stormsia/maily/commit/a6830dbb818f5a995290e2ae321974e3c935bf57))
* **db:** bundle alembic migrations inside package to fix standalone pip install ([1fc522c](https://github.com/stormsia/maily/commit/1fc522c78fd462bbbb124fc97dc055c4d48350c0))

## [0.4.0](https://github.com/stormsia/maily/compare/v0.3.0...v0.4.0) (2026-11-02)


### Features

* add AnonymMailNet provider and integrate with mailbox functionality ([ac7e73e](https://github.com/stormsia/maily/commit/ac7e73e4e01f91caec7885c8660bf83599f738a5))
* add async client, Docker packaging and README ([952b6ee](https://github.com/stormsia/maily/commit/952b6eef34fe2db545196aac2fe47c0039991af7))
* add detailed instructions for updating and recreating the Docker stack ([981bea5](https://github.com/stormsia/maily/commit/981bea5519f7530bd935f314301fb8dd111cc7ad))
* add DispoEmailOrg provider and implement mailbox functionality ([57b023d](https://github.com/stormsia/maily/commit/57b023d274505e2d08697c28f34ab335f36201a3))
* add dynamic provider headers management for temp-mail.io ([f9236f0](https://github.com/stormsia/maily/commit/f9236f03e7ca04a0c0dab112f4130c3a45ddb7ff))
* Add GitHub workflows for CI/CD, security, and documentation ([317674d](https://github.com/stormsia/maily/commit/317674df40109f9afe131dd07df2bf5ca1494d01))
* add overview and retention pages with charts and retention management ([8b045a3](https://github.com/stormsia/maily/commit/8b045a327b5b2cfdce7d6d9d2fbbb8858874ceb7))
* Add stable first-party classification for isort in ruff configuration ([8833126](https://github.com/stormsia/maily/commit/883312673d0d88c03883e2149b63ad759e017d03))
* add standalone client generation script and update tests ([6d70e9f](https://github.com/stormsia/maily/commit/6d70e9fec56e14bb1be5c093c10f4d6a66e56211))
* add standalone client implementation for mailtmapi ([9ede06d](https://github.com/stormsia/maily/commit/9ede06d682ab5be105b14f67f5ca35ed4dadab85))
* add standalone client with auto-update functionality ([5558a36](https://github.com/stormsia/maily/commit/5558a36dfda8f8812eacbe00d9a371ec6ae725d8))
* Add support for temp.tf provider with Gmail aliasing options and update documentation ([4ce190a](https://github.com/stormsia/maily/commit/4ce190a69e6fc794221f63d60f473f567e716c74))
* Add TempTF provider for temporary email functionality ([dab59f7](https://github.com/stormsia/maily/commit/dab59f7db43067bfc576ad6426a5a3c11dd6361b))
* Add tests for unique identity per mailbox and session management ([e46597c](https://github.com/stormsia/maily/commit/e46597c7be2eef9e4d7ebcd1701b0b7fd5b7ca97))
* **benchmarks:** add macro load testing, memory profiling, and property tests ([2876360](https://github.com/stormsia/maily/commit/2876360faba4520e4db0fce3700ea8e17b376722))
* **cd:** add CI gate, wheel smoke tests, Cosign signing, SHA256 sums, and TestPyPI target ([7a20463](https://github.com/stormsia/maily/commit/7a20463f22f56c80fe9e3456e6c9b6850669b6bb))
* **ci:** add PR diff coverage gate, PR size labeler, lychee link checker, and smart path filtering ([b14b506](https://github.com/stormsia/maily/commit/b14b506d94b03ded050cc87f470befe7f84b76fe))
* **ci:** add PR performance regression gate, zizmor audit, semver check, and clean commit lint ([fe84f71](https://github.com/stormsia/maily/commit/fe84f7112bd1c4b0fe7e01c9b26434e1f0b6b871))
* **ci:** add ratchet protection and score thresholds to mutation profiles ([7cd3e58](https://github.com/stormsia/maily/commit/7cd3e589c42481d210cc567337bc85cf103c80f9))
* **ci:** add Semantic PR Title Gate, OpenAPI Breaking Changes Gate, .trivyignore, typos spellchecker, pre-commit config, and concurrency cancellation ([d621d3c](https://github.com/stormsia/maily/commit/d621d3ce336858e5045a2ecc737c534b39b29b52))
* **ci:** complete master plan items: Biome, pip-audit SARIF, vulture, 85% coverage, tag verification, ruff format check, and nightly schedules ([12fd09f](https://github.com/stormsia/maily/commit/12fd09f7033184bb31128cce3c030954725aaf47))
* **ci:** expand performance benchmarks and smart diff-mutation testing ([551b341](https://github.com/stormsia/maily/commit/551b3412ccc9d1444beb2e8c7243660909060bb3))
* **ci:** implement executive Step Summary dashboard for pipeline results ([cddfd90](https://github.com/stormsia/maily/commit/cddfd906c3d54f685bd1e29802cf25186cbbb842))
* **ci:** publish executive test & quality dashboard and openapi changes to PR ([54304bd](https://github.com/stormsia/maily/commit/54304bd775dbe39e446a2645ce7b7abbbf833afe))
* **client:** modernize mailtmapi-client packaging, documentation, and facades ([5d7c109](https://github.com/stormsia/maily/commit/5d7c109c8bd35cea9f4cf2beeec7367023e87972))
* enhance API security and documentation ([e566dbb](https://github.com/stormsia/maily/commit/e566dbbe03cd651045543e428c00a27c9fca69d8))
* enhance CI workflows, add benchmarks, and improve security audits ([8071cb3](https://github.com/stormsia/maily/commit/8071cb3ee4ca838df5b5e58216ccbc68f406980c))
* Enhance detail page with auto-refresh and verification extraction ([6cbcfdd](https://github.com/stormsia/maily/commit/6cbcfddae39563fccd3f5d5981a8ebc4367e619c))
* Enhance domain cache management and improve health overview UI ([56a7ffc](https://github.com/stormsia/maily/commit/56a7ffcdc466ae949d0b04ba956fa0ed5df7f593))
* Enhance error handling and response structure ([f72042c](https://github.com/stormsia/maily/commit/f72042c2a68e977837ed46e020f5f586a6b78c2b))
* enhance error handling for API key and provider authentication failures ([0a8f573](https://github.com/stormsia/maily/commit/0a8f57344dd370bc3916e39abd3518132f890c6f))
* enhance message receipt handling and update stats ledger for accurate event tracking ([ce19fb9](https://github.com/stormsia/maily/commit/ce19fb9b23de733d198755e58eab588d48c45a07))
* Enhance stats history tracking with domain and owner_key_id ([7553970](https://github.com/stormsia/maily/commit/7553970680463328701c29f29f7bedffab774c21))
* **health:** add fault injection simulation parameters for e2e alert testing ([1b8d3cd](https://github.com/stormsia/maily/commit/1b8d3cd5e7578879a4d6e14fadcf5c13dac6e025))
* **health:** add live provider & email delivery verification suite with automated alerting ([6539dd5](https://github.com/stormsia/maily/commit/6539dd55dbcf20e3a3392429ab1c9fe38d484481))
* **health:** enable e2e email delivery testing for all 7 public providers ([9b21f9a](https://github.com/stormsia/maily/commit/9b21f9ab040ec8df31289ad850f80d8291ca22d9))
* **health:** treat delivery failures as degradation for automated issue alerting and status tracking ([198cdd6](https://github.com/stormsia/maily/commit/198cdd686879338f86f64c657794f37723a868a6))
* Implement activity ledger for dashboard stats ([12d552a](https://github.com/stormsia/maily/commit/12d552a4baa9226c4c1f8d0f5088eacb58202df3))
* Implement cross-origin request rejection and enhance health check response ([b2bd576](https://github.com/stormsia/maily/commit/b2bd5763679c7f8f6055fb4db2fcad45979b8fe6))
* implement short transaction handling for domain and provider header persistence ([9132548](https://github.com/stormsia/maily/commit/91325482a9a955cd2095d67b310f8f04ba3360c8))
* Implement sweep lock for retention sweep to prevent race conditions ([5626167](https://github.com/stormsia/maily/commit/56261679066bd1ca3aef7a173d1847b9a7e79e1d))
* **mutation:** expand targeted tests and ratchet quality gate thresholds ([b55763b](https://github.com/stormsia/maily/commit/b55763b030071dc7dea377f13ad989a602433bcf))
* **pages:** unify developer portal with API docs, benchmarks, and security analytics ([167f92f](https://github.com/stormsia/maily/commit/167f92f52ff244bb4d47fa28485826941849ff58))
* **providers:** centralize public provider registry and automate live health testing discovery ([dc152bf](https://github.com/stormsia/maily/commit/dc152bfeea9050318836ed2b0e694be959a15741))
* **publish:** configure maily-server and maily-client OIDC trusted publishing ([27287cd](https://github.com/stormsia/maily/commit/27287cd86b8a12a840997aee04663901641cfa4a))
* **release:** setup Release Please and Conventional Commits enforcement ([979ff0b](https://github.com/stormsia/maily/commit/979ff0b9a4185c09325e4d79e696918e02118685))
* **test-sender:** add autonomous test email dispatcher with primary and fallback providers ([487b59a](https://github.com/stormsia/maily/commit/487b59aa30681f5bf26cbeb55956f5363b955dbd))
* **ui:** improve keyboard accessibility and enhance modal focus handling ([8562d37](https://github.com/stormsia/maily/commit/8562d375211e789dcb4da9f534366e4105f418ca))
* Update overview metrics and provider card for improved clarity on mailbox and message statistics ([4271d3f](https://github.com/stormsia/maily/commit/4271d3f2172149adc6f1c10b3918cc12191fc97c))
* update workflows and configurations for improved CI/CD processes and security ([381eb6f](https://github.com/stormsia/maily/commit/381eb6f97902a5870ab3ab3f18abc8d0ac20da45))


### Bug Fixes

* **ci:** add GHSA-6v7p-g79w-8964 to .trivyignore and resolve ruff unused variable in openapi script ([87a4fcd](https://github.com/stormsia/maily/commit/87a4fcd7fdf61be7a1a62c8ae55e5293a846b6bc))
* **ci:** allow credential persistence for git fetch in commit-lint and pr-benchmark ([f7cafcd](https://github.com/stormsia/maily/commit/f7cafcd8e67f15622d82a24e651481a3381e70a1))
* **ci:** check existing static JS files with node --check ([362a296](https://github.com/stormsia/maily/commit/362a2966dc3b69e6c40693f0515a9df221c9372a))
* **ci:** checkout PR head ref in commit-lint workflow ([d776d91](https://github.com/stormsia/maily/commit/d776d91e5655323ab60be6a6158857a8a5f97065))
* **ci:** exclude unreleased container URL in lychee, ignore changelog in typos, and whitelist pages in zizmor ([cd848c9](https://github.com/stormsia/maily/commit/cd848c9c6cef7a8f4652903cd60aabd009ad6484))
* **ci:** fix release-please env secret expression in if condition ([b218fe7](https://github.com/stormsia/maily/commit/b218fe7d254349bb5452aa1a4e7b8414b82a4b87))
* **ci:** grant issues:write and map env in pr-benchmark workflow ([177bb48](https://github.com/stormsia/maily/commit/177bb4896caf25d0575577b2a1ef712a60e17788))
* **ci:** pass --yes to npx biome and htmlhint to prevent non-interactive prompts ([54f2972](https://github.com/stormsia/maily/commit/54f2972a0327d7bf35a37f951ac19ceeb79d7ef8))
* **ci:** provide MAILTM_API_KEY in Docker smoke test container ([8dda9af](https://github.com/stormsia/maily/commit/8dda9af308e9f7a5f855438675c3286539b14606))
* **ci:** remove invalid organizeImports key from .biome.json for Biome 2.x ([0a5e4e8](https://github.com/stormsia/maily/commit/0a5e4e8b8355bfec4fcdc64ab09c564c50a202f9))
* **ci:** rename shadowed lines variable in lint_pr_commits to pass mypy ([098aa43](https://github.com/stormsia/maily/commit/098aa43b21176afe2f288a3c864a2181f41f6e68))
* **ci:** resolve Biome config error, benchmark gh-pages missing ref, and gitleaks false positive ([cf1a327](https://github.com/stormsia/maily/commit/cf1a3277535f0b297169d561d51061ad1de53705))
* **ci:** resolve sqlite concurrency in tests and delay initial retention sweep ([aba74da](https://github.com/stormsia/maily/commit/aba74da98fd0fc9bda2f4663225b6a2f46b5cbaf))
* **ci:** robust polling wait loop for Docker container health check ([04096a3](https://github.com/stormsia/maily/commit/04096a385e731bccfeef4a1b57bad12693aa265d))
* **ci:** standardize Python 3.15 runtime, fix Docker smoke test, permissions, and restore full README ([16551ea](https://github.com/stormsia/maily/commit/16551ea70ddc448e05df5ca802e256351793f5ec))
* **ci:** update biome configuration and use biome lint for static assets ([25aae33](https://github.com/stormsia/maily/commit/25aae33b12b5902a16b858e174a05f9c53a679a7))
* **ci:** use native git diff for change detection without external actions ([e3c0060](https://github.com/stormsia/maily/commit/e3c00600717aceda0ffb2d7022ea8344e15e0026))
* **ci:** whitelist pypi-publish-client in zizmor and add LICENSE file ([48aa41a](https://github.com/stormsia/maily/commit/48aa41ae268e05adca7cb925d6cd2dd04b58bdf6))
* **compat:** use typing_extensions.TypedDict for Python &lt; 3.12 compatibility ([0c0d4e0](https://github.com/stormsia/maily/commit/0c0d4e09635ed8e86a844d37ffcfb23bad83f888))
* **docker,docs,codeql:** fix Dockerfile builder image, OpenAPI export via create_app, and CodeQL graceful fallback ([aff655e](https://github.com/stormsia/maily/commit/aff655ef41049ed8fa0b0c21644e83700852f9f2))
* **docker:** remove unnecessary name attribute from mailtmapi_data volume ([4a37e2d](https://github.com/stormsia/maily/commit/4a37e2da7179b4a1dabd5e55e643f7f869b5f5a2))
* **docker:** support workflow_dispatch, add release wheels, and modernize paths/user to maily ([7efdf0e](https://github.com/stormsia/maily/commit/7efdf0eb53a85af993ed9cef78046740d2c1d0b8))
* **mutation-test:** fix mutmut export CLI command and eliminate surviving mutants in crypto module ([23abdb2](https://github.com/stormsia/maily/commit/23abdb2ac107e5f790c200a134786f7f28183e15))
* **mutmut:** resolve alembic directory in mutation sandbox and harden quality gate ([549c336](https://github.com/stormsia/maily/commit/549c3366af05d56850d974b530b9ed0320d7f719))
* mypy error in retention.py ([7dc1a03](https://github.com/stormsia/maily/commit/7dc1a031e474c7ccbb2fc7befea2e14f4715632d))
* **openapi:** update existing sticky comment even when schema changes are resolved ([4625f2b](https://github.com/stormsia/maily/commit/4625f2b7a4f6b6fb737e79ad8105d8b4bce5873d))
* **release:** add concurrency group to release-please to avoid race conditions ([44cea5d](https://github.com/stormsia/maily/commit/44cea5d455498f662b55475fe35f89946e25b2dc))
* **security:** restore full allowlist and extend default in .gitleaks.toml ([59c2e32](https://github.com/stormsia/maily/commit/59c2e32878d86cadc5d16dc468d55ee5c774eb56))
* **settings:** sanitize empty proxy string to None ([69bd28e](https://github.com/stormsia/maily/commit/69bd28ef9896639e24d0c76f0478e89c6ee917c5))
* **tests:** enhance resource management and suppress warnings in test cases ([08d964c](https://github.com/stormsia/maily/commit/08d964c7738b092473eb403f6ee73978e619be0f))
* update Gmail credentials handling and improve error logging ([f9236f0](https://github.com/stormsia/maily/commit/f9236f03e7ca04a0c0dab112f4130c3a45ddb7ff))


### Performance Improvements

* **ci:** ignore sub-millisecond jitter in PR benchmark comparisons ([d3b22d5](https://github.com/stormsia/maily/commit/d3b22d5023de48eca70046c6e5c0df67c2304300))


### Dependencies

* bump the fastapi-stack group with 2 updates ([9fc1e23](https://github.com/stormsia/maily/commit/9fc1e2366a385467c709a7c332dc4c72d6424f53))
* update httpx requirement from &gt;=0.27 to &gt;=0.28.1 ([ddb9fa7](https://github.com/stormsia/maily/commit/ddb9fa71489218330be6db87891a3534b8ff6136))
* update loguru requirement from &gt;=0.7 to &gt;=0.7.3 ([117506b](https://github.com/stormsia/maily/commit/117506bd2c5f6dae2fc8cca111b26c50abe28fd0))
* update mypy requirement ([81c46b6](https://github.com/stormsia/maily/commit/81c46b62c011d53048520bde04f79f08bcf1a055))
* update pydantic-settings requirement from &gt;=2.6 to &gt;=2.15.0 ([20d6e61](https://github.com/stormsia/maily/commit/20d6e6168fb33676999a70144000d39be081f97c))
* update pytest-asyncio requirement from &gt;=0.24 to &gt;=1.4.1 ([b3d49b5](https://github.com/stormsia/maily/commit/b3d49b5e3f413d2db7bc4b40aca6092b379c7eb7))
* update pytest-xdist requirement from &gt;=3.6 to &gt;=3.8.0 ([ec16abc](https://github.com/stormsia/maily/commit/ec16abc66b7559066f56a06b0ccc3c7cf0166da5))
* update typing-extensions requirement from &gt;=4.8 to &gt;=4.16.0 ([bc605d8](https://github.com/stormsia/maily/commit/bc605d882ce3f627f61df8a08056d4e465ba2f75))


### Documentation

* add open source community health files and reinforce gitignore ([cb0ecb4](https://github.com/stormsia/maily/commit/cb0ecb45643ca7fc558ee21f6830112186e78a2d))
* **client:** correct sync facade syntax in dictionary access callout ([d86497d](https://github.com/stormsia/maily/commit/d86497d3aa2315e17a81b1e96027141242b2b9dd))
* **client:** document all 19 flat facade shortcut methods in client README ([0b1e162](https://github.com/stormsia/maily/commit/0b1e16258ae29ac99a19159adddc53604a6d69f1))
* emphasize PyPI as preferred installation while keeping git and single-file options ([0567e3b](https://github.com/stormsia/maily/commit/0567e3bdc5c8789e2d395617e5bce584461b59c7))
* **i18n:** translate Russian comments, docstrings, and messages to English ([eea911a](https://github.com/stormsia/maily/commit/eea911a666a5fc0ea22b3c876b7f06ac9a093c9a))
* **providers:** enhance guide with live test suite, factories, and issue automation details ([b9d98c1](https://github.com/stormsia/maily/commit/b9d98c194ed4093829072cd6d0808238c1f4e319))


### Code Refactoring

* enhance overview page with new metrics and interactive charts ([035d759](https://github.com/stormsia/maily/commit/035d7598c590e74a3c3c4e256cdc7541dd0b0933))
