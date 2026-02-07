# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- None

## [0.0.2] - 2025-02-07

### Added

- Requirements validation in `wat validate` command (checks env vars and files from config.yaml)
- PyPI trusted publishing via GitHub Actions
- CHANGELOG.md


### Changed

- Removed mypy from dev dependencies (using ruff only for linting)

## [0.0.1] - 2025-02-07

### Added

- Initial release of WATFlow
- CLI commands: `wat new`, `wat list`, `wat validate`, `wat run`, `wat deploy`
- Workflow template with config.yaml, main.py, tools/, and workflows/ structure
- Requirements validation for environment variables and files
- Claude AI integration with streaming support
- Gmail integration with OAuth 2.0 authentication
- Modal deployment support with scheduled execution
- Configuration system with phase-based execution
- Rich console output with progress indicators

[Unreleased]: https://github.com/cilladev/watflow/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/cilladev/watflow/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/cilladev/watflow/releases/tag/v0.0.1
