import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    TEAMCITY_URL = os.getenv('TEAMCITY_URL', 'http://localhost:8111')
    TEAMCITY_USERNAME = os.getenv('TEAMCITY_USERNAME', 'admin')
    TEAMCITY_PASSWORD = os.getenv('TEAMCITY_PASSWORD', 'admin')
    TEAMCITY_TOKEN = os.getenv('TEAMCITY_TOKEN', '')

    GIT_REPO_URL = os.getenv('GIT_REPO_URL', '')
    GIT_USERNAME = os.getenv('GIT_USERNAME', '')
    GIT_TOKEN = os.getenv('GIT_TOKEN', '')

    TEST_PROJECT_ID = os.getenv('TEST_PROJECT_ID', 'TestProject')

    # Test configuration
    TIMEOUT = 30
    POLL_INTERVAL = 2
    MAX_RETRIES = 3

    @property
    def auth(self):
        if self.TEAMCITY_TOKEN:
            return {'Authorization': f'Bearer {self.TEAMCITY_TOKEN}'}
        return (self.TEAMCITY_USERNAME, self.TEAMCITY_PASSWORD)


settings = Settings()