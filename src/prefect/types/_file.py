"""
File upload types for Prefect flows.

This module provides types for handling file uploads in flow parameters,
making it easy to accept files through the UI without manual base64 handling.
"""

from __future__ import annotations

import base64
from typing import Any, Optional

import pydantic
from pydantic import Field, field_validator, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema as cs


class UploadedFile(pydantic.BaseModel):
    """
    A type for handling file uploads in Prefect flow parameters.

    When used as a flow parameter type, the UI will automatically render
    a file upload field. The uploaded file is transmitted as base64 and
    automatically decoded when the flow runs.

    Example:
        ```python
        from prefect import flow
        from prefect.types import UploadedFile

        @flow
        def process_document(document: UploadedFile) -> None:
            # Access file content as text
            content = document.read_text()
            print(f"Processing: {document.name}")
            print(f"Size: {document.size} bytes")
            print(f"Content: {content}")

        @flow
        def process_binary(image: UploadedFile) -> None:
            # Access file content as bytes
            data = image.read_bytes()
            print(f"Processing {len(data)} bytes from {image.name}")
        ```

    Attributes:
        content: The base64-encoded file content
        name: The filename (e.g., "document.txt")
        content_type: The MIME type (e.g., "text/plain", "image/png")
    """

    content: str = Field(
        ...,
        description="Base64-encoded file content",
        json_schema_extra={"format": "base64"},
    )
    name: Optional[str] = Field(None, description="Filename")
    content_type: Optional[str] = Field(None, description="MIME type")

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "description": "Upload a file",
            "format": "base64",
            "x-uploaded-file": True,  # Marker for schema post-processing
        }
    )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: cs.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """
        Customize the JSON schema to appear as a simple string with format: base64.

        This makes the UI render a file upload field instead of an object form.
        """
        # Get the default schema
        json_schema = handler(core_schema)

        # Replace the object schema with a simple string schema
        return {
            "type": "string",
            "format": "base64",
            "title": json_schema.get("title", "UploadedFile"),
            "description": json_schema.get("description", "Upload a file"),
        }

    @pydantic.model_validator(mode="before")
    @classmethod
    def validate_input(cls, data: any) -> dict:
        """
        Accept either a base64 string or a dict with content/name/content_type.

        This allows the UI to send just a base64 string for simple cases,
        or the full object structure when metadata is available.
        """
        if isinstance(data, str):
            # Simple case: just a base64 string
            return {"content": data}
        return data

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
        if not v:
            raise ValueError("File content cannot be empty")

        try:
            # Attempt to decode to verify it's valid base64
            base64.b64decode(v, validate=True)
            return v
        except Exception as e:
            raise ValueError(f"Invalid base64 encoding: {e}")

    def read_bytes(self) -> bytes:
        """
        Read the file content as bytes.

        Returns:
            The decoded file content as bytes

        Example:
            ```python
            @flow
            def process_file(file: UploadedFile):
                data = file.read_bytes()
                print(f"File size: {len(data)} bytes")
            ```
        """
        return base64.b64decode(self.content)

    def read_text(self, encoding: str = "utf-8") -> str:
        """
        Read the file content as text.

        Args:
            encoding: The character encoding to use (default: utf-8)

        Returns:
            The decoded file content as a string

        Raises:
            UnicodeDecodeError: If the file cannot be decoded with the specified encoding

        Example:
            ```python
            @flow
            def process_text_file(file: UploadedFile):
                text = file.read_text()
                print(f"Content: {text}")
            ```
        """
        return self.read_bytes().decode(encoding)

    @property
    def size(self) -> int:
        """
        Get the size of the file in bytes.

        Returns:
            The file size in bytes

        Example:
            ```python
            @flow
            def check_file_size(file: UploadedFile):
                if file.size > 1_000_000:
                    print(f"Large file: {file.size} bytes")
            ```
        """
        return len(self.read_bytes())

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        name: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> "UploadedFile":
        """
        Create an UploadedFile from raw bytes.

        Useful for testing or programmatically creating file uploads.

        Args:
            data: The file content as bytes
            name: Optional filename
            content_type: Optional MIME type

        Returns:
            An UploadedFile instance

        Example:
            ```python
            file = UploadedFile.from_bytes(
                b"Hello, World!",
                name="greeting.txt",
                content_type="text/plain"
            )
            ```
        """
        encoded = base64.b64encode(data).decode("utf-8")
        return cls(content=encoded, name=name, content_type=content_type)

    @classmethod
    def from_text(
        cls,
        text: str,
        name: Optional[str] = None,
        content_type: Optional[str] = "text/plain",
        encoding: str = "utf-8",
    ) -> "UploadedFile":
        """
        Create an UploadedFile from a text string.

        Useful for testing or programmatically creating text file uploads.

        Args:
            text: The text content
            name: Optional filename
            content_type: Optional MIME type (default: "text/plain")
            encoding: Character encoding (default: "utf-8")

        Returns:
            An UploadedFile instance

        Example:
            ```python
            file = UploadedFile.from_text(
                "Hello, World!",
                name="greeting.txt"
            )
            ```
        """
        return cls.from_bytes(
            text.encode(encoding), name=name, content_type=content_type
        )

    def __repr__(self) -> str:
        """String representation of the UploadedFile."""
        name_part = f" name={self.name!r}" if self.name else ""
        size_part = f" size={self.size}"
        type_part = f" type={self.content_type!r}" if self.content_type else ""
        return f"UploadedFile({name_part}{size_part}{type_part})"
