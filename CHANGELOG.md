# Changelog

## [1.7.0](https://github.com/bagdeli/KavoshStart/compare/v1.6.0...v1.7.0) (2026-10-09)


### Features

* **acceptance:** enforce continuous evidence flow ([#61](https://github.com/bagdeli/KavoshStart/issues/61)) ([ec36661](https://github.com/bagdeli/KavoshStart/commit/ec36661cc66e5c76c68bd91cde52c17347513cdb))
* **ci:** add local-only T1 static validation ([9fe44f6](https://github.com/bagdeli/KavoshStart/commit/9fe44f66db71d0803c6255ed21b1a05b52f6c5ea)), closes [#32](https://github.com/bagdeli/KavoshStart/issues/32)
* **deploy:** enforce persistent environment conformance ([#59](https://github.com/bagdeli/KavoshStart/issues/59)) ([d8575ee](https://github.com/bagdeli/KavoshStart/commit/d8575ee83757de5a745ef7635a130ce6e3456b19))
* **governance:** machine-check SEC-2, SEC-3, SEC-4, SRC-7, guard wiring and AI section ([#12](https://github.com/bagdeli/KavoshStart/issues/12)) ([9c76bf8](https://github.com/bagdeli/KavoshStart/commit/9c76bf895b18418fe8ebb259fbad7815f05d1a76))
* **policy:** finish bounded free-only authorization controls ([#47](https://github.com/bagdeli/KavoshStart/issues/47)) ([8f2dd43](https://github.com/bagdeli/KavoshStart/commit/8f2dd435b886a84feac929cf6aeca0f63058c58b))
* **portfolio:** Layer O supervisor detects disabled enforcement from outside ([#19](https://github.com/bagdeli/KavoshStart/issues/19)) ([4ad1668](https://github.com/bagdeli/KavoshStart/commit/4ad16689661a63aa1c2ed71c57eabbe062f6a51b))
* **release:** add gated Test release candidates ([#60](https://github.com/bagdeli/KavoshStart/issues/60)) ([aaf4fd6](https://github.com/bagdeli/KavoshStart/commit/aaf4fd6cff32cdf90ad924ac1085336913ed5477))
* **release:** gated release pipeline with exact version pins ([#10](https://github.com/bagdeli/KavoshStart/issues/10)) ([8c10fb8](https://github.com/bagdeli/KavoshStart/commit/8c10fb82079529fd16ad42c8f20f898aeb13ab90))
* **runner:** runner by visibility — private repos self-hosted, public repos GitHub-hosted ([#22](https://github.com/bagdeli/KavoshStart/issues/22)) ([a9d4be0](https://github.com/bagdeli/KavoshStart/commit/a9d4be0df39ade0cb61abbf9f09bdd2f923a7146))
* **vnext:** enforce authorized free-only operations ([d0f03bb](https://github.com/bagdeli/KavoshStart/commit/d0f03bbc7752bff11c55ff431bd0b11bfe1257a9)), closes [#34](https://github.com/bagdeli/KavoshStart/issues/34)


### Bug Fixes

* **deploy:** expand/contract migrations, mandatory backup, clean per-version releases ([#13](https://github.com/bagdeli/KavoshStart/issues/13)) ([a7efdcc](https://github.com/bagdeli/KavoshStart/commit/a7efdcc52095398f49652d3e6d6413a833f51c35))
* **governance:** handle reusable caller timeouts ([#52](https://github.com/bagdeli/KavoshStart/issues/52)) ([9edab4c](https://github.com/bagdeli/KavoshStart/commit/9edab4cfe62a0516b06d762942dc8fc9cc3eee20))
* **health:** clear legacy tag and stale branch findings ([cdb1699](https://github.com/bagdeli/KavoshStart/commit/cdb16998087f3fd889b62849f9905f1325222572))
* **health:** close green status reports ([737adc6](https://github.com/bagdeli/KavoshStart/commit/737adc65ae52383721c52265731fdb061f547c6b))
* **health:** exact type labels, direct pushes, attribution; harden templates ([#14](https://github.com/bagdeli/KavoshStart/issues/14)) ([3a6027c](https://github.com/bagdeli/KavoshStart/commit/3a6027c63c8eadfe44d3cad53aa535e60edbbed6))
* **health:** treat public standard Actions minutes as free ([#63](https://github.com/bagdeli/KavoshStart/issues/63)) ([8ecbcc4](https://github.com/bagdeli/KavoshStart/commit/8ecbcc482888a8cf3d9f8db4930ac37c4f3b73ab))
* **main-guard:** missing required checks are violations ([#11](https://github.com/bagdeli/KavoshStart/issues/11)) ([56478f3](https://github.com/bagdeli/KavoshStart/commit/56478f30a2674ab2cfe770d0998a181d0a43d088))
* **privacy:** separate public and private control surfaces ([8042db7](https://github.com/bagdeli/KavoshStart/commit/8042db77b95f431471cf89eca252f6b04f5f255a))
* **release:** tag releases as plain vX.Y.Z ([#23](https://github.com/bagdeli/KavoshStart/issues/23)) ([c5987f8](https://github.com/bagdeli/KavoshStart/commit/c5987f81d9e0882a82f5446c4f8f436e9f912816))

## [1.6.0](https://github.com/bagdeli/KavoshStart/compare/v1.5.0...v1.6.0) (2026-10-09)


### Features

* **acceptance:** enforce continuous evidence flow ([#61](https://github.com/bagdeli/KavoshStart/issues/61)) ([ec36661](https://github.com/bagdeli/KavoshStart/commit/ec36661cc66e5c76c68bd91cde52c17347513cdb))
* **deploy:** enforce persistent environment conformance ([#59](https://github.com/bagdeli/KavoshStart/issues/59)) ([d8575ee](https://github.com/bagdeli/KavoshStart/commit/d8575ee83757de5a745ef7635a130ce6e3456b19))
* **release:** add gated Test release candidates ([#60](https://github.com/bagdeli/KavoshStart/issues/60)) ([aaf4fd6](https://github.com/bagdeli/KavoshStart/commit/aaf4fd6cff32cdf90ad924ac1085336913ed5477))


### Bug Fixes

* **governance:** handle reusable caller timeouts ([#52](https://github.com/bagdeli/KavoshStart/issues/52)) ([9edab4c](https://github.com/bagdeli/KavoshStart/commit/9edab4cfe62a0516b06d762942dc8fc9cc3eee20))

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
