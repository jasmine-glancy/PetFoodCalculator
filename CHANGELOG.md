# Changelog

All notable changes to this project from 2024-10-30 onward will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased Pet Food Calculator

## [2.0.1-beta] - 2024-10-30

### Added

- Feature: Add subsections to README directory for easier reading.
- Feature: Add links to README sections.
- Added additional version goals.

### Changed

- Improvement: Split README into sections depending on what topic was covered.
- Improvement: Link to README subsections to main file.

## [2.0.0-beta] - 2024-09-03

### Added

- Feature: Ability to search for a human food against FatSecret's API.
- Feature: Provide specific daily maximum for found human food for the pet based on their daily treat allotment.

### Fixed

- Bug: Fix typo in main where "calculate_rer" was inadvertently named "calculcate_rer"

### Changed

- Improvement: Changed "female", "female spayed", "male", and "male neutered" to numbers related to foreign keys in the reproductive status table
- Improvement: Changed "dry", "can", and "pouch" to numbers related to foreign keys in the food forms table

## [1.0.0-beta] - 2024-06-16

### Added

- Initial release of the Pet Food Calculator.
- Feature: Calculate recommended feeding amounts based on the pet's information.
- Feature: Provide specific recommendations based on pet's life stage.
