from pydantic import BaseModel,Field
from pathlib import Path
from langchain_core.prompt import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from typing import List,Literal
from langchain_google_genai import ChatGoogleGenerativeAI

class file_change(BaseModel):
    file_path : Path = Field(description="The path to the file to modify.")
    model : Literal["Modify","New","Delete"] = Field(description="The type of change to make.")
    description : str = Field(description="Description of changes")    

class Plan(BaseModel):
    overview : str = Field(description="An overview of plan")
    changes : List[file_change] = Field(description="List of changes to be made")
    tests : str = Field(description="Tests need to perform to verify the fix")

    
