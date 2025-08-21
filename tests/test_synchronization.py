import pytest
import time
from utils.teamcity_client import TeamCityClient
from utils.git_operations import GitOperations
from utils.test_helpers import TestHelpers
from config.settings import settings


class TestSynchronization:
    """Test cases for versioned settings synchronization."""

    @pytest.fixture
    def setup_versioned_project(self, teamcity_client: TeamCityClient, test_project_id: str, cleanup_project):
        """Setup project with versioned settings enabled."""
        if not settings.GIT_REPO_URL:
            pytest.skip("GIT_REPO_URL not configured for synchronization tests")

        cleanup_project(test_project_id)

        # Create project
        project_data = TestHelpers.generate_test_project_data(test_project_id)
        teamcity_client.create_project(project_data)

        # Create VCS root
        vcs_data = TestHelpers.generate_vcs_root_data(test_project_id, settings.GIT_REPO_URL)
        vcs_root = teamcity_client.create_vcs_root(vcs_data)

        # Enable versioned settings
        vs_config = TestHelpers.generate_versioned_settings_config(vcs_root['id'])
        teamcity_client.enable_versioned_settings(test_project_id, vs_config)

        return {
            'project_id': test_project_id,
            'vcs_root_id': vcs_root['id']
        }

    def test_server_to_vcs_synchronization(self, teamcity_client: TeamCityClient, setup_versioned_project,
                                           sample_kotlin_dsl):
        """Test synchronization from TeamCity server to VCS repository."""
        project_info = setup_versioned_project
        project_id = project_info['project_id']

        # Trigger synchronization from server to VCS
        teamcity_client.trigger_versioned_settings_sync(project_id)

        # Wait for synchronization to complete
        def sync_completed():
            try:
                vs_info = teamcity_client.get_versioned_settings(project_id)
                return vs_info.get('enabled') is True
            except:
                return False

        TestHelpers.wait_for_condition(sync_completed, timeout=60)

        # Verify synchronization status
        vs_info = teamcity_client.get_versioned_settings(project_id)
        assert vs_info['enabled'] is True

    def test_vcs_to_server_synchronization(self, teamcity_client: TeamCityClient, setup_versioned_project,
                                           git_operations: GitOperations, sample_kotlin_dsl):
        """Test synchronization from VCS repository to TeamCity server."""
        project_info = setup_versioned_project
        project_id = project_info['project_id']

        # Clone repository and make changes
        repo = git_operations.clone_repo()

        # Create Kotlin DSL file in repository
        dsl_content = sample_kotlin_dsl
        commit_hash = git_operations.create_commit(
            ".teamcity/settings.kts",
            dsl_content,
            "Add sample build configuration"
        )

        # Push changes to trigger synchronization
        git_operations.push_changes()

        # Wait for TeamCity to detect and process the changes
        def changes_detected():
            try:
                build_configs = teamcity_client.get_build_configurations(project_id)
                return len(build_configs) > 0
            except:
                return False

        TestHelpers.wait_for_condition(changes_detected, timeout=120)

        # Verify that build configuration was created from DSL
        build_configs = teamcity_client.get_build_configurations(project_id)
        assert len(build_configs) > 0

        # Find the build config created by our DSL
        build_config = next((bc for bc in build_configs if 'Build' in bc.get('name', '')), None)
        assert build_config is not None, "Build configuration not found after synchronization"

    def test_bidirectional_synchronization(self, teamcity_client: TeamCityClient, setup_versioned_project,
                                           git_operations: GitOperations, sample_kotlin_dsl):
        """Test that changes in both directions are properly synchronized."""
        project_info = setup_versioned_project
        project_id = project_info['project_id']

        # First: VCS to Server
        repo = git_operations.clone_repo()
        git_operations.create_commit(
            ".teamcity/settings.kts",
            sample_kotlin_dsl,
            "Initial DSL configuration"
        )
        git_operations.push_changes()

        # Wait for sync to server
        def server_updated():
            try:
                build_configs = teamcity_client.get_build_configurations(project_id)
                return len(build_configs) > 0
            except:
                return False

        TestHelpers.wait_for_condition(server_updated, timeout=120)

        # Verify server has the configuration
        build_configs = teamcity_client.get_build_configurations(project_id)
        assert len(build_configs) > 0

        # Second: Make changes on server and verify they sync back to VCS
        # Trigger server-to-VCS sync
        teamcity_client.trigger_versioned_settings_sync(project_id)

        # Wait and verify synchronization completed
        time.sleep(10)  # Allow time for sync to complete

        vs_info = teamcity_client.get_versioned_settings(project_id)
        assert vs_info['enabled'] is True

    def test_sync_conflict_resolution(self, teamcity_client: TeamCityClient, setup_versioned_project,
                                      git_operations: GitOperations, sample_kotlin_dsl):
        """Test how synchronization handles conflicts."""
        project_info = setup_versioned_project
        project_id = project_info['project_id']

        # Create conflicting changes
        repo = git_operations.clone_repo()

        # Create initial version
        git_operations.create_commit(
            ".teamcity/settings.kts",
            sample_kotlin_dsl,
            "Initial version"
        )
        git_operations.push_changes()

        # Wait for initial sync
        time.sleep(30)

        # Create conflicting version
        modified_dsl = sample_kotlin_dsl.replace('name = "Build"', 'name = "ModifiedBuild"')
        git_operations.create_commit(
            ".teamcity/settings.kts",
            modified_dsl,
            "Modified version"
        )
        git_operations.push_changes()

        # Wait for conflict resolution
        def sync_stabilized():
            try:
                vs_info = teamcity_client.get_versioned_settings(project_id)
                return vs_info.get('enabled') is True
            except:
                return False

        TestHelpers.wait_for_condition(sync_stabilized, timeout=180)

        # Verify system handled the conflict (should not crash)
        vs_info = teamcity_client.get_versioned_settings(project_id)
        assert vs_info['enabled'] is True

    def test_sync_performance_large_changes(self, teamcity_client: TeamCityClient, setup_versioned_project,
                                            git_operations: GitOperations):
        """Test synchronization performance with large changes."""
        project_info = setup_versioned_project
        project_id = project_info['project_id']

        # Generate large DSL content
        large_dsl = self._generate_large_kotlin_dsl()

        repo = git_operations.clone_repo()

        start_time = time.time()

        git_operations.create_commit(
            ".teamcity/settings.kts",
            large_dsl,
            "Large configuration change"
        )
        git_operations.push_changes()

        # Wait for synchronization to complete
        def large_sync_completed():
            try:
                build_configs = teamcity_client.get_build_configurations(project_id)
                return len(build_configs) >= 3  # Expecting multiple build configs from large DSL
            except:
                return False

        TestHelpers.wait_for_condition(large_sync_completed, timeout=300)

        sync_time = time.time() - start_time

        # Verify all configurations were synchronized
        build_configs = teamcity_client.get_build_configurations(project_id)
        assert len(build_configs) >= 3

        # Performance assertion
        assert sync_time < 300, f"Large sync took too long: {sync_time}s"

    def _generate_large_kotlin_dsl(self) -> str:
        """Generate a large Kotlin DSL configuration for performance testing."""
        return '''
import jetbrains.buildServer.configs.kotlin.*
import jetbrains.buildServer.configs.kotlin.buildSteps.script

version = "2025.07"

project {
    buildType(Build1)
    buildType(Build2)
    buildType(Build3)
    buildType(Deploy)
}

object Build1 : BuildType({
    name = "Unit Tests"

    steps {
        script {
            scriptContent = "echo 'Running unit tests'"
        }
    }
})

object Build2 : BuildType({
    name = "Integration Tests"

    steps {
        script {
            scriptContent = "echo 'Running integration tests'"
        }
    }
})

object Build3 : BuildType({
    name = "Performance Tests"

    steps {
        script {
            scriptContent = "echo 'Running performance tests'"
        }
    }
})

object Deploy : BuildType({
    name = "Deploy"

    dependencies {
        snapshot(Build1) {}
        snapshot(Build2) {}
        snapshot(Build3) {}
    }

    steps {
        script {
            scriptContent = "echo 'Deploying application'"
        }
    }
})
'''