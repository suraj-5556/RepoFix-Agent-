from pydantic import BaseModel, Field
from pathlib import Path
from typing import List, Literal, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.tools.search_tool import read_file, search_repository, read_file_result, search_file_results

class file_change(BaseModel):
    file_path : Path = Field(description="The path to the file to modify.")
    model : Literal["Modify","New","Delete"] = Field(description="The type of change to make.")
    description : str = Field(description="Description of changes")    

class Plan(BaseModel):
    overview : str = Field(description="An overview of plan")
    changes : List[file_change] = Field(description="List of changes to be made")
    tests : str = Field(description="Tests need to perform to verify the fix")
    task : list[str] = Field(description="List of tasks to be performed")


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.5,
)

# Keep global agent definition for backward compatibility
agent = create_react_agent(
    model=llm,
    prompt = Path(r"app/prompts/planner.txt").read_text(encoding="utf-8"),
    tools=[read_file, search_repository],
    response_format=Plan
)

def execute_planner(repo_path: str, issue_description: str) -> Plan:
    """
    Executes the planner agent on a specific repository path with a given issue description.
    """
    # 1. Bind tools to the specific repo_path to prevent the model from failing to pass it
    @tool
    def read_file_bound(file_path: Path) -> read_file_result:
        """Reads a file from the repository."""
        return read_file.func(file_path=file_path, repo_path=repo_path)

    @tool
    def search_repository_bound(keywords: list[str]) -> search_file_results:
        """Searches the repository for the given keywords using ripgrep."""
        return search_repository.func(keywords=keywords, repo_path=repo_path)

    # 2. Create the react agent dynamically with bound tools
    system_prompt = Path(r"app/prompts/planner.txt").read_text(encoding="utf-8")
    system_prompt += f"\n\nNote: You are currently planning for the repository located at: {repo_path}."

    repo_agent = create_react_agent(
        model=llm,
        prompt=system_prompt,
        tools=[read_file_bound, search_repository_bound],
        response_format=Plan
    )
    
    # 3. Invoke the agent
    content = f"Please analyze the following issue and design a plan.\nRepository Path: {repo_path}\nIssue Description: {issue_description}"
    
    result = repo_agent.invoke({
        "messages": [
            HumanMessage(content=content)
        ]
    })
    
    # 4. Extract structured response
    if "structured_response" in result:
        return result["structured_response"]
    
    raise ValueError(f"Agent did not return a structured plan. Full result: {result}")

if __name__ == "__main__":
    print("calling agent in test mode...")
    # Local test
    test_result = execute_planner(
        repo_path="c:/Users/khetr/OneDrive/Desktop/RepoFix-Agent-",
        issue_description="Add a test description to check if planning works."
    )
    print("Result:", test_result)
