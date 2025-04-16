# SmartScreenshot

SmartScreenshot is a GTK-based application for capturing screenshots (full-screen and window capture), processing them (e.g., blurring sensitive text using OCR), and running user-configurable scripts on the captured images. It supports both X11 and Wayland (for full-screen capture) using external tools.

## Features

- **Full-Screen & Window Capture:** Capture full-screen screenshots or capture a specific window.
- **Image Processing:** Automatically blur sensitive regions using OCR with configurable parameters.
- **Custom Script Integration:** Configure and run custom scripts on the captured images.
- **Clipboard Support:** Automatically copy the processed image to the clipboard.
- **External Viewer:** Opens processed images using the user’s default (or configured) image viewer.
- **Configurable Parameters:** Resolution overrides, capture delay, border sizes, and more can be set in a configuration file.

## Requirements

- Python 3
- GTK 3
- OpenCV (`cv2`)
- pytesseract  
  (Make sure Tesseract OCR is installed and available in your PATH or specify its full path in your environment.)
- Grim (for Wayland full-screen capture)
- A Linux system (for xdg-open and other Linux utilities)
- sudo dnf install gnome-screenshot

## Installation

1. **Install Tesseract OCR:**  
   On Fedora, you can install it via:
   ```bash
   sudo dnf install tesseract
   ```
   On Ubuntu:
   ```bash
   sudo apt-get install tesseract-ocr
   ```
2. **Install Python Dependencies:**
   ```bash
   pip install opencv-python pytesseract
   ```

## Usage

Run the application using:
```bash
python3 app.py
```
By default, the application uses the configuration file located at:
```
~/.config/smartscreenshot/smartscreenshot.ini
```
You can also specify an alternate configuration file via the command line:
```bash
python3 app.py /path/to/your_config.ini
```

### Tabs

- **Window Capture Tab:**  
  - Capture full-screen images or a specific window.
  - Upload an image from disk.
  - Thumbnails of available windows are shown with borders.
  
- **Scripts Tab:**  
  - View a list of custom scripts (configured in an external JSON file).
  - Run a script on the last captured (or uploaded) image.
  - Preview the processed image with your system’s default image viewer.
  - Processed images are automatically copied to the clipboard.

## Configuration

### Main Configuration File

The main configuration file (default at `~/.config/smartscreenshot/smartscreenshot.ini`) controls general application settings. For example:

```ini
[General]
override_width =          ; Leave blank to use the actual screen width.
override_height =         ; Leave blank to use the actual screen height.
main_border_width = 10
thumbnail_scale_divisor = 4
global_preview_scale_fraction = 0.5
container_border = 2
capture_delay = 0.5
scripts_config = ~/.config/smartscreenshot/scripts.json
image_viewer = xdg-open
```

- **override_width/override_height:**  
  If specified, these override the detected screen resolution.
  
- **main_border_width:**  
  Sets the outer border width for main containers.
  
- **thumbnail_scale_divisor:**  
  Determines thumbnail size as `screen_width // thumbnail_scale_divisor`.
  
- **global_preview_scale_fraction:**  
  Sets the width of the global preview (as a fraction of the screen width).
  
- **container_border:**  
  Sets the border thickness for framed containers.
  
- **capture_delay:**  
  Time (in seconds) to wait before taking a screenshot.
  
- **scripts_config:**  
  Path to the external scripts configuration file.
  
- **image_viewer:**  
  The command to open images externally (default: `xdg-open`).

### Scripts Configuration File

The scripts configuration is stored in a separate JSON file (default at `~/.config/smartscreenshot/scripts.json`). This file allows end users to add or modify custom scripts. Each script must follow a standard interface: it must accept the following command-line arguments (in order):

1. **Input Image Path** – The file path of the image to process (e.g. `"last_capture.png"`).
2. **Output Image Path** – The file path where the processed image should be saved (e.g. `"processed.png"`).
3. **Additional Parameters:**  
   Any extra parameters required by the script (e.g., kernel size, sigma, keywords).

A sample `scripts.json` file might look like this:

```json
{
  "scripts": [
    {
      "name": "Generic Blur",
      "path": "../scripts/secrets-handling/main.py",
      "parameters": [
        {"label": "Kernel Size", "default": "99"},
        {"label": "Sigma", "default": "30"}
      ]
    },
    {
      "name": "Custom Keyword Blur",
      "path": "../scripts/secrets-handling-custom-keywords/main.py",
      "parameters": [
        {"label": "Kernel Size", "default": "99"},
        {"label": "Sigma", "default": "30"},
        {"label": "Keywords (comma-separated)", "default": "password,name"}
      ]
    }
  ]
}
```

**Notes for Script Authors:**

- Your script should read command-line arguments as follows:
  ```bash
  python3 <script_path> <input_image> <output_image> [param1] [param2] ...
  ```
- Ensure your script handles default values appropriately if parameters are missing.
- If your script modifies the image, it should save the output to the specified `<output_image>`.

## Troubleshooting

- **Tesseract Not Found:**  
  If you get an error from pytesseract, ensure Tesseract OCR is installed and available in your PATH.
- **Wayland Support:**  
  For Wayland, full-screen capture uses the external tool `grim`. Make sure it is installed.
- **Relative Paths:**  
  The application uses relative paths based on its working directory. For consistency, consider using absolute paths in your configuration if needed.

## License

[Will do later...]
