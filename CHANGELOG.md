# Changelog

## [2.0.4](https://github.com/bagdeli/KavoshStart/compare/v2.0.3...v2.0.4) (2026-10-09)


### Bug Fixes

* **runtime:** remove hidden gh dependency from reusable control plane ([#97](https://github.com/bagdeli/KavoshStart/issues/97)) ([ac9064c](https://github.com/bagdeli/KavoshStart/commit/ac9064ca39dbd68ace137b726842e442a11da7dd))

## [2.0.3](https://github.com/bagdeli/KavoshStart/compare/v2.0.2...v2.0.3) (2026-10-09)


### Bug Fixes

* **source:** allow exact SHAs in docs audit provenance ([#92](https://github.com/bagdeli/KavoshStart/issues/92)) ([4b6995a](https://github.com/bagdeli/KavoshStart/commit/4b6995a63ce1748f670b39350225470bcf874753))

## [2.0.2](https://github.com/bagdeli/KavoshStart/compare/v2.0.1...v2.0.2) (2026-10-09)


### Bug Fixes

* **ci:** make self-hosted trust contract implementation-neutral ([#88](https://github.com/bagdeli/KavoshStart/issues/88)) ([e04c807](https://github.com/bagdeli/KavoshStart/commit/e04c807afbdee84905ef4ffd4e681a029e4224ed))

## [2.0.1](https://github.com/bagdeli/KavoshStart/compare/v2.0.0...v2.0.1) (2026-10-09)


### Bug Fixes

* **governance:** honor declared CI and release adapters ([#85](https://github.com/bagdeli/KavoshStart/issues/85)) ([9d059c1](https://github.com/bagdeli/KavoshStart/commit/9d059c1ff8909a8307841d5cf6873c98b702dd6f))

## [2.0.0](https://github.com/bagdeli/KavoshStart/compare/v1.7.1...v2.0.0) (2026-10-09)


### ⚠ BREAKING CHANGES

* **standard:** KavoshStart v2 replaces universal PR size gates and owner-only mechanical merges with risk/evidence governance, delegated low/medium merge, outcome-based command/release contracts, and explicit continuation/acceptance separation.

### Features

* **standard:** generalize risk evidence and delegated merge ([#73](https://github.com/bagdeli/KavoshStart/issues/73)) ([15e94c1](https://github.com/bagdeli/KavoshStart/commit/15e94c180fd62dde68a7ee88fe2f61fbf94d7900)), closes [#72](https://github.com/bagdeli/KavoshStart/issues/72)


### Bug Fixes

* **governance:** require ADR for breaking control-plane changes ([#79](https://github.com/bagdeli/KavoshStart/issues/79)) ([ba5098f](https://github.com/bagdeli/KavoshStart/commit/ba5098f1d2c9fb2c76a9692ebc4117ecd61a1d66))
* **main-guard:** tolerate post-merge PR association lag ([#82](https://github.com/bagdeli/KavoshStart/issues/82)) ([71b50c5](https://github.com/bagdeli/KavoshStart/commit/71b50c5f5b23c682bc960690347393c9b84e7fb6))

## [1.7.1](https://github.com/bagdeli/KavoshStart/compare/v1.7.0...v1.7.1) (2026-10-09)


### Bug Fixes

* **standard:** make self-hosting identity unambiguous ([#70](https://github.com/bagdeli/KavoshStart/issues/70)) ([ba3e81e](https://github.com/bagdeli/KavoshStart/commit/ba3e81e18d3f19e6568d45fc5c438d00cd147eb2))

## [1.7.0](https://github.com/bagdeli/KavoshStart/compare/v1.6.0...v1.7.0) (2026-10-09)


### Features

* **standard:** close lifecycle and acceptance gaps ([#67](https://github.com/bagdeli/KavoshStart/issues/67)) ([488d72d](https://github.com/bagdeli/KavoshStart/commit/488d72d6e7b59adb2bf72bc5a992f605be9bcb85))

## [1.6.0](https://github.com/bagdeli/KavoshStart/compare/v1.5.0...v1.6.0) (2026-10-09)


### Features

* **acceptance:** enforce continuous evidence flow ([#61](https://github.com/bagdeli/KavoshStart/issues/61)) ([ec36661](https://github.com/bagdeli/KavoshStart/commit/ec36661cc66e5c76c68bd91cde52c17347513cdb))
* **deploy:** enforce persistent environment conformance ([#59](https://github.com/bagdeli/KavoshStart/issues/59)) ([d8575ee](https://github.com/bagdeli/KavoshStart/commit/d8575ee83757de5a745ef7635a130ce6e3456b19))
* **release:** add gated Test release candidates ([#60](https://github.com/bagdeli/KavoshStart/issues/60)) ([aaf4fd6](https://github.com/bagdeli/KavoshStart/commit/aaf4fd6cff32cdf90ad924ac1085336913ed5477))


### Bug Fixes

* **governance:** handle reusable caller timeouts ([#52](https://github.com/bagdeli/KavoshStart/issues/52)) ([9edab4c](https://github.com/bagdeli/KavoshStart/commit/9edab4cfe62a0516b06d762942dc8fc9cc3eee20))
* **health:** treat public standard Actions minutes as free ([#63](https://github.com/bagdeli/KavoshStart/issues/63)) ([8ecbcc4](https://github.com/bagdeli/KavoshStart/commit/8ecbcc482888a8cf3d9f8db4930ac37c4f3b73ab))
* **release:** repair interrupted 1.6 transaction ([#64](https://github.com/bagdeli/KavoshStart/issues/64)) ([02c81e6](https://github.com/bagdeli/KavoshStart/commit/02c81e690c01a0c2802175d9eab0c1d7173229ef))

## [1.5.0](https://github.com/bagdeli/KavoshStart/compare/v1.4.0...v1.5.0) (2026-10-02)


### Features

* **policy:** finish bounded free-only authorization controls ([#47](https://github.com/bagdeli/KavoshStart/issues/47)) ([8f2dd43](https://github.com/bagdeli/KavoshStart/commit/8f2dd435b886a84feac929cf6aeca0f63058c58b))

## [1.4.0](https://github.com/bagdeli/KavoshStart/compare/v1.3.1...v1.4.0) (2026-10-02)


### Features

* **ci:** add local-only T1 static validation ([9fe44f6](https://github.com/bagdeli/KavoshStart/commit/9fe44f66db71d0803c6255ed21b1a05b52f6c5ea)), closes [#32](https://github.com/bagdeli/KavoshStart/issues/32)


### Bug Fixes

* **health:** close green status reports ([737adc6](https://github.com/bagdeli/KavoshStart/commit/737adc65ae52383721c52265731fdb061f547c6b))

## [1.3.1](https://github.com/bagdeli/KavoshStart/compare/v1.3.0...v1.3.1) (2026-10-02)


### Bug Fixes

* **health:** clear legacy tag and stale branch findings ([cdb1699](https://github.com/bagdeli/KavoshStart/commit/cdb16998087f3fd889b62849f9905f1325222572))

## [1.3.0](https://github.com/bagdeli/KavoshStart/compare/v1.2.0...v1.3.0) (2026-10-01)


### Features

* **vnext:** enforce authorized free-only operations ([d0f03bb](https://github.com/bagdeli/KavoshStart/commit/d0f03bbc7752bff11c55ff431bd0b11bfe1257a9)), closes [#34](https://github.com/bagdeli/KavoshStart/issues/34)


### Bug Fixes

* **privacy:** separate public and private control surfaces ([8042db7](https://github.com/bagdeli/KavoshStart/commit/8042db77b95f431471cf89eca252f6b04f5f255a))

## [1.2.0](https://github.com/bagdeli/KavoshStart/compare/v1.1.0...v1.2.0) (2026-09-26)


### Features

* **governance:** machine-check SEC-2, SEC-3, SEC-4, SRC-7, guard wiring and AI section ([#12](https://github.com/bagdeli/KavoshStart/issues/12)) ([9c76bf8](https://github.com/bagdeli/KavoshStart/commit/9c76bf895b18418fe8ebb259fbad7815f05d1a76))
* **portfolio:** Layer O supervisor detects disabled enforcement from outside ([#19](https://github.com/bagdeli/KavoshStart/issues/19)) ([4ad1668](https://github.com/bagdeli/KavoshStart/commit/4ad16689661a63aa1c2ed71c57eabbe062f6a51b))
* **release:** gated release pipeline with exact version pins ([#10](https://github.com/bagdeli/KavoshStart/issues/10)) ([8c10fb8](https://github.com/bagdeli/KavoshStart/commit/8c10fb82079529fd16ad42c8f20f898aeb13ab90))
* **runner:** runner by visibility — private repos self-hosted, public repos GitHub-hosted ([#22](https://github.com/bagdeli/KavoshStart/issues/22)) ([a9d4be0](https://github.com/bagdeli/KavoshStart/commit/a9d4be0df39ade0cb61abbf9f09bdd2f923a7146))


### Bug Fixes

* **deploy:** expand/contract migrations, mandatory backup, clean per-version releases ([#13](https://github.com/bagdeli/KavoshStart/issues/13)) ([a7efdcc](https://github.com/bagdeli/KavoshStart/commit/a7efdcc52095398f49652d3e6d6413a833f51c35))
* **health:** exact type labels, direct pushes, attribution; harden templates ([#14](https://github.com/bagdeli/KavoshStart/issues/14)) ([3a6027c](https://github.com/bagdeli/KavoshStart/commit/3a6027c63c8eadfe44d3cad53aa535e60edbbed6))
* **main-guard:** missing required checks are violations ([#11](https://github.com/bagdeli/KavoshStart/issues/11)) ([56478f3](https://github.com/bagdeli/KavoshStart/commit/56478f30a2674ab2cfe770d0998a181d0a43d088))
* **release:** tag releases as plain vX.Y.Z ([#23](https://github.com/bagdeli/KavoshStart/issues/23)) ([c5987f8](https://github.com/bagdeli/KavoshStart/commit/c5987f81d9e0882a82f5446c4f8f436e9f912816))

## [1.1.0](https://github.com/bagdeli/KavoshStart/compare/KavoshStart-v1.0.0...KavoshStart-v1.1.0) (2026-09-26)


### Features

* **governance:** machine-check SEC-2, SEC-3, SEC-4, SRC-7, guard wiring and AI section ([#12](https://github.com/bagdeli/KavoshStart/issues/12)) ([9c76bf8](https://github.com/bagdeli/KavoshStart/commit/9c76bf895b18418fe8ebb259fbad7815f05d1a76))
* **portfolio:** Layer O supervisor detects disabled enforcement from outside ([#19](https://github.com/bagdeli/KavoshStart/issues/19)) ([4ad1668](https://github.com/bagdeli/KavoshStart/commit/4ad16689661a63aa1c2ed71c57eabbe062f6a51b))
* **release:** gated release pipeline with exact version pins ([#10](https://github.com/bagdeli/KavoshStart/issues/10)) ([8c10fb8](https://github.com/bagdeli/KavoshStart/commit/8c10fb82079529fd16ad42c8f20f898aeb13ab90))
* **runner:** runner by visibility — private repos self-hosted, public repos GitHub-hosted ([#22](https://github.com/bagdeli/KavoshStart/issues/22)) ([a9d4be0](https://github.com/bagdeli/KavoshStart/commit/a9d4be0df39ade0cb61abbf9f09bdd2f923a7146))


### Bug Fixes

* **deploy:** expand/contract migrations, mandatory backup, clean per-version releases ([#13](https://github.com/bagdeli/KavoshStart/issues/13)) ([a7efdcc](https://github.com/bagdeli/KavoshStart/commit/a7efdcc52095398f49652d3e6d6413a833f51c35))
* **health:** exact type labels, direct pushes, attribution; harden templates ([#14](https://github.com/bagdeli/KavoshStart/issues/14)) ([3a6027c](https://github.com/bagdeli/KavoshStart/commit/3a6027c63c8eadfe44d3cad53aa535e60edbbed6))
* **main-guard:** missing required checks are violations ([#11](https://github.com/bagdeli/KavoshStart/issues/11)) ([56478f3](https://github.com/bagdeli/KavoshStart/commit/56478f30a2674ab2cfe770d0998a181d0a43d088))

## Changelog

Managed by release-please from Conventional Commits.
