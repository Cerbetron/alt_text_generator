import base64
from io import BytesIO
from PIL import Image
import os

def image_to_base64(image: Image.Image) -> str:
    """Convert a PIL Image to base64 string."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def safe_filename(name: str) -> str:
    """Sanitize filename for filesystem compatibility."""
    return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_')).rstrip()

def ensure_dir_exists(path: str):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def label_output(page: int, index: int, text: str) -> str:
    """
    Format output string for each image.
    Returns:
        'Page 1 - Image 2: description...'
    """
    return f"Page {page} - Image {index}: {clean_text(text)}"

def clean_text(text: str) -> str:
    """
    Normalize LLM output (strip trailing spaces, remove unwanted quotes).
    """
    return text.replace("\n", " ").replace('"', '').replace("'", '').strip()
