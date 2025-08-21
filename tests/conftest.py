import pytest
import logging
from utils.teamcity_client import TeamCityClient
from utils.git_operations import GitOperations
from utils.test_helpers import TestHelpers
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def teamcity_client():
    """TeamCity client fixture."""
    client = TeamCityClient()
    yield client


@pytest.fixture(scope="session")
def git_operations():
    """Git operations fixture."""
    with GitOperations() as git_ops:
        yield git_ops


@pytest.fixture
def test_project_id():
    """Generate unique test project ID."""
    import uuid
    return f"TestProj_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def cleanup_project(teamcity_client):
    """Fixture to cleanup test projects after tests."""
    created_projects = []

    def register_project(project_id: str):
        created_projects.append(project_id)

    yield register_project

    # Cleanup
    for project_id in created_projects:
        try:
            teamcity_client.delete_project(project_id)
            logger.info(f"Cleaned up project: {project_id}")
        except Exception as e:
            logger.warning(f"Failed to cleanup project {project_id}: {e}")


@pytest.fixture
def sample_kotlin_dsl():
    """Sample Kotlin DSL content."""
    return '''
import jetbrains.buildServer.configs.kotlin.v2019_2.*
import jetbrains.buildServer.configs.kotlin.v2019_2.buildSteps.script

version = "2019.2"

project {
    buildType(Build)
}

object Build : BuildType({
    name = "Build"

    steps {
        script {
            scriptContent = "echo 'Hello from Kotlin DSL!'"
        }
    }
})
'''