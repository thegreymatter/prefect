"""
Utilities for handling base64-encoded file uploads in Prefect flow run inputs.

This module provides field types and validators for working with files that are
uploaded through the UI and transmitted as base64-encoded strings.

Example:
    ```python
    from prefect import flow
    from prefect.input import RunInput
    from prefect.input.base64_file import Base64File

    class DocumentInput(RunInput):
        document: Base64File

    @flow
    async def process_document():
        async for input_data in DocumentInput.receive():
            # Access the decoded file bytes
            file_bytes = input_data.document.get_bytes()

            # Access file metadata
            print(f"Processing file: {input_data.document.filename}")
            print(f"File size: {len(file_bytes)} bytes")

            # Process the file...
            input_data.respond(DocumentInput(document=input_data.document))
    ```
"""

import base64
from typing import Any, Optional

from pydantic import BaseModel, field_validator


class Base64File(BaseModel):
    """
    A Pydantic model for handling base64-encoded file uploads.

    This model automatically decodes base64 strings into bytes and provides
    convenient access to file content and metadata.

    Attributes:
        content: The base64-encoded file content
        filename: Optional filename
        content_type: Optional MIME type
    """

    content: str
    filename: Optional[str] = None
    content_type: Optional[str] = None

    @field_validator("content")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        """
        Validate that the content is valid base64.

        Args:
            v: The base64 string to validate

        Returns:
            The validated base64 string

        Raises:
            ValueError: If the string is not valid base64
        """
        try:
            # Attempt to decode to verify it's valid base64
            base64.b64decode(v, validate=True)
            return v
        except Exception as e:
            raise ValueError(f"Invalid base64 encoding: {e}")

    def get_bytes(self) -> bytes:
        """
        Get the decoded file content as bytes.

        Returns:
            The decoded file content
        """
        return base64.b64decode(self.content)

    def get_size(self) -> int:
        """
        Get the size of the decoded file in bytes.

        Returns:
            Size in bytes
        """
        return len(self.get_bytes())

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> "Base64File":
        """
        Create a Base64File from raw bytes.

        Args:
            data: The file content as bytes
            filename: Optional filename
            content_type: Optional MIME type

        Returns:
            A Base64File instance
        """
        encoded = base64.b64encode(data).decode("utf-8")
        return cls(content=encoded, filename=filename, content_type=content_type)

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """
        Override model_dump to ensure we only serialize the base64 string.

        This is important for sending files back through the API.
        """
        result = super().model_dump(**kwargs)
        # Ensure content is a string, not bytes
        if "content" in result and isinstance(result["content"], bytes):
            result["content"] = base64.b64encode(result["content"]).decode("utf-8")
        return result


def validate_base64_string(v: Any) -> str:
    """
    A standalone validator function for base64 strings.

    This can be used as a Pydantic field validator for simple string fields
    that should contain base64-encoded data.

    Args:
        v: The value to validate

    Returns:
        The validated base64 string

    Raises:
        ValueError: If the value is not a valid base64 string

    Example:
        ```python
        from pydantic import BaseModel, field_validator
        from prefect.input.base64_file import validate_base64_string

        class MyInput(RunInput):
            file_data: str

            @field_validator('file_data')
            @classmethod
            def check_base64(cls, v):
                return validate_base64_string(v)
        ```
    """
    if not isinstance(v, str):
        raise ValueError("Value must be a string")

    try:
        base64.b64decode(v, validate=True)
        return v
    except Exception as e:
        raise ValueError(f"Invalid base64 encoding: {e}")


def decode_base64(encoded: str) -> bytes:
    """
    Decode a base64 string to bytes.

    Args:
        encoded: The base64-encoded string

    Returns:
        The decoded bytes

    Raises:
        ValueError: If the string is not valid base64
    """
    try:
        return base64.b64decode(encoded, validate=True)
    except Exception as e:
        raise ValueError(f"Failed to decode base64: {e}")


def encode_base64(data: bytes) -> str:
    """
    Encode bytes to a base64 string.

    Args:
        data: The bytes to encode

    Returns:
        The base64-encoded string
    """
    return base64.b64encode(data).decode("utf-8")
