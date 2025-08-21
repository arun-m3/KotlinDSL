import time
import json
from typing import Dict, Any, Callable
from config.settings import settings
from utils.dsl_loader import DSLTemplateLoader
import logging

logger = logging.getLogger(__name__)


class TestHelpers:
    @staticmethod
    def wait_for_condition(condition_func: Callable[[], bool],
                           timeout: int = settings.TIMEOUT,
                           poll_interval: int = settings.POLL_INTERVAL,
                           error_message: str = "Condition not met within timeout") -> bool:
        """Wait for a condition to be true."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(poll_interval)

        raise TimeoutError(error_message)

    @staticmethod
    def validate_kotlin_dsl_structure(project_data: Dict[str, Any]) -> bool:
        """Validate that project has proper Kotlin DSL structure."""
        required_fields = ['id', 'name', 'versionedSettingsConfig']
        return all(field in project_data for field in required_fields)

    @staticmethod
    def generate_test_project_data(project_id: str) -> Dict[str, Any]:
        """Generate test project data."""
        return {
            "id": project_id,
            "name": f"Test Project {project_id}",
            "description": "Automated test project for Kotlin DSL validation"
        }

    @staticmethod
    def generate_vcs_root_data(project_id: str, repo_url: str) -> Dict[str, Any]:
        """Generate VCS root configuration."""
        return {
            "name": f"{project_id}_VCS",
            "vcsName": "jetbrains.git",
            "project": {"id": project_id},
            "properties": {
                "property": [
                    {"name": "url", "value": repo_url},
                    {"name": "branch", "value": "refs/heads/main"},
                    {"name": "authMethod", "value": "PASSWORD"},
                    {"name": "username", "value": settings.GIT_USERNAME},
                    {"name": "secure:password", "value": settings.GIT_TOKEN}
                ]
            }
        }

    @staticmethod
    def generate_versioned_settings_config(vcs_root_id: str) -> Dict[str, Any]:
        """Generate versioned settings configuration."""
        return {
            "format": "kotlin",
            "synchronizationMode": "enabled",
            "allowUIEditing": True,
            "storeSecureValuesOutsideVcs": True,
            "vcsRootId": vcs_root_id,
            "importDecision": "importFromVCS",
            "buildSettingsMode": "useFromVCS"
        }

    @staticmethod
    def load_expected_response(filename: str) -> Dict[str, Any]:
        """Load expected response from test data."""
        with open(f"test_data/expected_responses/{filename}", 'r') as f:
            return json.load(f)

    # @staticmethod
    # def get_dsl_template(template_name: str, **kwargs) -> str:
    #     """
    #     Get DSL template with variable substitution.
    #
    #     Args:
    #         template_name: Template name (e.g., 'simple_build', 'large_project')
    #         **kwargs: Variables to substitute in template
    #
    #     Returns:
    #         Processed DSL content
    #     """
    #     loader = DSLTemplateLoader()
    #     return loader.load_template(template_name, **kwargs)
    #
    # @staticmethod
    # def generate_large_kotlin_dsl(project_id: str) -> str:
    #     """Generate large Kotlin DSL using template file."""
    #     return TestHelpers.get_dsl_template(
    #         'large_project',
    #         project_id=project_id,
    #         project_description=f"Large performance test project for {project_id}",
    #         build_environment="performance_test"
    #     )
    #
    # @staticmethod
    # def generate_dsl_with_n_builds(build_count: int, project_id: str = "TestProject") -> str:
    #     """Generate DSL with N builds using template."""
    #     loader = DSLTemplateLoader()
    #     return loader.load_parametrized_template(
    #         'multi_build_template',
    #         {
    #             'project_id': project_id,
    #             'build_count': build_count,
    #             'project_description': f"Multi-build project with {build_count} builds"
    #         }
    #     )
