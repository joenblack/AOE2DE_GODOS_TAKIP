import base64
import os

def get_image_base64(image_path: str) -> str:
    """Read an image file and encode it to base64 string for embedding."""
    if not os.path.exists(image_path):
        return None
    
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode("utf-8")
        
    ext = os.path.splitext(image_path)[1].lower().replace(".", "")
    if ext == "jpg": ext = "jpeg"
    
    return f"data:image/{ext};base64,{encoded}"
