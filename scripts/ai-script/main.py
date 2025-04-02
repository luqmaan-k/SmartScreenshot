import cv2
import pytesseract
import re
import argparse
import os
from PIL import Image
from transformers import pipeline

parser = argparse.ArgumentParser(description="Blur sensitive text in an image.")
parser.add_argument("image_path", type=str, help="Path to the input image.")
parser.add_argument("--kernel", type=int, default=15, help="Kernel size for Gaussian blur (must be odd).")
parser.add_argument("--sigma", type=int, default=30, help="Sigma value for Gaussian blur.")
parser.add_argument("--expand", type=int, default=10, help="Expansion pixels for bounding box.")
args = parser.parse_args()

image = cv2.imread(args.image_path)
if image is None:
    print(f"Error: Could not read the image file '{args.image_path}'")
    exit(1)
print(f"Image '{args.image_path}' loaded successfully.")

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

config = r'--oem 3 --psm 6'  
data = pytesseract.image_to_data(gray, config=config, output_type=pytesseract.Output.DICT)
texts = data["text"]
lefts, tops, widths, heights = data["left"], data["top"], data["width"], data["height"]

print(f"Detected {len([t for t in texts if t.strip()])} non-empty text regions.")

sensitive_labels = ["password", "api key", "secret", "token", "pwd", "pass", "authorization", "bearer"]
secret_patterns = [
    re.compile(r'[A-Za-z0-9_\-]{20,}'),      
    re.compile(r'AKIA[0-9A-Z]{16}'),        
    re.compile(r'ghp_[A-Za-z0-9]{36}'),     
    re.compile(r'AIza[0-9A-Za-z-_]{35}'),   
    re.compile(r'eyJ[a-zA-Z0-9]{30,}'),     
]

sensitive_boxes = []
for i, text in enumerate(texts):
    text = text.lower().strip()
    if not text:
        continue

    if any(label in text for label in sensitive_labels):
        print(f"Found sensitive label: '{texts[i]}'")
        sensitive_boxes.append((lefts[i], tops[i], widths[i], heights[i]))

        for j in range(i + 1, len(texts)):
            if abs(tops[j] - tops[i]) < 15 and texts[j].strip():
                print(f"Blurring sensitive value: '{texts[j]}'")
                sensitive_boxes.append((lefts[j], tops[j], widths[j], heights[j]))
                break

    elif any(pattern.match(text) for pattern in secret_patterns):
        print(f"Found potential secret: '{texts[i]}'")
        sensitive_boxes.append((lefts[i], tops[i], widths[i], heights[i]))

def expand_box(x, y, w, h, expand, img_width, img_height):
    new_x, new_y = max(0, x - expand), max(0, y - expand)
    new_w, new_h = min(img_width - new_x, w + 2 * expand), min(img_height - new_y, h + 2 * expand)
    return new_x, new_y, new_w, new_h

for (x, y, w, h) in sensitive_boxes:
    x, y, w, h = expand_box(x, y, w, h, args.expand, image.shape[1], image.shape[0])
    roi = image[y:y+h, x:x+w]
    k = max(3, args.kernel | 1) 
    blurred_roi = cv2.GaussianBlur(roi, (k, k), args.sigma)
    image[y:y+h, x:x+w] = blurred_roi

output_path = os.path.basename(args.image_path)
print(output_path)
cv2.imwrite(output_path, image)
os.replace(output_path, args.image_path)
print(f"Image saved and replaced as '{args.image_path}'.")
