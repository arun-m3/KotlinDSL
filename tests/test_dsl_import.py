import pytest
import time
from utils.teamcity_client import TeamCityClient
from utils.test_helpers import TestHelpers
from config.settings import settings
from utils.git_operations import GitOperations


class TestDSLImport:
    # Test cases for DSL-based project import functionality.

    def test_project_basic(self, teamcity_client: TeamCityClient, test_project_id: str, cleanup_project):
        # Test basic project creation and retrieval.
        cleanup_project(test_project_id)

        # Create test project
        project_data = TestHelpers.generate_test_project_data(test_project_id)
        created_project = teamcity_client.create_project(project_data)

        # Verify project was created
        assert created_project['id'] == test_project_id
        assert created_project['name'] == project_data['name']

        # Verify project is accessible
        retrieved_project = teamcity_client.get_project(test_project_id)
        assert retrieved_project['id'] == test_project_id

    def test_import_with_vcs_integration(self, teamcity_client: TeamCityClient, test_project_id: str, cleanup_project):
        # Test import of project with VCS integration.
        cleanup_project(test_project_id)

        if not settings.GIT_REPO_URL:
            pytest.skip("GIT_REPO_URL not configured")

        # Create project
        project_data = TestHelpers.generate_test_project_data(test_project_id)
        teamcity_client.create_project(project_data)

        # Create VCS root
        vcs_data = TestHelpers.generate_vcs_root_data(test_project_id, settings.GIT_REPO_URL)
        vcs_root = teamcity_client.create_vcs_root(vcs_data)

        # Enable versioned settings
        vs_config = TestHelpers.generate_versioned_settings_config(vcs_root['id'])
        versioned_settings = teamcity_client.enable_versioned_settings(test_project_id, vs_config)

        # Verify versioned settings are enabled
        assert versioned_settings['synchronizationMode'] == "enabled"
        assert versioned_settings['vcsRootId'] == vcs_root['id']

    def test_project_usability_after_import(self, teamcity_client: TeamCityClient, test_project_id: str,
                                            cleanup_project):
        # Test that imported project is fully usable.
        cleanup_project(test_project_id)

        # Create and import project
        project_data = TestHelpers.generate_test_project_data(test_project_id)
        teamcity_client.create_project(project_data)

        # Wait for project to be fully initialized
        def project_ready():
            try:
                project = teamcity_client.get_project(test_project_id)
                return project.get('id') == test_project_id
            except:
                return False

        TestHelpers.wait_for_condition(project_ready, timeout=30)

        # Create VCS root
        vcs_data = TestHelpers.generate_vcs_root_data(test_project_id, settings.GIT_REPO_URL)
        vcs_root = teamcity_client.create_vcs_root(vcs_data)

        # Enable versioned settings
        vs_config = TestHelpers.generate_versioned_settings_config(vcs_root['id'])
        teamcity_client.enable_versioned_settings(test_project_id, vs_config)

        # Verify we can access project details
        project = teamcity_client.get_project(test_project_id)
        assert project['id'] == test_project_id

        # Wait for build configurations to be created from DSL import
        def build_configs_ready():
            try:
                build_configs = teamcity_client.get_build_configurations(test_project_id)
                # Check if we have the expected build configuration
                return (len(build_configs) > 0 and
                        any(config.get('name') == 'Build' for config in build_configs))
            except:
                return False

        # Wait up to 30 seconds for DSL import to complete
        TestHelpers.wait_for_condition(
            build_configs_ready,
            timeout=60,  # 30 seconds should be enough for DSL import
            poll_interval=5,  # Check every 5 seconds
            error_message="Build configurations were not created from DSL import within timeout"
        )
        # Verify we can get build configurations
        build_configs = teamcity_client.get_build_configurations(test_project_id)
        assert isinstance(build_configs, list)
        assert build_configs[0]['id'] == f"{test_project_id}_Build"

    def test_project_validation_errors(self, teamcity_client: TeamCityClient, test_project_id: str):
        # Test project validation with invalid data.

        # Test with invalid project data
        with pytest.raises(Exception):
            invalid_data = {"invalid": "data"}
            teamcity_client.create_project(invalid_data)

        # Test with duplicate project ID
        project_data = TestHelpers.generate_test_project_data(test_project_id)
        teamcity_client.create_project(project_data)

        with pytest.raises(Exception):
            teamcity_client.create_project(project_data)  # Duplicate, should throw an exception

        # Delete project
        teamcity_client.delete_project(test_project_id)
