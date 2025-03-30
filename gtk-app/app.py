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

        # Create a Notebook (tabs) as the main container
        notebook = Gtk.Notebook()
        self.add(notebook)

        # --- Tab 1: Full Screen Capture ---
        full_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        full_box.set_border_width(10)
        capture_full_btn = Gtk.Button(label="Capture Full Screen")
        capture_full_btn.connect("clicked", self.on_capture_full_clicked)
        full_box.pack_start(capture_full_btn, False, False, 0)
        notebook.append_page(full_box, Gtk.Label(label="Full Screen"))

        # --- Tab 2: Window Capture ---
        window_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        window_box.set_border_width(10)
        refresh_btn = Gtk.Button(label="Refresh Window List")
        refresh_btn.connect("clicked", lambda b: self.populate_window_list())
        window_box.pack_start(refresh_btn, False, False, 0)
        # Scrolled window for the list of windows
        scrolled_list = Gtk.ScrolledWindow()
        scrolled_list.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_list.set_min_content_height(480)
        window_box.pack_start(scrolled_list, True, True, 0)
        # Use a FlowBox to layout window "cards" (2 per row)
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(2)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_row_spacing(10)
        self.flowbox.set_column_spacing(10)
        scrolled_list.add(self.flowbox)
        self.populate_window_list()
        notebook.append_page(window_box, Gtk.Label(label="Window Capture"))

        # --- Tab 3: Processed Screenshot ---
        proc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        proc_box.set_border_width(10)
        # Adjustable parameter (e.g., brightness)
        adj = Gtk.Adjustment.new(value=1.0, lower=0.0, upper=2.0, step_increment=0.1, page_increment=0.0, page_size=0.0)
        self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        self.scale.set_digits(1)
        proc_box.pack_start(self.scale, False, False, 0)
        process_btn = Gtk.Button(label="Process Full Screenshot")
        process_btn.connect("clicked", self.on_process_clicked)
        proc_box.pack_start(process_btn, False, False, 0)
        notebook.append_page(proc_box, Gtk.Label(label="Processed"))

        self.show_all()

    def show_preview_popup(self, pixbuf, title="Preview"):
        # Create a new popup window for preview
        popup = Gtk.Window(title=title)
        popup.set_transient_for(self)
        popup.set_default_size(800, 600)
        popup.set_resizable(True)
        
        # Store the original full-res pixbuf for dynamic scaling
        popup.original_pixbuf = pixbuf
        
        # Create a container; connect its size-allocate signal to update the image dynamically.
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_hexpand(True)
        container.set_vexpand(True)
        popup.add(container)
        
        # Create the image widget that will display the pixbuf
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.set_hexpand(True)
        image.set_vexpand(True)
        container.pack_start(image, True, True, 0)
        
        # Connect the size-allocate on the container rather than the popup itself.
        def on_size_allocate(widget, allocation):
            orig = popup.original_pixbuf
            if orig:
                new_width = allocation.width
                new_height = allocation.height
                scaled = orig.scale_simple(new_width, new_height, GdkPixbuf.InterpType.HYPER)
                image.set_from_pixbuf(scaled)
        container.connect("size-allocate", on_size_allocate)
        
        popup.show_all()

    def on_capture_full_clicked(self, button):
        # Hide the app window so it isn't captured
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
        # Pass the original full-res pixbuf for the popup preview.
        self.show_preview_popup(pb, title="Full Screen Preview")

    def populate_window_list(self):
        # Remove all current children in the flowbox
        for child in self.flowbox.get_children():
            self.flowbox.remove(child)
            
        screen = Wnck.Screen.get_default()
        screen.force_update()
        windows = screen.get_windows()
        for win in windows:
            title = win.get_name()
            if title and not win.is_minimized():
                xid = win.get_xid()
                # Create a vertical "card": button on top, thumbnail below.
                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                btn = Gtk.Button(label=title)
                btn.xid = xid
                btn.connect("clicked", self.on_window_button_clicked)
                vbox.pack_start(btn, False, False, 0)
                
                display = Gdk.Display.get_default()
                gdk_win = GdkX11.X11Window.foreign_new_for_display(display, xid)
                thumb = None
                if gdk_win:
                    geom = gdk_win.get_geometry()
                    w_width, w_height = geom.width, geom.height
                    pb = Gdk.pixbuf_get_from_window(gdk_win, 0, 0, w_width, w_height)
                    if pb:
                        new_width = 480
                        scale_factor = new_width / float(w_width) if w_width else 1
                        new_height = int(w_height * scale_factor) if w_height else 0
                        if new_width > 0 and new_height > 0:
                            thumb = pb.scale_simple(new_width, new_height, GdkPixbuf.InterpType.HYPER)
                if not thumb:
                    thumb = win.get_icon()
                image_widget = Gtk.Image()
                if thumb:
                    image_widget.set_from_pixbuf(thumb)
                else:
                    image_widget.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
                vbox.pack_start(image_widget, False, False, 0)
                self.flowbox.add(vbox)
        self.flowbox.show_all()

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
        # Pass the full-res capture for popup preview
        self.show_preview_popup(pb, title="Window Capture Preview")
        
    def on_process_clicked(self, button):
        brightness = self.scale.get_value()
        subprocess.run(["python3", "process_image.py", "screenshot.png", "processed.png", str(brightness)])
        pb_processed = GdkPixbuf.Pixbuf.new_from_file("processed.png")
        self.show_preview_popup(pb_processed, title="Processed Screenshot Preview")

if __name__ == "__main__":
    app = ScreenshotApp()
    app.connect("destroy", Gtk.main_quit)
    Gtk.main()
