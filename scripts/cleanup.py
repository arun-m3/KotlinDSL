#!/usr/bin/env python3
"""
Cleanup script for test environment.
"""

import sys
from utils.teamcity_client import TeamCityClient


def cleanup_test_projects():
    """Remove all test projects created during testing."""
    try:
        client = TeamCityClient()
        projects = client.get_projects()

        test_projects = [p for p in projects if p['id'].startswith('Test')]

        print(f"Found {len(test_projects)} test projects to cleanup")

        for project in test_projects:
            try:
                client.delete_project(project['id'])
                print(f"✅ Deleted project: {project['id']}")
            except Exception as e:
                print(f"❌ Failed to delete project {project['id']}: {e}")

        print("Cleanup completed")
        return True

    except Exception as e:
        print(f"Cleanup failed: {e}")
        return False


if __name__ == "__main__":
    if cleanup_test_projects():
        sys.exit(0)
    else:
        sys.exit(1)