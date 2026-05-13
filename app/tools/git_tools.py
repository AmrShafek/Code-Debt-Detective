"""
Git Analysis Tools
Provides version control analysis, code ownership, change frequency, and commit pattern detection
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from crewai_tools import tool

# Shared analysis cache for inter-agent communication
_analysis_cache = {}


def _run_git_command(directory: str, command: List[str]) -> Tuple[str, str, int]:
    """Execute a git command and return stdout, stderr, returncode"""
    try:
        result = subprocess.run(
            ['git'] + command,
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except FileNotFoundError:
        return "", "Git not found in PATH", 127
    except Exception as e:
        return "", str(e), 1


def _is_git_repo(directory: str) -> bool:
    """Check if directory is a git repository"""
    _, _, code = _run_git_command(directory, ['rev-parse', '--git-dir'])
    return code == 0


@tool
def get_git_history(directory: str, max_commits: int = 100, since: str = "") -> dict:
    """
    Retrieves commit history with metadata for change analysis

    Args:
        directory: Path to the git repository
        max_commits: Maximum number of commits to retrieve
        since: Git date format string (e.g., '3 months ago', '2024-01-01')

    Returns:
        Dict with commit log, author statistics, and temporal patterns
    """
    if not _is_git_repo(directory):
        return {"error": "Not a git repository", "is_git_repo": False}

    try:
        # Build git log command
        format_str = '%H|%an|%ae|%ad|%s|%D'
        cmd = ['log', f'--pretty=format:{format_str}', '--date=short', f'-n{max_commits}']
        if since:
            cmd.extend(['--since', since])

        stdout, stderr, code = _run_git_command(directory, cmd)

        if code != 0:
            return {"error": stderr, "is_git_repo": True}

        commits = []
        author_stats = defaultdict(lambda: {"commits": 0, "files_changed": 0, "insertions": 0, "deletions": 0})
        daily_commits = defaultdict(int)

        for line in stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split('|')
            if len(parts) >= 5:
                commit_hash, author, email, date, message = parts[:5]
                refs = parts[5] if len(parts) > 5 else ''

                commits.append({
                    "hash": commit_hash[:8],
                    "full_hash": commit_hash,
                    "author": author,
                    "email": email,
                    "date": date,
                    "message": message,
                    "refs": refs
                })

                author_stats[author]["commits"] += 1
                daily_commits[date] += 1

        # Get stats per commit (expensive, so limit to recent)
        for commit in commits[:50]:
            stat_cmd = ['show', '--stat', '--format=', commit["full_hash"]]
            stat_out, _, _ = _run_git_command(directory, stat_cmd)

            files_changed = 0
            insertions = 0
            deletions = 0

            for stat_line in stat_out.split('\n'):
                # Match lines like: " 5 files changed, 10 insertions(+), 3 deletions(-)"
                match = re.search(r'(\d+) files? changed(?:, (\d+) insertions?\(\+\))?(?:, (\d+) deletions?\(-\))?', stat_line)
                if match:
                    files_changed = int(match.group(1) or 0)
                    insertions = int(match.group(2) or 0)
                    deletions = int(match.group(3) or 0)

            author_stats[commit["author"]]["files_changed"] += files_changed
            author_stats[commit["author"]]["insertions"] += insertions
            author_stats[commit["author"]]["deletions"] += deletions

            commit["files_changed"] = files_changed
            commit["insertions"] = insertions
            commit["deletions"] = deletions

        # Calculate velocity metrics
        if daily_commits:
            dates = sorted(daily_commits.keys())
            date_range = (datetime.strptime(dates[-1], '%Y-%m-%d') - datetime.strptime(dates[0], '%Y-%m-%d')).days
            avg_commits_per_day = round(len(commits) / max(date_range, 1), 2)
        else:
            avg_commits_per_day = 0

        result = {
            "commits": commits,
            "total_commits": len(commits),
            "author_statistics": dict(author_stats),
            "unique_authors": len(author_stats),
            "daily_commit_distribution": dict(daily_commits),
            "avg_commits_per_day": avg_commits_per_day,
            "most_active_author": max(author_stats.items(), key=lambda x: x[1]["commits"])[0] if author_stats else None,
            "is_git_repo": True
        }

        _analysis_cache['git_history'] = result
        return result
    except Exception as e:
        return {"error": str(e), "is_git_repo": True}


@tool
def get_file_blame(directory: str, file_path: str, line_range: str = "") -> dict:
    """
    Retrieves git blame information for a specific file to identify code ownership

    Args:
        directory: Path to the git repository
        file_path: Relative path to the file
        line_range: Optional line range (e.g., '10,50' for lines 10-50)

    Returns:
        Dict with line-by-line ownership, author contributions, and age metrics
    """
    if not _is_git_repo(directory):
        return {"error": "Not a git repository", "is_git_repo": False}

    try:
        cmd = ['blame', '--line-porcelain', file_path]
        if line_range:
            cmd.extend(['-L', line_range])

        stdout, stderr, code = _run_git_command(directory, cmd)

        if code != 0:
            return {"error": stderr, "file": file_path, "is_git_repo": True}

        lines = []
        author_lines = defaultdict(int)
        author_ages = defaultdict(list)

        current_line = {}
        for line in stdout.split('\n'):
            if line.startswith('author '):
                current_line['author'] = line[7:]
            elif line.startswith('author-mail '):
                current_line['email'] = line[12:].strip('<>')
            elif line.startswith('author-time '):
                timestamp = int(line[12:])
                current_line['date'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                current_line['age_days'] = (datetime.now() - datetime.fromtimestamp(timestamp)).days
            elif line.startswith('\t'):
                current_line['code'] = line[1:]
                lines.append(current_line)

                if 'author' in current_line:
                    author_lines[current_line['author']] += 1
                    author_ages[current_line['author']].append(current_line.get('age_days', 0))

                current_line = {}

        # Calculate ownership percentages
        total_lines = len(lines)
        ownership = []
        for author, count in sorted(author_lines.items(), key=lambda x: x[1], reverse=True):
            avg_age = round(sum(author_ages[author]) / len(author_ages[author]), 1) if author_ages[author] else 0
            ownership.append({
                "author": author,
                "lines": count,
                "percentage": round(count / total_lines * 100, 1) if total_lines > 0 else 0,
                "avg_line_age_days": avg_age
            })

        result = {
            "file": file_path,
            "total_lines": total_lines,
            "ownership": ownership,
            "primary_author": ownership[0]["author"] if ownership else None,
            "ownership_concentration": round(ownership[0]["percentage"], 1) if ownership else 0,
            "bus_factor": len([o for o in ownership if o["percentage"] > 10]),
            "lines": lines[:50] if len(lines) > 50 else lines,  # Limit output
            "is_git_repo": True
        }

        return result
    except Exception as e:
        return {"error": str(e), "file": file_path, "is_git_repo": True}


@tool
def detect_churn(directory: str, top_n: int = 20, since: str = "6 months ago") -> dict:
    """
    Detects high-churn files (frequently modified files) that indicate instability or technical debt

    Args:
        directory: Path to the git repository
        top_n: Number of top churning files to return
        since: Time period for analysis (e.g., '3 months ago', '1 year ago')

    Returns:
        Dict with churn hotspots, change frequency, and risk indicators
    """
    if not _is_git_repo(directory):
        return {"error": "Not a git repository", "is_git_repo": False}

    try:
        # Get file change statistics
        cmd = ['log', '--pretty=format:', '--name-only', '--since', since, '--']
        stdout, stderr, code = _run_git_command(directory, cmd)

        if code != 0:
            return {"error": stderr, "is_git_repo": True}

        file_changes = defaultdict(lambda: {"commits": 0, "authors": set(), "last_modified": None})

        current_commit_files = set()
        for line in stdout.split('\n'):
            line = line.strip()
            if not line:
                # Commit boundary - increment counters
                for f in current_commit_files:
                    file_changes[f]["commits"] += 1
                current_commit_files = set()
            elif line.endswith('.py') or line.endswith('.js') or line.endswith('.ts'):
                current_commit_files.add(line)

        # Get last modification dates
        for file_path in list(file_changes.keys())[:100]:  # Limit for performance
            date_cmd = ['log', '-1', '--pretty=format:%ad', '--date=short', '--', file_path]
            date_out, _, _ = _run_git_command(directory, date_cmd)
            if date_out:
                file_changes[file_path]["last_modified"] = date_out.strip()

        # Get author counts
        for file_path in list(file_changes.keys())[:50]:
            auth_cmd = ['log', '--pretty=format:%an', '--since', since, '--', file_path]
            auth_out, _, _ = _run_git_command(directory, auth_cmd)
            authors = set(a for a in auth_out.split('\n') if a)
            file_changes[file_path]["authors"] = authors
            file_changes[file_path]["author_count"] = len(authors)

        # Convert to list and calculate metrics
        churn_data = []
        for file_path, data in file_changes.items():
            if data["commits"] > 0:
                # Churn score = commits * author_count (higher = more problematic)
                churn_score = data["commits"] * (1 + data.get("author_count", 1) * 0.5)

                churn_data.append({
                    "file": file_path,
                    "commits": data["commits"],
                    "author_count": data.get("author_count", 1),
                    "last_modified": data["last_modified"],
                    "churn_score": round(churn_score, 1),
                    "risk_level": (
                        "critical" if churn_score > 20 else
                        "high" if churn_score > 10 else
                        "medium" if churn_score > 5 else "low"
                    )
                })

        churn_data.sort(key=lambda x: x['churn_score'], reverse=True)

        # Identify churn patterns
        high_churn = [c for c in churn_data if c["risk_level"] in ("critical", "high")]

        result = {
            "hotspots": churn_data[:top_n],
            "total_files_tracked": len(churn_data),
            "high_churn_files": len(high_churn),
            "avg_commits_per_file": round(
                sum(c["commits"] for c in churn_data) / len(churn_data), 1
            ) if churn_data else 0,
            "period": since,
            "is_git_repo": True
        }

        _analysis_cache['churn'] = result
        return result
    except Exception as e:
        return {"error": str(e), "is_git_repo": True}


@tool
def get_recent_changes(directory: str, file_path: str = "", max_commits: int = 10) -> dict:
    """
    Retrieves recent commits affecting a specific file or the entire repository

    Args:
        directory: Path to the git repository
        file_path: Optional specific file to check (empty for entire repo)
        max_commits: Maximum number of commits to retrieve

    Returns:
        Dict with recent changes, diffs summary, and impact assessment
    """
    if not _is_git_repo(directory):
        return {"error": "Not a git repository", "is_git_repo": False}

    try:
        cmd = ['log', f'-n{max_commits}', '--pretty=format:%H|%an|%ad|%s', '--date=short', '--stat']
        if file_path:
            cmd.extend(['--', file_path])

        stdout, stderr, code = _run_git_command(directory, cmd)

        if code != 0:
            return {"error": stderr, "is_git_repo": True}

        changes = []
        current_change = None

        for line in stdout.split('\n'):
            if '|' in line and not line.startswith(' '):
                parts = line.split('|')
                if len(parts) >= 4:
                    if current_change:
                        changes.append(current_change)

                    current_change = {
                        "hash": parts[0][:8],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3],
                        "files": [],
                        "total_insertions": 0,
                        "total_deletions": 0
                    }
            elif '|' in line and ('+' in line or '-' in line):
                # File stat line: " file.py | 10 +++----"
                file_match = re.match(r'\s*(.+?)\s*\|\s*(\d+)\s*([+-]*)', line)
                if file_match and current_change:
                    filename = file_match.group(1).strip()
                    changes_count = int(file_match.group(2))
                    signs = file_match.group(3)
                    insertions = signs.count('+')
                    deletions = signs.count('-')

                    current_change["files"].append({
                        "file": filename,
                        "changes": changes_count,
                        "insertions": insertions,
                        "deletions": deletions
                    })
                    current_change["total_insertions"] += insertions
                    current_change["total_deletions"] += deletions
            elif 'files changed' in line and current_change:
                match = re.search(r'(\d+) files? changed(?:, (\d+) insertions?\(\+\))?(?:, (\d+) deletions?\(-\))?', line)
                if match:
                    current_change["files_changed"] = int(match.group(1) or 0)
                    current_change["total_insertions"] = int(match.group(2) or 0)
                    current_change["total_deletions"] = int(match.group(3) or 0)

        if current_change:
            changes.append(current_change)

        # Calculate change impact
        for change in changes:
            change["impact_score"] = (
                change.get("files_changed", 0) * 2 +
                change.get("total_insertions", 0) +
                change.get("total_deletions", 0)
            )
            change["is_large_change"] = change["impact_score"] > 50
            change["is_refactoring"] = "refactor" in change["message"].lower() or change.get("total_deletions", 0) > change.get("total_insertions", 0) * 2

        result = {
            "changes": changes,
            "target": file_path or "entire repository",
            "total_changes": len(changes),
            "large_changes": sum(1 for c in changes if c.get("is_large_change")),
            "refactoring_commits": sum(1 for c in changes if c.get("is_refactoring")),
            "is_git_repo": True
        }

        return result
    except Exception as e:
        return {"error": str(e), "is_git_repo": True}


@tool
def analyze_commit_patterns(directory: str, since: str = "6 months ago") -> dict:
    """
    Analyzes commit patterns to detect process issues, review gaps, and development velocity

    Args:
        directory: Path to the git repository
        since: Time period for analysis

    Returns:
        Dict with commit patterns, quality indicators, and process recommendations
    """
    if not _is_git_repo(directory):
        return {"error": "Not a git repository", "is_git_repo": False}

    try:
        # Get detailed commit log
        cmd = ['log', f'--since={since}', '--pretty=format:%H|%an|%ae|%ad|%s', '--date=short']
        stdout, stderr, code = _run_git_command(directory, cmd)

        if code != 0:
            return {"error": stderr, "is_git_repo": True}

        commits = []
        author_commits = defaultdict(list)
        daily_counts = defaultdict(int)
        message_lengths = []

        for line in stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 5:
                commit = {
                    "hash": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "date": parts[3],
                    "message": parts[4]
                }
                commits.append(commit)
                author_commits[parts[1]].append(parts[3])
                daily_counts[parts[3]] += 1
                message_lengths.append(len(parts[4]))

        # Analyze patterns
        patterns = {
            "total_commits": len(commits),
            "unique_authors": len(author_commits),
            "avg_message_length": round(sum(message_lengths) / len(message_lengths), 1) if message_lengths else 0,
            "short_messages": sum(1 for m in message_lengths if m < 10),
            "conventional_commits": sum(
                1 for c in commits 
                if re.match(r'^(feat|fix|docs|style|refactor|test|chore)\b', c["message"], re.IGNORECASE)
            ),
            "merge_commits": sum(1 for c in commits if c["message"].startswith('Merge')),
            "revert_commits": sum(1 for c in commits if 'revert' in c["message"].lower()),
            "wip_commits": sum(1 for c in commits if 'wip' in c["message"].lower() or 'work in progress' in c["message"].lower())
        }

        # Detect commit frequency issues
        dates = sorted(daily_counts.keys())
        if len(dates) > 1:
            date_objects = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
            span_days = (date_objects[-1] - date_objects[0]).days
            patterns["commits_per_day"] = round(len(commits) / max(span_days, 1), 2)

            # Find commit streaks and gaps
            gaps = []
            for i in range(1, len(date_objects)):
                gap = (date_objects[i] - date_objects[i-1]).days
                if gap > 7:
                    gaps.append({
                        "from": dates[i-1],
                        "to": dates[i],
                        "days": gap
                    })
            patterns["long_gaps"] = gaps[:5]

        # Author distribution analysis
        author_contributions = []
        for author, dates_list in author_commits.items():
            author_contributions.append({
                "author": author,
                "commits": len(dates_list),
                "first_commit": min(dates_list),
                "last_commit": max(dates_list),
                "active_days": len(set(dates_list))
            })

        author_contributions.sort(key=lambda x: x["commits"], reverse=True)

        # Bus factor calculation (how many authors contribute > 50% of commits)
        cumulative = 0
        bus_factor = 0
        for author in author_contributions:
            cumulative += author["commits"]
            bus_factor += 1
            if cumulative / len(commits) > 0.5:
                break

        patterns["author_distribution"] = author_contributions
        patterns["bus_factor"] = bus_factor
        patterns["dominant_author_ratio"] = round(
            author_contributions[0]["commits"] / len(commits), 2
        ) if author_contributions else 0

        # Quality indicators
        quality_issues = []
        if patterns["short_messages"] / max(patterns["total_commits"], 1) > 0.2:
            quality_issues.append("Many commits have very short messages")
        if patterns["wip_commits"] > 5:
            quality_issues.append("Multiple WIP commits detected - consider squashing")
        if patterns["revert_commits"] > 3:
            quality_issues.append("High number of revert commits indicates instability")
        if bus_factor == 1 and patterns["total_commits"] > 20:
            quality_issues.append("Single point of failure - only one major contributor")

        patterns["quality_issues"] = quality_issues
        patterns["quality_score"] = max(0, 100 - len(quality_issues) * 15)

        result = {
            "patterns": patterns,
            "period": since,
            "is_git_repo": True
        }

        _analysis_cache['commit_patterns'] = result
        return result
    except Exception as e:
        return {"error": str(e), "is_git_repo": True}


@tool
def get_code_ownership(directory: str, min_ownership_pct: float = 30.0) -> dict:
    """
    Analyzes code ownership across the repository to identify knowledge concentration

    Args:
        directory: Path to the git repository
        min_ownership_pct: Minimum percentage to consider an owner (default 30%)

    Returns:
        Dict with ownership map, orphan files, and knowledge distribution metrics
    """
    if not _is_git_repo(directory):
        return {"error": "Not a git repository", "is_git_repo": False}

    try:
        # Get all tracked files
        stdout, stderr, code = _run_git_command(directory, ['ls-files'])

        if code != 0:
            return {"error": stderr, "is_git_repo": True}

        files = [f for f in stdout.strip().split('\n') if f.endswith('.py')]

        file_ownership = []
        orphan_files = []
        author_domain = defaultdict(list)  # Files where author is primary owner

        for file_path in files[:100]:  # Limit for performance
            blame = get_file_blame(directory, file_path)

            if "error" in blame:
                continue

            ownership = blame.get("ownership", [])

            if not ownership:
                orphan_files.append(file_path)
                continue

            primary = ownership[0]
            file_ownership.append({
                "file": file_path,
                "primary_author": primary["author"],
                "ownership_pct": primary["percentage"],
                "lines": blame.get("total_lines", 0)
            })

            if primary["percentage"] >= min_ownership_pct:
                author_domain[primary["author"]].append(file_path)

        # Calculate knowledge distribution
        total_files = len(file_ownership)
        well_owned = len([f for f in file_ownership if f["ownership_pct"] >= min_ownership_pct])

        author_stats = []
        for author, files_owned in author_domain.items():
            author_stats.append({
                "author": author,
                "files_owned": len(files_owned),
                "ownership_pct": round(len(files_owned) / total_files * 100, 1) if total_files > 0 else 0,
                "files": files_owned[:10]  # Sample
            })

        author_stats.sort(key=lambda x: x["files_owned"], reverse=True)

        result = {
            "file_ownership": file_ownership[:50],  # Sample
            "author_domains": author_stats,
            "orphan_files": orphan_files[:20],
            "total_files_analyzed": total_files,
            "well_owned_files": well_owned,
            "ownership_coverage": round(well_owned / total_files * 100, 1) if total_files > 0 else 0,
            "knowledge_concentration": round(
                sum(a["ownership_pct"] ** 2 for a in author_stats) / 10000, 2
            ) if author_stats else 0,  # Herfindahl index
            "is_git_repo": True
        }

        _analysis_cache['code_ownership'] = result
        return result
    except Exception as e:
        return {"error": str(e), "is_git_repo": True}


@tool
def detect_refactoring_candidates(directory: str, since: str = "3 months ago") -> dict:
    """
    Uses git history to identify files that are refactoring candidates based on change patterns

    Args:
        directory: Path to the git repository
        since: Time period for analysis

    Returns:
        Dict with refactoring candidates, change patterns, and priority scores
    """
    if not _is_git_repo(directory):
        return {"error": "Not a git repository", "is_git_repo": False}

    try:
        # Get files with high bug-fix ratio
        cmd = ['log', f'--since={since}', '--pretty=format:%s', '--name-only']
        stdout, stderr, code = _run_git_command(directory, cmd)

        if code != 0:
            return {"error": stderr, "is_git_repo": True}

        file_bug_fixes = defaultdict(int)
        file_refactors = defaultdict(int)
        file_total_changes = defaultdict(int)

        current_message = ""
        current_files = set()

        for line in stdout.split('\n'):
            line = line.strip()
            if not line:
                # Process commit
                is_bug_fix = any(k in current_message.lower() for k in ['fix', 'bug', 'hotfix', 'patch'])
                is_refactor = any(k in current_message.lower() for k in ['refactor', 'cleanup', 'restructure'])

                for f in current_files:
                    file_total_changes[f] += 1
                    if is_bug_fix:
                        file_bug_fixes[f] += 1
                    if is_refactor:
                        file_refactors[f] += 1

                current_message = ""
                current_files = set()
            elif line.endswith('.py'):
                current_files.add(line)
            else:
                current_message = line

        candidates = []
        for file_path in file_total_changes:
            if not file_path.endswith('.py'):
                continue

            total = file_total_changes[file_path]
            bugs = file_bug_fixes[file_path]
            refactors = file_refactors[file_path]

            if total < 3:
                continue

            bug_ratio = bugs / total
            refactor_ratio = refactors / total

            # Priority score: high bug ratio + high total changes = needs refactoring
            priority_score = (bug_ratio * 50) + (min(total, 20) * 2) + (refactor_ratio * 10)

            candidates.append({
                "file": file_path,
                "total_changes": total,
                "bug_fixes": bugs,
                "refactors": refactors,
                "bug_ratio": round(bug_ratio, 2),
                "refactor_ratio": round(refactor_ratio, 2),
                "priority_score": round(priority_score, 1),
                "priority": (
                    "high" if priority_score > 40 else
                    "medium" if priority_score > 20 else "low"
                ),
                "indicators": [
                    "high_bug_rate" if bug_ratio > 0.3 else None,
                    "frequently_modified" if total > 10 else None,
                    "previous_refactors" if refactors > 2 else None
                ]
            })

        candidates.sort(key=lambda x: x['priority_score'], reverse=True)

        result = {
            "candidates": candidates[:20],
            "total_candidates": len(candidates),
            "high_priority": [c for c in candidates if c["priority"] == "high"],
            "period": since,
            "is_git_repo": True
        }

        _analysis_cache['refactoring_candidates'] = result
        return result
    except Exception as e:
        return {"error": str(e), "is_git_repo": True}