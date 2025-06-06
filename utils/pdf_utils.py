import fitz  # PyMuPDF
from PIL import Image
import io
from collections import defaultdict

def extract_images_from_pdf(uploaded_file):
    """
    Extract images from each page of the uploaded PDF.

    Args:
        uploaded_file: Streamlit file-like PDF input

    Returns:
        A dictionary mapping page number to list of PIL images
        e.g., {1: [PIL.Image, PIL.Image], 2: [PIL.Image], ...}
    """
    pdf_bytes = uploaded_file.read()
    try:
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        print("Failed to open PDF:", e)
        return {}

    images_by_page = defaultdict(list)

    for page_index in range(len(pdf_doc)):
        page = pdf_doc[page_index]
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = pdf_doc.extract_image(xref)
                img_bytes = base_image["image"]
                image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                images_by_page[page_index + 1].append(image)
            except Exception as e:
                print(f"❌ Error on page {page_index + 1}, image {img_index}: {e}")
                continue

    pdf_doc.close()
    return dict(images_by_page)
