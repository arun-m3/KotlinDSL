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
Run Team City instance using:
   docker run --name teamcity-server-instance \
   -v <path to data directory>:/data/teamcity_server/datadir \
   -v <path to logs directory>:/opt/teamcity/logs \
   -p <port on host>:8111 \
   jetbrains/teamcity-server

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd teamcity-dsl-qa

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt

3. **Configure environment**:
   ```bash
   cp .env.example .env
# Edit .env with your settings

4. **Start TeamCity (Docker)**:
   ```bash
   docker-compose up -d teamcity-server teamcity-agent

5. **Wait for TeamCity to start and setup admin user**:
   ```bash
   python scripts/setup_environment.py


6. **Running Tests**
   Run All Tests
      ```bash
      pytest -v
   Run Specific Test Categories
      ```bash
      pytest tests/test_dsl_import.py -v
      pytest tests/test_synchronization.py -v
      pytest tests/test_pipeline_execution.py -v

7. **Pipeline: Jenkins**
   Use the provided Jenkinsfile for Jenkins CI/CD.

