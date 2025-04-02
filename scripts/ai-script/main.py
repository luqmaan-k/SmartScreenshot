#!/usr/bin/env python3
import cv2
import pytesseract
import re
import os
import sys
from transformers import pipeline

def expand_box(x, y, w, h, expand=10, img_width=None, img_height=None):
    new_x = max(0, x - expand)
    new_y = max(0, y - expand)
    new_w = w + 2 * expand
    new_h = h + 2 * expand
    if img_width and new_x + new_w > img_width:
        new_w = img_width - new_x
    if img_height and new_y + new_h > img_height:
        new_h = img_height - new_y
    return new_x, new_y, new_w, new_h

def blur_region(img, x, y, w, h, kernel_size, sigma, expand=15):
    """Blurs a region with Gaussian blur."""
    img_h, img_w = img.shape[:2]
    x, y, w, h = expand_box(x, y, w, h, expand, img_w, img_h)
    roi = img[y:y+h, x:x+w]
    k = max(15, (min(w, h) // 2) | 1)  # Ensure kernel size is odd
    blurred_roi = cv2.GaussianBlur(roi, (kernel_size, kernel_size), sigma)
    img[y:y+h, x:x+w] = blurred_roi

def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <input_image> <output_image> <sensitive_labels_comma_separated> [kernel_size] [sigma]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_path = sys.argv[2]
    sensitive_labels = sys.argv[3].split(",")
    kernel_size = int(sys.argv[4]) if len(sys.argv) > 4 else 99
    sigma = float(sys.argv[5]) if len(sys.argv) > 5 else 30
    
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not read the image file '{image_path}'")
        sys.exit(1)
    
    print("Image loaded successfully.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    data = pytesseract.image_to_data(gray, config='--oem 3 --psm 6', output_type=pytesseract.Output.DICT)
    texts, lefts, tops, widths, heights = data["text"], data["left"], data["top"], data["width"], data["height"]
    
    print(f"Detected {len([t for t in texts if t.strip()])} non-empty text regions.")
    secret_patterns = [
        re.compile(r'[A-Za-z0-9_\-]{20,}'),
        re.compile(r'AKIA[0-9A-Z]{16}'),
        re.compile(r'ghp_[A-Za-z0-9]{36}'),
        re.compile(r'AIza[0-9A-Za-z-_]{35}'),
        re.compile(r'eyJ[a-zA-Z0-9]{30,}')
    ]
    
    sensitive_boxes = []
    for i, text in enumerate(texts):
        text = text.strip().lower()
        if not text:
            continue
        
        if any(label.lower() in text for label in sensitive_labels):
            print(f"Found potential sensitive label: '{texts[i]}'")
            sensitive_boxes.append((lefts[i], tops[i], widths[i], heights[i]))
            
            for j in range(i + 1, len(texts)):
                if abs(tops[j] - tops[i]) < 15 and texts[j].strip():
                    print(f"Blurring subsequent text as sensitive value: '{texts[j]}'")
                    sensitive_boxes.append((lefts[j], tops[j], widths[j], heights[j]))
                    break
        elif any(pattern.match(text) for pattern in secret_patterns):
            print(f"Found potential secret: '{texts[i]}'")
            sensitive_boxes.append((lefts[i], tops[i], widths[i], heights[i]))
    
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    for i, text in enumerate(texts):
        text = text.strip()
        if not text or any((lefts[i], tops[i], widths[i], heights[i]) == box for box in sensitive_boxes):
            continue
        result = classifier(text, candidate_labels=["password", "normal text"])
        score = result["scores"][0] if result["labels"][0] == "password" else 1 - result["scores"][0]
        if result["labels"][0] == "password" and score > 0.7:
            print(f"Classified '{text}' as sensitive with score {score:.3f}")
            sensitive_boxes.append((lefts[i], tops[i], widths[i], heights[i]))
    
    print(f"Number of sensitive regions detected: {len(sensitive_boxes)}")
    
    for box in sensitive_boxes:
        blur_region(image, *box, kernel_size, sigma)
    
    cv2.imwrite(output_path, image)
    print(f"Processed image saved as '{output_path}'.")
    
if __name__ == "__main__":
    main()

