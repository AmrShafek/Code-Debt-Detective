"""
Session Memory
Manages analysis session state, history, and context persistence
"""

import json
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime


class SessionMemory:
    """Manages analysis session state and persistence"""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("app") / "memory" / "sessions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._current_session: Optional[Dict[str, Any]] = None
        self._session_id: Optional[str] = None

    def new_session(self, repo_name: str) -> str:
        """Create a new analysis session"""
        timestamp = datetime.now()
        self._session_id = f"{repo_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        self._current_session = {
            "session_id": self._session_id,
            "repo_name": repo_name,
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
            "analysis_results": None,
            "refactoring_results": None,
            "state": "created"
        }
        return self._session_id

    def save_analysis(self, results: Dict[str, Any]):
        """Save analysis results to current session"""
        if not self._current_session:
            return

        self._current_session["analysis_results"] = results
        self._current_session["state"] = "analysis_complete"
        self._current_session["updated_at"] = datetime.now().isoformat()
        self._persist()

    def save_refactoring(self, results: Dict[str, Any]):
        """Save refactoring results to current session"""
        if not self._current_session:
            return

        self._current_session["refactoring_results"] = results
        self._current_session["state"] = "refactoring_complete"
        self._current_session["updated_at"] = datetime.now().isoformat()
        self._persist()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session by ID"""
        session_file = self.storage_dir / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, 'r') as f:
                return json.load(f)
        return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions"""
        sessions = []
        for f in sorted(self.storage_dir.glob("*.json"), reverse=True):
            try:
                with open(f, 'r') as sf:
                    session = json.load(sf)
                    sessions.append({
                        "session_id": session.get("session_id"),
                        "repo_name": session.get("repo_name"),
                        "created_at": session.get("created_at"),
                        "state": session.get("state")
                    })
            except:
                pass
        return sessions

    def get_current(self) -> Optional[Dict[str, Any]]:
        """Get current active session"""
        return self._current_session

    def get_analysis_results(self) -> Optional[Dict[str, Any]]:
        """Get analysis results from current session"""
        if self._current_session:
            return self._current_session.get("analysis_results")
        return None

    def get_refactoring_results(self) -> Optional[Dict[str, Any]]:
        """Get refactoring results from current session"""
        if self._current_session:
            return self._current_session.get("refactoring_results")
        return None

    def clear_current(self):
        """Clear the current session"""
        self._current_session = None
        self._session_id = None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session file"""
        session_file = self.storage_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        return False

    def _persist(self):
        """Persist current session to disk"""
        if not self._current_session or not self._session_id:
            return
        session_file = self.storage_dir / f"{self._session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(self._current_session, f, indent=2, default=str)
