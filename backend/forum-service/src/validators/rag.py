from pydantic import BaseModel, Field
from typing import List



class SourceRef(BaseModel):
    id: str = Field(..., description="Unique identifier of the source")
    title: str = Field(..., description="Title of the source")

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="The question to ask the RAG system")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top relevant sources to return (1-20)")

class AskResponse(BaseModel):
    answer: str = Field(..., min_length=1, description="Generated answer to the question")
    sources: List[SourceRef] = Field(default_factory=list, description="List of sources used to generate the answer")