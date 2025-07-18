# DataMap CLI – Product Requirements Document (PRD)

## Overview

The goal of this project is to create a cross-platform Command Line Interface (CLI) tool to interact with the [DataMap](https://datamap.pcs.usp.br/) platform. The CLI will allow users to easily retrieve information and download datasets using a simple and intuitive command-line experience.

## Objectives

- Provide researchers and users with quick access to dataset information from the terminal.
- Enable efficient and automated download of files associated with datasets.
- Ensure compatibility across major operating systems.

## Functional Requirements

### 1. Retrieve Dataset Metadata

- **Command:** Get dataset details.
- **Input:** UUID of a dataset.
- **Output:** Display basic metadata such as title, description, creation date, and available versions.

### 2. List Dataset Versions

- **Command:** List versions of a dataset.
- **Input:** UUID of a dataset.
- **Output:** Display a list of available versions with UUIDs and optional labels.

### 3. List Files of a Version

- **Command:** List datafiles of a version.
- **Input:** UUID of a version.
- **Output:** Display filenames and their corresponding UUIDs.

### 4. Download All Files from a Version

- **Command:** Download files.
- **Input:** UUID of a version and optional output directory.
- **Output:** Download all datafiles associated with that version into a local directory.

## Non-Functional Requirements

### 1. Cross-Platform Compatibility

- Must work on Windows, macOS, and Linux without additional system-specific configuration.

### 2. API Authentication

- The CLI must use the official application credentials (APP ID and APP KEY) when making requests to the DataMap API.

### 3. User Experience

- Clear and informative error messages for invalid input or failed requests.
- Output should be human-readable and suitable for scripting or logging when needed.

### 4. Performance

- File downloads should support large datasets and show progress to the user.
- The CLI should not introduce significant latency when querying metadata.

### 5. Security

- Sensitive credentials (e.g., APP KEY) must not be exposed in logs or outputs.
- Should support environment variable configuration for authentication credentials.

## Success Criteria

- A user can list and retrieve datasets, versions, and files via the CLI.
- A user can successfully download all files associated with a dataset version.
- The CLI is stable and usable across all supported platforms.
