# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1] - 2019-04-24
### Changed
- Fixed bug that was only allowing one less than botMsgsPerStep messages to be processed per robot per step. This was impacting any robots trying to send botMsgsPerStep messages in a single step as one of their messages was being incorrectly dropped.

## [1.0.0] - 2019-04-19
### Added
- More stats have been added to server score board.
- Added this CHANGELOG.md

### Changed
- Default game mechanics changed so it takes longer for robots to win. Damages have been cut in half and robot acceleration rate has been doubled.
- Viewer sends keep alive more often to ensure viewer is not dropped by server.
- NetBots now requires Python 3.6 or higher because server code started using f-strings.

## [0.9.0] - 2019-04-16
- Beta release.

[Unreleased]: https://github.com/dbakewel/netbots/compare/1.0.1...HEAD
[1.0.1]: https://github.com/dbakewel/netbots/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/dbakewel/netbots/compare/0.9.0...1.0.0
[0.9.0]: https://github.com/dbakewel/netbots/releases/tag/0.9.0