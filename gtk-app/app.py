#!/usr/bin/env python3
import gi, subprocess, time
gi.require_version("Gtk", "3.0")
gi.require_version("Wnck", "3.0")
gi.require_version("GdkX11", "3.0")
from gi.repository import Gtk, GdkPixbuf, Gdk, Wnck, GdkX11

class ScreenshotApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Screenshot App")
        self.set_default_size(1000, 700)

        # Main container
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_vbox)

        # Section: Full-screen capture
        full_label = Gtk.Label(label="Full Screen Capture:")
        main_vbox.pack_start(full_label, False, False, 0)

        self.full_preview = Gtk.Image()
        main_vbox.pack_start(self.full_preview, True, True, 0)

        capture_full_btn = Gtk.Button(label="Capture Full Screen")
        capture_full_btn.connect("clicked", self.on_capture_full_clicked)
        main_vbox.pack_start(capture_full_btn, False, False, 0)

        # Section: Window capture list
        list_label = Gtk.Label(label="Capture Specific Window:")
        main_vbox.pack_start(list_label, False, False, 0)

        # A scrolled window to hold the list of windows
        scrolled_list = Gtk.ScrolledWindow()
        scrolled_list.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_list.set_min_content_height(150)
        main_vbox.pack_start(scrolled_list, False, False, 0)

        # Box to hold buttons for each window
        self.window_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        scrolled_list.add(self.window_list_box)

        self.populate_window_list()

        # Section: Processed screenshot preview
        proc_label = Gtk.Label(label="Processed Screenshot Preview:")
        main_vbox.pack_start(proc_label, False, False, 0)

        self.processed_image = Gtk.Image()
        main_vbox.pack_start(self.processed_image, True, True, 0)

        # Button to process the full screenshot
        process_btn = Gtk.Button(label="Process Full Screenshot")
        process_btn.connect("clicked", self.on_process_clicked)
        main_vbox.pack_start(process_btn, False, False, 0)

        self.show_all()

    def populate_window_list(self):
        # Clear existing children
        for child in self.window_list_box.get_children():
            self.window_list_box.remove(child)

        screen = Wnck.Screen.get_default()
        screen.force_update()
        windows = screen.get_windows()
        for win in windows:
            title = win.get_name()
            # Check that the window is not minimized
            if title and not win.is_minimized():
                btn = Gtk.Button(label=title)
                # Attach the xid as a normal attribute (avoid set_data)
                btn.xid = win.get_xid()
                btn.connect("clicked", self.on_window_button_clicked)
                self.window_list_box.pack_start(btn, False, False, 0)
        self.window_list_box.show_all()

    def on_capture_full_clicked(self, button):
        # Hide the app window so it isn't captured
        self.hide()
        # Process pending events so that the window is really hidden
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        # Wait a little more if needed
        time.sleep(0.5)

        root_window = Gdk.get_default_root_window()
        width = root_window.get_width()
        height = root_window.get_height()

        pb = Gdk.pixbuf_get_from_window(root_window, 0, 0, width, height)
        self.show()

        if not pb:
            print("Screenshot failed (pb is None). Are you on X11?")
            return

        pb.savev("screenshot.png", "png", [], [])
        # Scale for preview (e.g., 960px wide)
        new_width = 960
        scale_factor = new_width / float(width)
        new_height = int(height * scale_factor)
        scaled_pb = pb.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)
        self.full_preview.set_from_pixbuf(scaled_pb)

    def on_window_button_clicked(self, button):
        xid = button.xid  # Access our attribute directly
        display = Gdk.Display.get_default()
        # Use the correct class: GdkX11.X11Window
        gdk_window = GdkX11.X11Window.foreign_new_for_display(display, xid)
        if not gdk_window:
            print("Failed to get Gdk.Window for XID", xid)
            return

        geom = gdk_window.get_geometry()
        width, height = geom.width, geom.height

        self.hide()
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.5)
        pb = Gdk.pixbuf_get_from_window(gdk_window, 0, 0, width, height)
        self.show()

        if not pb:
            print("Failed to capture window with XID", xid)
            return

        pb.savev("window_screenshot.png", "png", [], [])
        # Scale for preview (e.g., 480px wide)
        new_width = 480
        scale_factor = new_width / float(width)
        new_height = int(height * scale_factor)
        scaled_pb = pb.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)
        self.full_preview.set_from_pixbuf(scaled_pb)

    def on_process_clicked(self, button):
        brightness = self.scale.get_value()
        subprocess.run(["python3", "process_image.py", "screenshot.png", "processed.png", str(brightness)])
        pb_processed = GdkPixbuf.Pixbuf.new_from_file("processed.png")
        self.processed_image.set_from_pixbuf(pb_processed)

if __name__ == "__main__":
    app = ScreenshotApp()
    app.connect("destroy", Gtk.main_quit)
    Gtk.main()

