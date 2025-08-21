#!/usr/bin/env python3
"""
Setup script for TeamCity test environment.
"""

import os
import sys
import time
import requests
from config.settings import settings
from utils.teamcity_client import TeamCityClient


def wait_for_teamcity():
    """Wait for TeamCity server to be ready."""
    print("Waiting for TeamCity server to start...")

    for attempt in range(60):  # Wait up to 10 minutes
        try:
            response = requests.get(f"{settings.TEAMCITY_URL}/app/rest/server",
                                    timeout=5, verify=False)
            if response.status_code == 200:
                print("TeamCity server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass

        print(f"Attempt {attempt + 1}/60 - TeamCity not ready yet...")
        time.sleep(10)

    print("TeamCity server failed to start within timeout")
    return False


def setup_admin_user():
    """Setup admin user if needed."""
    try:
        client = TeamCityClient()
        # Try to access projects to verify authentication
        projects = client.get_projects()
        print(f"Authentication successful. Found {len(projects)} projects.")
        return True
    except Exception as e:
        print(f"Authentication failed: {e}")
        print("Please setup admin user manually through TeamCity web UI")
        return False


def verify_setup():
    """Verify the test environment is properly configured."""
    print("Verifying test environment setup...")

    # Check TeamCity connectivity
    if not wait_for_teamcity():
        return False

    # Check authentication
    if not setup_admin_user():
        return False

    # Check environment variables
    required_vars = ['TEAMCITY_URL', 'TEAMCITY_USERNAME', 'TEAMCITY_PASSWORD']
    missing_vars = [var for var in required_vars if not getattr(settings, var)]

    if missing_vars:
        print(f"Missing required environment variables: {missing_vars}")
        return False

    print("Environment setup verification completed successfully!")
    return True


if __name__ == "__main__":
    if verify_setup():
        print("✅ Environment is ready for testing")
        sys.exit(0)
    else:
        print("❌ Environment setup failed")
        sys.exit(1)