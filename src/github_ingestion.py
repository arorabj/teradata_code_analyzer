"""
GitHub Ingestion Module
Handles cloning and updating GitHub repositories
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional
import tempfile


class GitHubIngestion:
    """Handle GitHub repository cloning and management"""
    
    def __init__(self, repo_url: str, branch: str = "main", token: Optional[str] = None):
        """
        Initialize GitHub ingestion
        
        Args:
            repo_url: GitHub repository URL
            branch: Branch to clone
            token: Optional GitHub personal access token
        """
        self.repo_url = repo_url
        self.branch = branch
        self.token = token
        self.local_path = None
        
        # Create workspace directory
        self.workspace = Path(tempfile.gettempdir()) / "teradata_lineage_workspace"
        self.workspace.mkdir(exist_ok=True)
        
    def _prepare_url_with_token(self) -> str:
        """Prepare repository URL with authentication token"""
        if not self.token:
            return self.repo_url
        
        # Insert token into HTTPS URL
        if self.repo_url.startswith("https://github.com/"):
            return self.repo_url.replace(
                "https://github.com/",
                f"https://{self.token}@github.com/"
            )
        
        return self.repo_url
    
    def clone_or_pull(self) -> Path:
        """
        Clone repository or pull latest changes if already exists
        
        Returns:
            Path to local repository
        """
        # Extract repo name from URL
        repo_name = self.repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        self.local_path = self.workspace / repo_name
        
        try:
            if self.local_path.exists():
                print(f"Repository exists, pulling latest changes...")
                self._pull_changes()
            else:
                print(f"Cloning repository...")
                self._clone_repo()
            
            return self.local_path
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Git operation failed: {e.stderr}")
    
    def _clone_repo(self):
        """Clone the repository"""
        url = self._prepare_url_with_token()
        
        cmd = [
            "git", "clone",
            "--depth", "1",  # Shallow clone for speed
            "--branch", self.branch,
            url,
            str(self.local_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"Repository cloned successfully to {self.local_path}")
    
    def _pull_changes(self):
        """Pull latest changes from remote"""
        original_dir = os.getcwd()
        
        try:
            os.chdir(self.local_path)
            
            # Reset any local changes
            subprocess.run(
                ["git", "reset", "--hard"],
                capture_output=True,
                check=True
            )
            
            # Pull latest
            subprocess.run(
                ["git", "pull", "origin", self.branch],
                capture_output=True,
                check=True
            )
            
            print(f"Repository updated successfully")
            
        finally:
            os.chdir(original_dir)
    
    def get_file_list(self, extensions: Optional[list] = None) -> list:
        """
        Get list of files in repository
        
        Args:
            extensions: List of file extensions to filter (e.g., ['.sql', '.ksh'])
        
        Returns:
            List of file paths
        """
        if not self.local_path or not self.local_path.exists():
            raise Exception("Repository not cloned yet")
        
        files = []
        
        for path in self.local_path.rglob('*'):
            if path.is_file():
                if extensions is None or path.suffix.lower() in extensions:
                    files.append(path)
        
        return files
    
    def read_file(self, file_path: Path) -> str:
        """
        Read file content
        
        Args:
            file_path: Path to file
        
        Returns:
            File content as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""
    
    def cleanup(self):
        """Remove local repository clone"""
        if self.local_path and self.local_path.exists():
            shutil.rmtree(self.local_path)
            print(f"Cleaned up {self.local_path}")