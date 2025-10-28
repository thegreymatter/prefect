"""
Example flow demonstrating file upload functionality with base64 encoding.

This example shows how to create a flow that accepts file uploads through the UI,
processes them, and returns results.
"""

from prefect import flow
from prefect.input import Base64File, RunInput


class FileUploadInput(RunInput):
    """Input model for accepting file uploads."""

    document: Base64File
    description: str = "Upload a file for processing"


@flow
def process_uploaded_file():
    """
    A flow that accepts file uploads and processes them.

    To test this flow:
    1. Run this flow from the UI
    2. In the flow run form, upload a file using the file input field
    3. The flow will receive the file as a base64-encoded string
    4. The file will be decoded and processed
    """
    print("Waiting for file upload...")

    # Receive the file upload from the UI
    for input_data in FileUploadInput.receive():
        # Access the decoded file bytes
        file_bytes = input_data.document.get_bytes()

        print(f"Received file: {input_data.document.filename}")
        print(f"Content type: {input_data.document.content_type}")
        print(f"File size: {input_data.document.get_size()} bytes")
        print(f"First 100 bytes: {file_bytes[:100]}")

        # Process the file (example: count lines if it's a text file)
        try:
            content = file_bytes.decode("utf-8")
            line_count = len(content.splitlines())
            print(f"Text file detected with {line_count} lines")
        except UnicodeDecodeError:
            print("Binary file detected (not text)")

        # You can respond back with the same or different data
        print("File processed successfully!")
        break


@flow
def upload_file_with_schema():
    """
    A flow that uses parameter schema to define file upload fields.

    This demonstrates how to use the file upload in flow parameters.
    """
    # This will be automatically rendered as a file upload in the UI
    # when the parameter schema includes format: "base64"
    pass


if __name__ == "__main__":
    # Run the flow
    process_uploaded_file()
