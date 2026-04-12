from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ErrorCode(str, Enum):
    AMBIGUOUS_QUERY        = "AMBIGUOUS_QUERY"
    METRIC_NOT_FOUND       = "METRIC_NOT_FOUND"
    SQL_GENERATION_FAILED  = "SQL_GENERATION_FAILED"
    NO_DATA_FOUND          = "NO_DATA_FOUND"
    LLM_UNAVAILABLE        = "LLM_UNAVAILABLE"
    INTERNAL_ERROR         = "INTERNAL_ERROR"


class ErrorResponse(BaseModel):
    error_code:  ErrorCode
    message:     str
    recoverable: bool
    request_id:  str
    suggestion:  Optional[str] = None
