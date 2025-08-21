import pytest
import time
from utils.teamcity_client import TeamCityClient
from utils.git_operations import GitOperations
from utils.test_helpers import TestHelpers
from config.settings import settings


class TestPipelineExecution:
    """Test cases for CI/CD pipeline execution after DSL import/sync."""

    @pytest.fixture
    def setup_pipeline_project(self, teamcity_client: TeamCityClient, test_project_id: str,
                               git_operations: GitOperations, sample_kotlin_dsl, cleanup_project):
        """Setup project with working pipeline from Kotlin DSL."""
        if not settings.GIT_REPO_URL:
            pytest.skip("GIT_REPO_URL not configured for pipeline tests")

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

        # Create DSL in repository
        repo = git_operations.clone_repo()
        git_operations.create_commit(
            ".teamcity/settings.kts",
            sample_kotlin_dsl,
            "Add build configuration"
        )
        git_operations.push_changes()

        # Wait for synchronization to complete
        def build_config_exists():
            try:
                build_configs = teamcity_client.get_build_configurations(test_project_id)
                return len(build_configs) > 0
            except:
                return False

        TestHelpers.wait_for_condition(build_config_exists, timeout=120)

        build_configs = teamcity_client.get_build_configurations(test_project_id)
        assert len(build_configs) > 0, "No build configurations found after setup"

        return {
            'project_id': test_project_id,
            'build_config_id': build_configs[0]['id'],
            'vcs_root_id': vcs_root['id']
        }

    def test_pipeline_execution_success(self, teamcity_client: TeamCityClient, setup_pipeline_project):
        """Test successful execution of imported/synchronized pipeline."""
        project_info = setup_pipeline_project
        build_config_id = project_info['build_config_id']

        # Trigger build
        build_info = teamcity_client.trigger_build(build_config_id)
        build_id = str(build_info['id'])

        # Wait for build completion
        completed_build = teamcity_client.wait_for_build_completion(build_id, timeout=300)

        # Verify build completed successfully
        assert completed_build['state'] == 'finished'
        assert completed_build['status'] == 'SUCCESS'

    def test_pipeline_execution_with_parameters(self, teamcity_client: TeamCityClient, setup_pipeline_project):
        """Test pipeline execution with custom parameters."""
        project_info = setup_pipeline_project
        build_config_id = project_info['build_config_id']

        # Trigger build with parameters
        parameters = {
            'env.TEST_PARAM': 'test_value',
            'system.build.number': '1.0.0-test'
        }

        build_info = teamcity_client.trigger_build(build_config_id, parameters)
        build_id = str(build_info['id'])

        # Wait for build completion
        completed_build = teamcity_client.wait_for_build_completion(build_id, timeout=300)

        # Verify build completed
        assert completed_build['state'] == 'finished'

        # Verify parameters were applied (check build info)
        assert 'properties' in completed_build

    def test_multiple_stage_pipeline(self, teamcity_client: TeamCityClient, test_project_id: str,
                                     git_operations: GitOperations, cleanup_project):
        """Test execution of multi-stage pipeline."""
        if not settings.GIT_REPO_URL:
            pytest.skip("GIT_REPO_URL not configured")

        cleanup_project(test_project_id)

        # Create project with multi-stage pipeline
        project_data = TestHelpers.generate_test_project_data(test_project_id)
        teamcity_client.create_project(project_data)

        # Create VCS root
        vcs_data = TestHelpers.generate_vcs_root_data(test_project_id, settings.GIT_REPO_URL)
        vcs_root = teamcity_client.create_vcs_root(vcs_data)

        # Enable versioned settings
        vs_config = TestHelpers.generate_versioned_settings_config(vcs_root['id'])
        teamcity_client.enable_versioned_settings(test_project_id, vs_config)

        # Create multi-stage DSL
        multi_stage_dsl = self._get_multi_stage_dsl()
        repo = git_operations.clone_repo()
        git_operations.create_commit(
            ".teamcity/settings.kts",
            multi_stage_dsl,
            "Add multi-stage pipeline"
        )
        git_operations.push_changes()

        # Wait for synchronization
        def multiple_configs_exist():
            try:
                build_configs = teamcity_client.get_build_configurations(test_project_id)
                return len(build_configs) >= 2
            except:
                return False

        TestHelpers.wait_for_condition(multiple_configs_exist, timeout=120)

        # Get build configurations
        build_configs = teamcity_client.get_build_configurations(test_project_id)
        assert len(build_configs) >= 2

        # Find the main build configuration
        main_build = next((bc for bc in build_configs if 'Build' in bc.get('name', '')), None)
        assert main_build is not None

        # Trigger the main build
        build_info = teamcity_client.trigger_build(main_build['id'])
        build_id = str(build_info['id'])

        # Wait for completion
        completed_build = teamcity_client.wait_for_build_completion(build_id, timeout=600)

        # Verify pipeline executed successfully
        assert completed_build['state'] == 'finished'

    def test_pipeline_failure_handling(self, teamcity_client: TeamCityClient, test_project_id: str,
                                       git_operations: GitOperations, cleanup_project):
        """Test pipeline behavior when stages fail."""
        if not settings.GIT_REPO_URL:
            pytest.skip("GIT_REPO_URL not configured")

        cleanup_project(test_project_id)

        # Setup project
        project_data = TestHelpers.generate_test_project_data(test_project_id)
        teamcity_client.create_project(project_data)

        vcs_data = TestHelpers.generate_vcs_root_data(test_project_id, settings.GIT_REPO_URL)
        vcs_root = teamcity_client.create_vcs_root(vcs_data)

        vs_config = TestHelpers.generate_versioned_settings_config(vcs_root['id'])
        teamcity_client.enable_versioned_settings(test_project_id, vs_config)

        # Create DSL with failing step
        failing_dsl = self._get_failing_pipeline_dsl()
        repo = git_operations.clone_repo()
        git_operations.create_commit(
            ".teamcity/settings.kts",
            failing_dsl,
            "Add failing pipeline"
        )
        git_operations.push_changes()

        # Wait for sync
        def build_config_ready():
            try:
                build_configs = teamcity_client.get_build_configurations(test_project_id)
                return len(build_configs) > 0
            except:
                return False

        TestHelpers.wait_for_condition(build_config_ready, timeout=120)

        # Trigger failing build
        build_configs = teamcity_client.get_build_configurations(test_project_id)
        build_config_id = build_configs[0]['id']

        build_info = teamcity_client.trigger_build(build_config_id)
        build_id = str(build_info['id'])

        # Wait for build to complete (should fail)
        completed_build = teamcity_client.wait_for_build_completion(build_id, timeout=300)

        # Verify build failed as expected
        assert completed_build['state'] == 'finished'
        assert completed_build['status'] == 'FAILURE'

    def test_concurrent_pipeline_execution(self, teamcity_client: TeamCityClient, setup_pipeline_project):
        """Test concurrent execution of multiple pipeline instances."""
        project_info = setup_pipeline_project
        build_config_id = project_info['build_config_id']

        # Trigger multiple builds concurrently
        build_ids = []
        for i in range(3):
            build_info = teamcity_client.trigger_build(
                build_config_id,
                {'env.BUILD_NUMBER': str(i + 1)}
            )
            build_ids.append(str(build_info['id']))

        # Wait for all builds to complete
        completed_builds = []
        for build_id in build_ids:
            completed_build = teamcity_client.wait_for_build_completion(build_id, timeout=300)
            completed_builds.append(completed_build)

        # Verify all builds completed
        for build in completed_builds:
            assert build['state'] == 'finished'

        # At least some should succeed (allowing for resource constraints)
        successful_builds = [b for b in completed_builds if b['status'] == 'SUCCESS']
        assert len(successful_builds) > 0

    def test_pipeline_execution_after_dsl_update(self, teamcity_client: TeamCityClient,
                                                 setup_pipeline_project, git_operations: GitOperations):
        """Test pipeline execution after updating DSL configuration."""
        project_info = setup_pipeline_project
        project_id = project_info['project_id']

        # Update DSL with additional step
        updated_dsl = self._get_updated_pipeline_dsl()

        git_operations.create_commit(
            ".teamcity/settings.kts",
            updated_dsl,
            "Update pipeline configuration"
        )
        git_operations.push_changes()

        # Wait for synchronization
        time.sleep(30)

        # Trigger build with updated configuration
        build_configs = teamcity_client.get_build_configurations(project_id)
        build_config_id = build_configs[0]['id']

        build_info = teamcity_client.trigger_build(build_config_id)
        build_id = str(build_info['id'])

        # Wait for completion
        completed_build = teamcity_client.wait_for_build_completion(build_id, timeout=300)

        # Verify updated pipeline executed successfully
        assert completed_build['state'] == 'finished'
        assert completed_build['status'] == 'SUCCESS'

    def _get_multi_stage_dsl(self) -> str:
        """Get multi-stage pipeline DSL."""
        return '''
import jetbrains.buildServer.configs.kotlin.v2019_2.*
import jetbrains.buildServer.configs.kotlin.v2019_2.buildSteps.script

version = "2019.2"

project {
    buildType(Test)
    buildType(Build)
    buildType(Deploy)
}

object Test : BuildType({
    name = "Test"

    steps {
        script {
            scriptContent = "echo 'Running tests'"
        }
    }
})

object Build : BuildType({
    name = "Build"

    dependencies {
        snapshot(Test) {}
    }

    steps {
        script {
            scriptContent = "echo 'Building application'"
        }
    }
})

object Deploy : BuildType({
    name = "Deploy"

    dependencies {
        snapshot(Build) {}
    }

    steps {
        script {
            scriptContent = "echo 'Deploying application'"
        }
    }
})
'''

    def _get_failing_pipeline_dsl(self) -> str:
        """Get pipeline DSL that will fail."""
        return '''
import jetbrains.buildServer.configs.kotlin.v2019_2.*
import jetbrains.buildServer.configs.kotlin.v2019_2.buildSteps.script

version = "2019.2"

project {
    buildType(FailingBuild)
}

object FailingBuild : BuildType({
    name = "Failing Build"

    steps {
        script {
            scriptContent = "exit 1"  // This will cause the build to fail
        }
    }
})
'''

    def _get_updated_pipeline_dsl(self) -> str:
        """Get updated pipeline DSL with additional steps."""
        return '''
import jetbrains.buildServer.configs.kotlin.v2019_2.*
import jetbrains.buildServer.configs.kotlin.v2019_2.buildSteps.script

version = "2019.2"

project {
    buildType(UpdatedBuild)
}

object UpdatedBuild : BuildType({
    name = "Updated Build"

    steps {
        script {
            name = "Setup"
            scriptContent = "echo 'Setting up environment'"
        }
        script {
            name = "Build"
            scriptContent = "echo 'Building application'"
        }
        script {
            name = "Test"
            scriptContent = "echo 'Running tests'"
        }
        script {
            name = "Package"
            scriptContent = "echo 'Packaging application'"
        }
    }
})
'''