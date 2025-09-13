from pydantic import BaseModel, RootModel
from typing import List, Union
from enum import Enum

class Metadata(BaseModel): # JSON output format which we would like to get from LLM
    Summary: List[str]
    Title: str
    Author: List[str]
    DateCreated: str
    LastModifiedDate: str
    Publisher: str
    Language: str
    PageCount: Union[int, str]  # Can be "Not Available"
    SentimentTone: str
class ChangeFormat(BaseModel):
    Page: str
    Changes: str

class SummaryResponse(RootModel[list[ChangeFormat]]):
    pass
# we use Enum class for data validation -> we define a variable and its value
# Enum is enumerated class. PromptType is of Enum class. We validate strings.
# ❌ Hard to discover what prompts exist
# Developer has to guess or look at the registry manually
# Enum class allows IDE to help (suggesting the correct value)
class PromptType(str, Enum): 
    DOCUMENT_ANALYSIS = "document_analysis"
    DOCUMENT_COMPARISON = "document_comparison"
    CONTEXTUALIZE_QUESTION = "contextualize_question"
    CONTEXT_QA = "context_qa"
    # use case: PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION.value]
    # ✅ Using Enum - type-safe and discoverable
    # class DocumentComparatorLLM:
    #     def __init__(self):
    #         # IDE autocomplete + compile-time error checking
    #         self.prompt = PROMPT_REGISTRY[PromptType.DOCUMENT_COMPARISON.value]