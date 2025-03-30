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

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scrolled_main = Gtk.ScrolledWindow()
        scrolled_main.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_main.add(main_vbox)
        self.add(scrolled_main)

        # Full-screen capture area
        full_label = Gtk.Label(label="Full Screen Capture:")
        main_vbox.pack_start(full_label, False, False, 0)

        self.full_preview = Gtk.Image()
        main_vbox.pack_start(self.full_preview, True, True, 0)

        capture_full_btn = Gtk.Button(label="Capture Full Screen")
        capture_full_btn.connect("clicked", self.on_capture_full_clicked)
        main_vbox.pack_start(capture_full_btn, False, False, 0)

        # Window capture list
        list_label = Gtk.Label(label="Capture Specific Window:")
        main_vbox.pack_start(list_label, False, False, 0)

        refresh_btn = Gtk.Button(label="Refresh Window List")
        refresh_btn.connect("clicked", lambda b: self.populate_window_list())
        main_vbox.pack_start(refresh_btn, False, False, 0)

        # Scrolled window to hold a FlowBox
        scrolled_list = Gtk.ScrolledWindow()
        scrolled_list.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # Minimum height so the thumbnails are not cut off
        scrolled_list.set_min_content_height(720)
        main_vbox.pack_start(scrolled_list, False, False, 0)

        # FlowBox that will show 2 items per row
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(2)  # 2 items per row
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_row_spacing(10)
        self.flowbox.set_column_spacing(10)

        scrolled_list.add(self.flowbox)

        self.populate_window_list()

        # Processed screenshot preview
        proc_label = Gtk.Label(label="Processed Screenshot Preview:")
        main_vbox.pack_start(proc_label, False, False, 0)

        self.processed_image = Gtk.Image()
        main_vbox.pack_start(self.processed_image, True, True, 0)

        process_btn = Gtk.Button(label="Process Full Screenshot")
        process_btn.connect("clicked", self.on_process_clicked)
        main_vbox.pack_start(process_btn, False, False, 0)

        self.show_all()

    def populate_window_list(self):
        # Clear existing items
        for child in self.flowbox.get_children():
            self.flowbox.remove(child)

        screen = Wnck.Screen.get_default()
        screen.force_update()
        windows = screen.get_windows()

        for win in windows:
            title = win.get_name()
            if title and not win.is_minimized():
                xid = win.get_xid()

                # We'll create a vertical box: Button on top, thumbnail below
                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

                # Button with window title
                btn = Gtk.Button(label=title)
                btn.xid = xid
                btn.connect("clicked", self.on_window_button_clicked)
                vbox.pack_start(btn, False, False, 0)

                # Attempt a small live thumbnail
                display = Gdk.Display.get_default()
                gdk_win = GdkX11.X11Window.foreign_new_for_display(display, xid)
                thumb = None
                if gdk_win:
                    geom = gdk_win.get_geometry()
                    w_width, w_height = geom.width, geom.height
                    pb = Gdk.pixbuf_get_from_window(gdk_win, 0, 0, w_width, w_height)
                    if pb:
                        # Scale to 200 px wide
                        new_width = 480
                        scale_factor = new_width / float(w_width) if w_width else 1
                        new_height = int(w_height * scale_factor) if w_height else 0
                        if new_width > 0 and new_height > 0:
                            thumb = pb.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)

                # If capturing live thumbnail fails, fallback to window icon
                if not thumb:
                    thumb = win.get_icon()  # might be None or a default icon

                image_widget = Gtk.Image()
                if thumb:
                    image_widget.set_from_pixbuf(thumb)
                else:
                    # fallback to a generic icon name
                    image_widget.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)

                vbox.pack_start(image_widget, False, False, 0)

                self.flowbox.add(vbox)

        self.flowbox.show_all()

    def on_capture_full_clicked(self, button):
        # Hide the app window
        self.hide()
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
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
        new_width = 960
        scale_factor = new_width / float(width)
        new_height = int(height * scale_factor)
        scaled_pb = pb.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)
        self.full_preview.set_from_pixbuf(scaled_pb)

    def on_window_button_clicked(self, button):
        xid = button.xid
        display = Gdk.Display.get_default()
        gdk_win = GdkX11.X11Window.foreign_new_for_display(display, xid)
        if not gdk_win:
            print("Failed to get Gdk.Window for XID", xid)
            return
        geom = gdk_win.get_geometry()
        width, height = geom.width, geom.height

        self.hide()
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.5)
        pb = Gdk.pixbuf_get_from_window(gdk_win, 0, 0, width, height)
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
        # Example brightness
        brightness = 1.0
        subprocess.run(["python3", "process_image.py", "screenshot.png", "processed.png", str(brightness)])
        pb_processed = GdkPixbuf.Pixbuf.new_from_file("processed.png")
        self.processed_image.set_from_pixbuf(pb_processed)

if __name__ == "__main__":
    app = ScreenshotApp()
    app.connect("destroy", Gtk.main_quit)
    Gtk.main()

