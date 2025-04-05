# Changelog

All notable changes to this project from 2024-10-30 onward will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased Pet Food Calculator

## [2.1.8-beta] - 2025-4-4

## Added

- Feature: Added new_food routing and setup

## [2.1.7-beta] - 2025-3-25

## Added

- Feature: Added custom warning SVGs from SVG Repo to replace the warning emojis
- Feature: Added scroll button to Pet Weight & Body Condition Score, RER, Completed Reports, Final Report, and Nutrition Resources pages

## Fix

- Refactor: Adjusted formatting for HTML documents

## Changed

- UI: Added headings to RER page
- UI: Added different row colors for completed reports

## [2.1.6-beta] - 2025-3-22

## Added

- Feature: Create file for MongoDB integration

## Changed

- UI: Adjust label size for login and register
  
## [2.1.5-beta] - 2025-2-25

## Added

- UI: Add [OpenDyslexic](https://github.com/antijingoist/opendyslexic) font
- Feature: Accordion for Worldwide and United States nutrition resources
  - UI: Added link stylization and organization summary

## Fixed

- Refactor: Adjusted font size and placement on the page

## Changed

- Pathway: Add CHANGELOG.md to the README_DIR

## [2.1.4-beta] - 2024-11-21

## Added

- Feature: Add PROJECT_SETUP for a more detailed dependencies list
- Feature: Added quick installation instructions with pip

## Fixed

- Refactor: Adjusted margins for the pet food bowl graphic on finished reports page

## [2.1.3-beta] - 2024-11-18

## Added

- Feature: Add a requirements.txt for easy start up

## Fixed

- Bug: Fixed quotation typo in main.py (#94)

## [2.1.2-beta] - 2024-10-31

## Added

- Feature: Add product features in README.

## Fixed

- Bug: Modified CSS for pregnant dogs within their last 21 days of gestation (text was clipping prior).
- Bug: Fixed broken links.

## Changed

- Improvement: Modified conditional CSS for pregnant dogs.

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
