#/user/bin/env python3
import cv2
import pytesseract
import re
import numpy as np
import pyautogui
import datetime
from pynput import keyboard

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

def capture_and_process(kernel_size, sigma):
    print("Hotkey pressed! Capturing screenshot...")
    screenshot = pyautogui.screenshot()
    image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    processed_image = auto_blur(image, kernel_size, sigma)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"screenshot_blurred_{timestamp}.png"
    cv2.imwrite(output_path, processed_image)
    print(f"Processed screenshot saved as '{output_path}'.")

def on_activate():
    kernel_size = 99
    sigma = 30.0
    if kernel_size % 2 == 0:
        kernel_size += 1
    capture_and_process(kernel_size, sigma)

hotkeys = keyboard.GlobalHotKeys({
    '<ctrl>+<shift>+h': on_activate
})

print("Press CTRL+SHIFT+H to capture and process a screenshot.")
print("Press CTRL+C to exit.")

hotkeys.start()
hotkeys.join()
