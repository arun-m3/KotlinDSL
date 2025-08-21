import requests
import time
import json
from typing import Dict, Any, Optional, List
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class TeamCityClient:
    def __init__(self):
        self.base_url = settings.TEAMCITY_URL
        self.auth = settings.auth
        self.session = requests.Session()

        if isinstance(self.auth, tuple):
            self.session.auth = self.auth
        else:
            self.session.headers.update(self.auth)

        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling and retries."""
        url = f"{self.base_url}/app/rest{endpoint}"

        for attempt in range(settings.MAX_RETRIES):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == settings.MAX_RETRIES - 1:
                    raise
                time.sleep(settings.POLL_INTERVAL)

    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects."""
        response = self._make_request('GET', '/projects')
        return response.json().get('project', [])

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get specific project details."""
        response = self._make_request('GET', f'/projects/{project_id}')
        return response.json()

    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project."""
        response = self._make_request('POST', '/projects', json=project_data)
        return response.json()

    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        try:
            self._make_request('DELETE', f'/projects/{project_id}')
            return True
        except requests.exceptions.RequestException:
            return False

    def get_versioned_settings(self, project_id: str) -> Dict[str, Any]:
        """Get versioned settings for a project."""
        response = self._make_request('GET', f'/projects/id:{project_id}/versionedSettings/status')
        return response.json()

    def enable_versioned_settings(self, project_id: str, vcs_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Enable versioned settings for a project."""
        response = self._make_request('PUT', f'/projects/{project_id}/versionedSettings/config', json=vcs_settings)
        return response.json()

    def trigger_versioned_settings_sync(self, project_id: str) -> Dict[str, Any]:
        """Trigger synchronization of versioned settings."""
        response = self._make_request('POST', f'/projects/{project_id}/versionedSettings/synchronize')
        return response.json()

    def get_build_configurations(self, project_id: str) -> List[Dict[str, Any]]:
        """Get build configurations for a project."""
        response = self._make_request('GET', f'/buildTypes?locator=project:{project_id}')
        return response.json().get('buildType')

    def trigger_build(self, build_config_id: str, properties: Dict[str, str] = None) -> Dict[str, Any]:
        """Trigger a build."""
        build_data = {
            'buildType': {'id': build_config_id}
        }
        if properties:
            build_data['properties'] = {
                'property': [{'name': k, 'value': v} for k, v in properties.items()]
            }

        response = self._make_request('POST', '/buildQueue', json=build_data)
        return response.json()

    def get_build_status(self, build_id: str) -> Dict[str, Any]:
        """Get build status."""
        response = self._make_request('GET', f'/builds/{build_id}')
        return response.json()

    def wait_for_build_completion(self, build_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for build to complete."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            build_info = self.get_build_status(build_id)
            state = build_info.get('state')

            if state in ['finished', 'canceled']:
                return build_info
            elif state == 'running':
                time.sleep(settings.POLL_INTERVAL)
            else:
                time.sleep(settings.POLL_INTERVAL)

        raise TimeoutError(f"Build {build_id} did not complete within {timeout} seconds")

    def get_vcs_roots(self, project_id: str = None) -> List[Dict[str, Any]]:
        """Get VCS roots."""
        endpoint = '/vcs-roots'
        if project_id:
            endpoint += f'?locator=project:{project_id}'

        response = self._make_request('GET', endpoint)
        return response.json().get('vcs-root', [])

    def create_vcs_root(self, vcs_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a VCS root."""
        response = self._make_request('POST', '/vcs-roots', json=vcs_data)
        return response.json()