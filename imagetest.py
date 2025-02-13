import base64
import os

def encode_image(image_path):
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return ""
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"

# Test one image
print(encode_image("/home/Mainhub/emojis/good.png"))
