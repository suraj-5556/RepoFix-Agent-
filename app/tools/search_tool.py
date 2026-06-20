from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from subprocess import run

class Match(BaseModel):
    file_path : Path = Field(description="The path to the file to search in.")
    line_number : int 
    content : str = Field(description="The content of the line to search for.")
    matched_keyword : str = Field(description="The keyword that matched.")

class search_file_results(BaseModel):
    matches : list[Match]

class read_file_result(BaseModel):
    file_path : Path = Field(description="The path to the file.")
    content : str = Field(description="The content of the file.")

@tool
def read_file(
    file_path : Path,
    repo_path : Optional[str] = None
) -> read_file_result:
    """
    Reads a file from disk. If repo_path is provided, file_path will be resolved relative to repo_path.
    """
    try:
        resolved_path = Path(repo_path) / file_path if repo_path else file_path
        with open(resolved_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return read_file_result(file_path=resolved_path, content=content)
    except FileNotFoundError:
        return "File not found."

@tool
def search_repository(
    keywords: list[str],
    repo_path: str,
) -> search_file_results:
    """
    Search repository using ripgrep, git grep, or python fallback and return matches.
    """
    import os

    matches: list[Match] = []
    repo_path_obj = Path(repo_path)

    def make_relative(file_path_str: str) -> Path:
        p = Path(file_path_str)
        if not p.is_absolute():
            # If it's already a relative path, return it directly
            return p
        try:
            # Try to resolve to get correct casing of drive letter
            abs_file = p.resolve()
            abs_repo = repo_path_obj.resolve()
            return abs_file.relative_to(abs_repo)
        except Exception:
            # Fallback if relative_to fails (e.g. drive letter or casing difference)
            try:
                file_str = str(p.resolve()).replace("\\", "/").lower()
                repo_str = str(repo_path_obj.resolve()).replace("\\", "/").lower()
                if file_str.startswith(repo_str):
                    rel_str = str(p.resolve())[len(repo_str):].lstrip("\\/")
                    return Path(rel_str)
            except Exception:
                pass
            return p

    # 1. Try Ripgrep (rg)
    rg_success = False
    try:
        for keyword in keywords:
            result = run(
                [
                    "rg",
                    "--line-number",
                    "--no-heading",
                    "--ignore-case",
                    keyword,
                    repo_path,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode in (0, 1):
                rg_success = True
                for line in result.stdout.splitlines():
                    try:
                        file_path_str, line_number, line_content = line.split(":", maxsplit=2)
                        matches.append(
                            Match(
                                file_path=make_relative(file_path_str),
                                matched_keyword=keyword,
                                line_number=int(line_number),
                                content=line_content.strip(),
                            )
                        )
                    except ValueError:
                        continue
            else:
                break
    except FileNotFoundError:
        pass

    if rg_success:
        return search_file_results(matches=matches)

    # 2. Try Git Grep
    matches.clear()
    git_success = False
    try:
        for keyword in keywords:
            result = run(
                [
                    "git",
                    "grep",
                    "-I",
                    "--no-index",
                    "--line-number",
                    "--ignore-case",
                    keyword,
                    "--",
                    ".",
                ],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode in (0, 1):
                git_success = True
                for line in result.stdout.splitlines():
                    try:
                        file_path_str, line_number, line_content = line.split(":", maxsplit=2)
                        matches.append(
                            Match(
                                file_path=make_relative(file_path_str),
                                matched_keyword=keyword,
                                line_number=int(line_number),
                                content=line_content.strip(),
                            )
                        )
                    except ValueError:
                        continue
            else:
                break
    except FileNotFoundError:
        pass

    if git_success:
        return search_file_results(matches=matches)

    # 3. Python Fallback Walk
    matches.clear()
    skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env', 'build', 'dist', '.idea', '.vscode'}
    for root, dirs, files in os.walk(repo_path_obj):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in {
                '.pyc', '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz', 
                '.exe', '.dll', '.so', '.dylib', '.db', '.sqlite', '.sqlite3', '.bin', '.pkl'
            }:
                continue
            try:
                if file_path.stat().st_size > 5 * 1024 * 1024:
                    continue
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        for keyword in keywords:
                            if keyword.lower() in line.lower():
                                matches.append(
                                    Match(
                                        file_path=make_relative(str(file_path)),
                                        matched_keyword=keyword,
                                        line_number=line_num,
                                        content=line.strip(),
                                    )
                                )
            except Exception:
                continue

    return search_file_results(matches=matches)