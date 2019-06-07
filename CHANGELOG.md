# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.0] - 2019-06-02
### Added
- The server now supports advanced collisions (enable with -advancedcollisions option). Hit damage is assigned based on speed and angle of collision.
- Viewer -randcolor option added that uses random color for robots.
- A new robot class system has been implemented. Enable with -allowclasses option on server. There is still more work before classes have correct game mechanics.
- The server now has -scanmaxdistance option which defines the max distance an enemy robot can be detected with scanRequest.
- Team demo robot added. This is an example of using python threading to control two robot from one python script. The robots can share information and work together.
- Data from each robots last scanRequest and fireCanonRequest message are now stored and sent to the viewer. This can be used by later viewer updates.

### Changed
- Demo robots wait longer for server to to reply to joinRequest.
- Robots can no longer send messages with unknown data fields and optional fields are now supported and validated.
- Shells now appear as small arrows in viewer rather than circles.
- Robot names are now limited to max length of 16 characters.
- Fixed bug that did not allow scanReply to return robot further than 1415 distance away.
- Minor updates to README.
- Server no longer mistakenly includes result field in fireCanonReply message.

## [1.3.0] - 2019-05-15
### Added
- Server option -noviewers which disables viewers.
- Server prints command line options on startup.

### Changed
- netbots_math.contains() can now scan a full circle (0 to 0 radians)
- Robot colors in viewer have been improved.
- Minor documentation fixes.

## [1.2.0] - 2019-05-06
### Added
- Ability to use all permutations of each start set of start locations. Enable with -startperms command line option. When enabled, each set of start locations will be used multiple times with each permutation of robots to positions. 
- Percent of total points each robot has is now displayed on the scoreboard. Other stats have also been added.

### Changed
- Default -droprate to 11 (a prime number). This may be more fair.
- Stats have now been combined with scoreboard.
- Server now busy waits, rather than calling time.sleep(), which is much more accurate for timing steps.
- Other minor performance improvements.

## [1.1.1] - 2019-05-02
### Added
- NetBots contribution guidelines added.

### Changed
- Formatting updates to better comply with PEP8
- Removed repeated import and fixed spelling.

## [1.1.0] - 2019-04-25
### Added
- Added Total Damage inflicted to server score board. This is the damage that explosions from a robot's shells have had on all robots, including the robot that fired the shell.

### Changed
- Fixed bug where alive robots were colliding with dead robots. Dead robots should not cause collisions.
- Added missing "pass" statement to Sitting Duck demo robot. Missing statement was causing Sitting Duck to not run.

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

[Unreleased]: https://github.com/dbakewel/netbots/compare/1.4.0...HEAD
[1.4.0]: https://github.com/dbakewel/netbots/compare/1.3.0...1.4.0
[1.3.0]: https://github.com/dbakewel/netbots/compare/1.2.0...1.3.0
[1.2.0]: https://github.com/dbakewel/netbots/compare/1.1.1...1.2.0
[1.1.1]: https://github.com/dbakewel/netbots/compare/1.1.0...1.1.1
[1.1.0]: https://github.com/dbakewel/netbots/compare/1.0.1...1.1.0
[1.0.1]: https://github.com/dbakewel/netbots/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/dbakewel/netbots/compare/0.9.0...1.0.0
[0.9.0]: https://github.com/dbakewel/netbots/releases/tag/0.9.0