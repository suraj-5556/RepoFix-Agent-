from pydantic import BaseModel,Field
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from typing import List,Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage,HumanMessage,AIMessage

from app.tools.search_tool import read_file,search_repository

print("import done")

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
    # model="gemini-2.5-pro",
    model="gemini-2.5-flash",
    temperature=0.5,
)

agent = create_react_agent(
    model=llm,
    prompt = Path(r"app/prompts/planner.txt").read_text(encoding="utf-8"),
    tools=[read_file,search_repository],
    response_format=Plan
)
print("calling agent")
result = agent.invoke({
    "messages": [
        HumanMessage(content="testing")
    ]
})
print("Result:", result)
