from pydantic import BaseModel, Field, ConfigDict



class SuccessResponse(BaseModel):
    """Schema for success response"""
    message: str = Field(
        description="Success message"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully"
            }
        }
    )


class ErrorResponse(BaseModel):
    """Schema for error response"""
    detail: str = Field(
        description="Details of the error"
    )
    status_code: int = Field(
        description="HTTP status code"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Resource not found",
                "status_code": 404
            }
        }
    )
