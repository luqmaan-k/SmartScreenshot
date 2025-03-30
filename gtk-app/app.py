#!/usr/bin/env python3
import gi, subprocess
gi.require_version("Gtk", "3.0")  # or "4.0" if you prefer GTK 4
from gi.repository import Gtk, GdkPixbuf, Gdk

class ScreenshotApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Screenshot App")
        self.set_default_size(800, 600)

        # Main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        # Image widget to display screenshot preview
        self.screenshot_image = Gtk.Image()
        vbox.pack_start(self.screenshot_image, True, True, 0)

        # Button to capture screenshot
        capture_button = Gtk.Button(label="Capture Full Screen")
        capture_button.connect("clicked", self.on_capture_clicked)
        vbox.pack_start(capture_button, False, False, 0)

        # Adjustable parameter (e.g. brightness)
        adj = Gtk.Adjustment.new(value=1.0, lower=0.0, upper=2.0, step_increment=0.1, page_increment=0.0, page_size=0.0)
        self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        self.scale.set_digits(1)
        vbox.pack_start(self.scale, False, False, 0)

        # Button to process the screenshot (simulate by running a script)
        process_button = Gtk.Button(label="Process Screenshot")
        process_button.connect("clicked", self.on_process_clicked)
        vbox.pack_start(process_button, False, False, 0)

        # Processed image preview (could be same widget or separate)
        self.processed_image = Gtk.Image()
        vbox.pack_start(self.processed_image, True, True, 0)

        self.show_all()

    def on_capture_clicked(self, button):
        # Capture the full screen using GdkPixbuf
        root_window = Gdk.get_default_root_window()
        width = root_window.get_width()
        height = root_window.get_height()
        # Get screenshot (full screen)
        pb = Gdk.pixbuf_get_from_window(root_window, 0, 0, width, height)
        # Optionally, save it to file
        pb.savev("screenshot.png", "png", [], [])
        self.screenshot_image.set_from_pixbuf(pb)

    def on_process_clicked(self, button):
        # Read the adjustable parameter (for example, brightness factor)
        brightness = self.scale.get_value()
        # Here we simulate processing: you could call an external script or process with Pillow
        # For demonstration, let's assume we have a script called "process_image.py"
        # that accepts input and output file names and a brightness parameter.
        subprocess.run(["python3", "process_image.py", "screenshot.png", "processed.png", str(brightness)])
        # Load the processed image and update preview
        pb_processed = GdkPixbuf.Pixbuf.new_from_file("processed.png")
        self.processed_image.set_from_pixbuf(pb_processed)

win = ScreenshotApp()
win.connect("destroy", Gtk.main_quit)
Gtk.main()

