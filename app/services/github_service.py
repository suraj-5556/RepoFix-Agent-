import requests
from typing import Dict

def get_github_issue(repo_url: str, issue_number: int) -> dict:
    """
    Queries the public GitHub API to fetch issue details.
    Does not require authentication.
    """
    # Clean up the URL
    clean_url = repo_url.strip().rstrip("/")
    if clean_url.endswith(".git"):
        clean_url = clean_url[:-4]
        
    parts = clean_url.split("/")
    if len(parts) < 2 or "github.com" not in clean_url:
        raise ValueError("Invalid GitHub repository URL. Must be like https://github.com/owner/repo")
        
    owner = parts[-2]
    repo = parts[-1]
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    
    # Perform public API request
    response = requests.get(api_url)
    
    if response.status_code == 404:
        raise FileNotFoundError(f"Issue #{issue_number} was not found in repository {owner}/{repo}.")
    elif response.status_code != 200:
        raise Exception(f"Failed to fetch issue from GitHub (HTTP {response.status_code}): {response.text}")
        
    data = response.json()
    
    # Return structured issue metadata
    return {
        "title": data.get("title", ""),
        "body": data.get("body", "") or "No description provided.",
        "state": data.get("state", "unknown"),
        "html_url": data.get("html_url", ""),
        "user": data.get("user", {}).get("login", "unknown")
    }
