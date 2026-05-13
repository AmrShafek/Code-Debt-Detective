"""
Repository Scanner
Handles repository discovery, cloning, and path management
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class RepoScanner:
    """Scans and manages code repositories for analysis"""

    def __init__(self, repos_base_dir: Optional[Path] = None):
        self.repos_base = repos_base_dir or Path("repos") / "scanned_projects"
        self.repos_base.mkdir(parents=True, exist_ok=True)

    def list_local_repos(self) -> List[Dict[str, Any]]:
        """List all locally available repositories"""
        repos = []
        if not self.repos_base.exists():
            return repos

        for item in self.repos_base.iterdir():
            if item.is_dir():
                is_git = (item / ".git").exists()
                repo_info = {
                    "name": item.name,
                    "path": str(item),
                    "is_git_repo": is_git,
                    "size_bytes": self._get_dir_size(item),
                    "last_modified": datetime.fromtimestamp(
                        item.stat().st_mtime
                    ).isoformat()
                }
                repos.append(repo_info)

        return sorted(repos, key=lambda r: r["last_modified"], reverse=True)

    def clone_repository(self, url: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """Clone a git repository for analysis"""
        repo_name = url.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        target_path = self.repos_base / repo_name

        if target_path.exists():
            return {
                "success": True,
                "path": str(target_path),
                "name": repo_name,
                "message": "Repository already exists"
            }

        try:
            cmd = ["git", "clone", url, str(target_path)]
            if branch:
                cmd.extend(["--branch", branch])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr,
                    "name": repo_name
                }

            return {
                "success": True,
                "path": str(target_path),
                "name": repo_name,
                "message": "Repository cloned successfully"
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Clone timed out", "name": repo_name}
        except Exception as e:
            return {"success": False, "error": str(e), "name": repo_name}

    def scan_directory(self, path: str) -> Dict[str, Any]:
        """Scan a local directory as a repository"""
        target = Path(path)
        if not target.exists():
            return {"success": False, "error": f"Path does not exist: {path}"}

        if not target.is_dir():
            return {"success": False, "error": f"Path is not a directory: {path}"}

        repo_name = target.name
        target_path = self.repos_base / repo_name

        if not target_path.exists():
            shutil.copytree(
                target, target_path,
                ignore=shutil.ignore_patterns(
                    ".git", "__pycache__", "node_modules", ".venv", "venv"
                )
            )

        return {
            "success": True,
            "path": str(target_path),
            "name": repo_name,
            "is_git_repo": (target / ".git").exists(),
            "file_count": self._count_files(target_path)
        }

    def remove_repo(self, name: str) -> bool:
        """Remove a scanned repository"""
        target = self.repos_base / name
        if target.exists():
            shutil.rmtree(target)
            return True
        return False

    def get_repo_path(self, name: str) -> Optional[str]:
        """Get the full path to a repository by name"""
        target = self.repos_base / name
        return str(target) if target.exists() else None

    def _get_dir_size(self, path: Path) -> int:
        total = 0
        for f in path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total

    def _count_files(self, path: Path) -> int:
        return sum(1 for f in path.rglob("*") if f.is_file())
