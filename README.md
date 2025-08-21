# TeamCity Kotlin DSL Test Automation

This project provides comprehensive test automation for TeamCity Kotlin DSL versioned settings, covering import, synchronization, and pipeline execution scenarios.

## Features

- **DSL Import Testing**: Validates proper import of Kotlin DSL-based projects
- **Synchronization Testing**: Tests bidirectional sync between TeamCity and VCS
- **Pipeline Execution Testing**: Verifies that imported/synchronized pipelines execute correctly
- **API-Based Testing**: Uses TeamCity REST API for reliable, fast testing
- **Docker Support**: Includes Docker Compose setup for local testing
- **Comprehensive Reporting**: Generates HTML and JSON test reports

## Project Structure

See the project structure section above for detailed file organization.

## Setup Instructions

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (for local TeamCity instance)
- Git repository access (for synchronization tests)

### Local Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd teamcity-dsl-qa