#!/usr/bin/env python3
import cv2
import pytesseract
import re
import os
import sys

def blur_region(image, x, y, w, h, kernel_size, sigma):
    roi = image[y:y+h, x:x+w]
    blurred_roi = cv2.GaussianBlur(roi, (kernel_size, kernel_size), sigma)
    image[y:y+h, x:x+w] = blurred_roi

def auto_blur(image, kernel_size, sigma):
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    texts = data["text"]
    lefts = data["left"]
    tops = data["top"]
    widths = data["width"]
    heights = data["height"]
    print(f"Detected {len([t for t in texts if t.strip()])} non-empty text regions.")

    sensitive_labels = ["password", "api key", "secret", "token", "pwd", "pass", "credential", "key"]

    sensitive_patterns = [
        re.compile(r'[a-fA-F0-9]{32,}'),
        re.compile(r'[A-Za-z0-9-_]{20,}'),
        re.compile(r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+'),
        re.compile(r'[A-Za-z0-9+/]{20,}=*'),
    ]

    sensitive_boxes = []
    for i in range(len(texts)):
        text = texts[i].strip()
        if not text:
            continue
        lower_text = text.lower()
        if any(label in lower_text for label in sensitive_labels):
            print(f"Found potential sensitive label in text: '{texts[i]}'")
            sensitive_boxes.append((lefts[i], tops[i], widths[i], heights[i]))
            for j in range(i + 1, len(texts)):
                if abs(tops[j] - tops[i]) < 10 and texts[j].strip():
                    print(f"Blurring subsequent text as sensitive value: '{texts[j]}'")
                    sensitive_boxes.append((lefts[j], tops[j], widths[j], heights[j]))
                    break
        elif any(pattern.search(text) for pattern in sensitive_patterns):
            print(f"Found potential standalone secret: '{text}'")
            sensitive_boxes.append((lefts[i], tops[i], widths[i], heights[i]))

    print(f"Number of sensitive boxes detected: {len(sensitive_boxes)}")
    for box in sensitive_boxes:
        x, y, w, h = box
        blur_region(image, x, y, w, h, kernel_size, sigma)
    return image

def manual_blur_by_keywords(image, kernel_size, sigma, keywords):
    # Convert keywords list to lower-case and trim whitespace.
    keywords = [kw.strip().lower() for kw in keywords if kw.strip()]
    if not keywords:
        return image

    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    texts = data["text"]
    lefts = data["left"]
    tops = data["top"]
    widths = data["width"]
    heights = data["height"]

    for keyword in keywords:
        count = 0
        for i, text in enumerate(texts):
            if keyword in text.lower():
                blur_region(image, lefts[i], tops[i], widths[i], heights[i], kernel_size, sigma)
                count += 1
        print(f"Blurred {count} regions containing '{keyword}'.")
    return image

def main():
    if len(sys.argv) < 3:
        print("Usage: {} <input_image> <output_image> [kernel_size] [sigma] [keywords]".format(sys.argv[0]))
        sys.exit(1)

    image_path = sys.argv[1]
    output_path = sys.argv[2]
    try:
        kernel_size = int(sys.argv[3]) if len(sys.argv) > 3 else 99
    except:
        kernel_size = 99
    try:
        sigma = float(sys.argv[4]) if len(sys.argv) > 4 else 30
    except:
        sigma = 30

    # Ensure kernel_size is odd.
    if kernel_size % 2 == 0:
        kernel_size += 1

    # Optional keywords parameter as a comma-separated string.
    keywords = []
    if len(sys.argv) > 5:
        keywords_str = sys.argv[5]
        if keywords_str.strip():
            keywords = keywords_str.split(',')

    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not read the image file '{image_path}'")
        sys.exit(1)
    print("Image loaded successfully.")

    # Apply automatic blurring.
    auto_blur(image, kernel_size, sigma)

    # Apply manual blurring based on provided keywords.
    if keywords:
        manual_blur_by_keywords(image, kernel_size, sigma, keywords)
    else:
        print("No manual keywords provided; skipping manual blur.")

    cv2.imwrite(output_path, image)
    print(f"Processed image saved as '{output_path}'.")

if __name__ == "__main__":
    main()

