import subprocess
import time
from pathlib import Path

def clone_repository(repo_url: str) -> str:
    """
    Clones a git repository to a unique directory under `cloned_repos/` in the workspace.
    Returns the absolute path to the cloned repository.
    """
    # Resolve workspace root dynamically relative to this file
    workspace_root = Path(__file__).resolve().parent.parent.parent
    cloned_repos_dir = workspace_root / "cloned_repos"
    cloned_repos_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract repo name from URL
    # e.g., https://github.com/owner/repo-name.git -> repo-name
    repo_name = repo_url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
        
    if not repo_name:
        repo_name = "cloned_repo"
        
    timestamp = int(time.time())
    dest_path = cloned_repos_dir / f"{repo_name}_{timestamp}"
    
    # Run git clone
    result = subprocess.run(
        ["git", "clone", repo_url, str(dest_path)],
        capture_output=True,
        text=True,
        check=False
    )
    
    if result.returncode != 0:
        raise Exception(f"Git clone failed: {result.stderr.strip() or 'Unknown error'}")
        
    return str(dest_path.resolve())
