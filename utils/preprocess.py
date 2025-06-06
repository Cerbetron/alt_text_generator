import cv2
import numpy as np
from PIL import Image
import io

def preprocess_image(image: Image.Image, debug=False):
    """
    Light preprocessing to classify possible issues but does not skip any image.
    Returns:
        - cleaned_image: minimally cleaned image (PIL)
        - is_logo: whether it's likely a company logo
        - was_flagged: whether the image had artifact indicators
        - reason: reason why it was flagged (empty if not flagged)
    """
    img = np.array(image)
    if len(img.shape) == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    elif len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    h, w = img.shape[:2]
    reason = ""

    # Artifact check: uniform image
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    std_dev = np.std(gray)
    if debug: print(f"[StdDev] {std_dev:.2f}")
    if std_dev < 3:
        reason = "Low visual variance (uniform background)"

    # Small or oddly shaped images
    if h < 30 or w < 30 or h/w > 10 or w/h > 10:
        reason = "Image dimensions too small or unbalanced"

    # Solid white or black
    mean_gray = np.mean(gray)
    if mean_gray > 245:
        reason = "Image is mostly white"
    elif mean_gray < 5:
        reason = "Image is mostly black"

    # Logo detection
    is_logo = False
    if w < 400 and h < 200:
        top_region = gray[:int(0.3 * h), :]
        if np.mean(top_region) > 180:
            is_logo = True

    final_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    was_flagged = reason != ""
    return final_img, is_logo, was_flagged, reason