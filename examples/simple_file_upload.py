"""
Simple example using UploadedFile for file uploads.

This example shows how easy it is to accept file uploads in your flows
using the UploadedFile type - no manual base64 handling required!
"""

from prefect import flow
from prefect.types import UploadedFile


@flow(log_prints=True)
def hello(name: UploadedFile) -> None:
    """
    A simple 'hello world' flow that reads a name from an uploaded file.

    To run this flow:
    1. Deploy this flow or run it through the UI
    2. When prompted, upload a text file containing a name
    3. The flow will read the file and greet the person!

    Example file content:
        Marvin
    """
    # Read the file content as text
    content = name.read_text().strip()

    # Print the greeting
    print(f"Hello, {content}!")

    # You can also access metadata
    if name.name:
        print(f"File name: {name.name}")
    print(f"File size: {name.size} bytes")


@flow(log_prints=True)
def process_document(document: UploadedFile) -> dict:
    """
    Process an uploaded document and return statistics.

    Args:
        document: Any text file to analyze

    Returns:
        A dictionary with document statistics
    """
    # Read the content
    content = document.read_text()

    # Calculate statistics
    stats = {
        "filename": document.name or "unknown",
        "size_bytes": document.size,
        "num_lines": len(content.splitlines()),
        "num_words": len(content.split()),
        "num_chars": len(content),
    }

    print(f"Document Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    return stats


@flow(log_prints=True)
def analyze_image(image: UploadedFile) -> None:
    """
    Analyze an uploaded image file.

    Args:
        image: An image file (PNG, JPG, etc.)
    """
    # Get the raw bytes
    data = image.read_bytes()

    print(f"Received image: {image.name}")
    print(f"Content type: {image.content_type}")
    print(f"Size: {image.size} bytes")
    print(f"First 20 bytes: {data[:20].hex()}")

    # You could use PIL/Pillow here to actually process the image
    # from PIL import Image
    # import io
    # img = Image.open(io.BytesIO(data))
    # print(f"Image dimensions: {img.size}")


@flow(log_prints=True)
def process_multiple_files(
    config: UploadedFile,
    data: UploadedFile,
    readme: str = "No readme provided",
) -> None:
    """
    Example flow that accepts multiple file uploads and other parameters.

    Args:
        config: A configuration file (JSON, YAML, etc.)
        data: A data file to process
        readme: Optional readme text
    """
    print(f"Config file: {config.name} ({config.size} bytes)")
    print(f"Data file: {data.name} ({data.size} bytes)")
    print(f"Readme: {readme}")

    # Process the files
    config_content = config.read_text()
    data_content = data.read_bytes()

    print(f"Config preview: {config_content[:100]}...")
    print(f"Data size: {len(data_content)} bytes")


if __name__ == "__main__":
    # For local testing, create a sample file
    sample_file = UploadedFile.from_text(
        "Marvin",
        name="sample.txt",
        content_type="text/plain"
    )

    hello(name=sample_file)
