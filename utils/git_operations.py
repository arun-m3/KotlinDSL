import git
import tempfile
import shutil
import os
from typing import Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class GitOperations:
    def __init__(self, repo_url: str = None):
        self.repo_url = repo_url or settings.GIT_REPO_URL
        self.temp_dir = None
        self.repo = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def clone_repo(self, target_dir: str = None) -> git.Repo:
        """Clone repository to temporary directory."""
        if not target_dir:
            self.temp_dir = tempfile.mkdtemp()
            target_dir = self.temp_dir

        try:
            self.repo = git.Repo.clone_from(self.repo_url, target_dir)
            logger.info(f"Repository cloned to {target_dir}")
            return self.repo
        except git.exc.GitCommandError as e:
            logger.error(f"Failed to clone repository: {e}")
            raise

    def create_commit(self, file_path: str, content: str, commit_message: str) -> str:
        """Create a commit with specified file changes."""
        if not self.repo:
            raise ValueError("Repository not initialized")

        full_path = os.path.join(self.repo.working_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w') as f:
            f.write(content)

        self.repo.index.add([file_path])
        commit = self.repo.index.commit(commit_message)

        logger.info(f"Created commit: {commit.hexsha}")
        return commit.hexsha

    def push_changes(self, branch: str = "main") -> bool:
        """Push changes to remote repository."""
        if not self.repo:
            raise ValueError("Repository not initialized")

        try:
            origin = self.repo.remote("origin")
            origin.push(branch)
            logger.info(f"Changes pushed to {branch}")
            return True
        except git.exc.GitCommandError as e:
            logger.error(f"Failed to push changes: {e}")
            return False

    def get_latest_commit_hash(self, branch: str = "main") -> str:
        """Get latest commit hash from branch."""
        if not self.repo:
            raise ValueError("Repository not initialized")

        return self.repo.commit(branch).hexsha

    def cleanup(self):
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")