from pathlib import Path
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool,BaseTool
from subprocess import run

class match (BaseModel):
    file_path : Path = Field(description="The path to the file to search in.")
    line_number : int 
    content : str = Field(description="The content of the line to search for.")

class search_file_results (BaseModel):
    matches : list[match]

class read_file_result(BaseModel):
    file_path : Path = Field(description="The path to the file.")
    content : str = Field(description="The content of the file.")

@tool
def read_file(
    file_path : Path
    ) -> read_file_result:
    """reads file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
        
        return read_file_result(file_path=file_path, content=content)
    except FileNotFoundError:
        return "File not found."

@tool
def search_repository(
    keywords: list[str],
    repo_path: str,
) -> search_file_results:
    """
    Search repository using ripgrep and return matches.
    """

    matches: list[Match] = []

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

        for line in result.stdout.splitlines():

            try:
                file_path, line_number, line_content = (
                    line.split(":", maxsplit=2)
                )

                matches.append(
                    Match(
                        file_path=str(
                            Path(file_path).relative_to(
                                repo_path
                            )
                        ),
                        matched_keyword=keyword,
                        line_number=int(line_number),
                        line_content=line_content.strip(),
                    )
                )

            except ValueError:
                continue

    return search_file_results(
        matches=matches
    )