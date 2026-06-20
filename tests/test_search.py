from pathlib import Path
from unittest.mock import patch
from app.tools.search_tool import search_repository

def test_search_repository():
    # Search for something known in our workspace
    workspace_root = str(Path(__file__).resolve().parent.parent)
    result = search_repository.func(keywords=["execute_planner"], repo_path=workspace_root)
    
    assert len(result.matches) > 0
    # Make sure we found matches in main.py or planner_agent.py
    files_with_matches = [str(m.file_path).replace("\\", "/") for m in result.matches]
    assert any("app/main.py" in f or "planner_agent.py" in f for f in files_with_matches)
    
    # Check that matches have line numbers and content
    for match in result.matches:
        assert match.line_number > 0
        assert "execute_planner" in match.content.lower()

def test_search_repository_fallback():
    workspace_root = str(Path(__file__).resolve().parent.parent)
    
    # Mock subprocess.run to raise FileNotFoundError (simulating neither rg nor git grep is available)
    with patch("app.tools.search_tool.run", side_effect=FileNotFoundError("Mocked command not found")):
        result = search_repository.func(keywords=["execute_planner"], repo_path=workspace_root)
        
        assert len(result.matches) > 0
        files_with_matches = [str(m.file_path).replace("\\", "/") for m in result.matches]
        assert any("app/main.py" in f or "planner_agent.py" in f for f in files_with_matches)
        
        for match in result.matches:
            assert match.line_number > 0
            assert "execute_planner" in match.content.lower()
