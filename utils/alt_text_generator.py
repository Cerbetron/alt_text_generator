import requests
import base64
from io import BytesIO
from PIL import Image

def encode_image_to_base64(image: Image.Image) -> str:
    """Converts PIL image to base64 string."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def build_openai_payload(b64_image: str, prompt: str):
    return {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
                ]
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }

def build_groq_payload(b64_image: str, prompt: str):
    return {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
                ]
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }

def generate_alt_text(
    image: Image.Image,
    model: str,
    openai_key: str,
    groq_key: str,
    is_logo: bool = False,
    alt_line_count: int = 2,
    language: str = "English"
) -> str:
    """
    Generate alt-text using the selected vision model.

    Args:
        image: PIL Image (already preprocessed)
        model: 'OpenAI' or 'Groq'
        openai_key: OpenAI API key
        groq_key: Groq API key
        is_logo: Whether the image is a company logo
        alt_line_count: Max number of lines for alt-text
        language: Desired language for the alt-text

    Returns:
        Alt-text string
    """
    if is_logo:
        return "Company logo."

    prompt = (
        f"Generate a brief alt-text in {language} for this image within "
        f"{alt_line_count} line(s), suitable for screen readers."
    )
    b64_image = encode_image_to_base64(image)

    try:
        if model == "OpenAI":
            if not openai_key:
                return "[OpenAI API key missing]"
            headers = {"Authorization": f"Bearer {openai_key}"}
            json_data = build_openai_payload(b64_image, prompt)
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=json_data,
                timeout=15
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()

        elif model == "Groq":
            if not groq_key:
                return "[Groq API key missing]"
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            }
            json_data = build_groq_payload(b64_image, prompt)
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=json_data,
                timeout=15
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()

        else:
            return "[Unsupported model selected]"

    except requests.exceptions.Timeout:
        return "[Alt-text generation failed: request timed out]"
    except requests.exceptions.HTTPError as http_err:
        return f"[Alt-text generation failed: {http_err.response.status_code} HTTP error]"
    except requests.exceptions.RequestException:
        return "[Alt-text generation failed due to API error]"
    except Exception:
        return "[Alt-text generation failed unexpectedly]"
