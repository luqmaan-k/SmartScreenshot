#!/usr/bin/env python3
import gi, subprocess, time
gi.require_version("Gtk", "3.0")
gi.require_version("Wnck", "3.0")
gi.require_version("GdkX11", "3.0")
from gi.repository import Gtk, GdkPixbuf, Gdk, Wnck, GdkX11

class ScreenshotApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Screenshot App")
        
        # Get primary monitor resolution
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        self.screen_width = geometry.width
        self.screen_height = geometry.height
        print(f"Screen resolution: {self.screen_width} x {self.screen_height}")
        
        # Set default window size relative to screen resolution.
        self.set_default_size(self.screen_width // 2, self.screen_height // 2)
        
        # Global buffer for last captured screenshot and its name.
        self.last_pixbuf = None
        self.last_capture_name = "None"
        
        # Create a Notebook (tabs) as the main container.
        notebook = Gtk.Notebook()
        self.add(notebook)
        
        # --- Tab: Window Capture ---
        window_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        window_box.set_border_width(10)
        
        # Buttons area.
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        window_box.pack_start(button_box, False, False, 0)
        
        capture_full_btn = Gtk.Button(label="Capture Full Screen")
        capture_full_btn.connect("clicked", self.on_capture_full_clicked)
        button_box.pack_start(capture_full_btn, False, False, 0)
        
        refresh_btn = Gtk.Button(label="Refresh Window List")
        refresh_btn.connect("clicked", lambda b: self.populate_window_list())
        button_box.pack_start(refresh_btn, False, False, 0)
        
        # Scrolled window for the list of windows.
        scrolled_list = Gtk.ScrolledWindow()
        scrolled_list.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_list.set_min_content_height(self.screen_height // 2)
        window_box.pack_start(scrolled_list, True, True, 0)
        
        # FlowBox to layout window "cards" (2 per row).
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(2)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_row_spacing(10)
        self.flowbox.set_column_spacing(10)
        scrolled_list.add(self.flowbox)
        self.populate_window_list()
        
        notebook.append_page(window_box, Gtk.Label(label="Window Capture"))
        
        # --- Tab: Scripts ---
        # Use a vertical Paned widget for the Scripts tab.
        script_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        
        # Connect size-allocate to split space equally.
        script_paned.connect("size-allocate", self.on_script_paned_allocate)
        
        # Top pane: script sections.
        self.script_flow = Gtk.FlowBox()
        self.script_flow.set_valign(Gtk.Align.START)
        self.script_flow.set_max_children_per_line(2)
        self.script_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.script_flow.set_row_spacing(10)
        self.script_flow.set_column_spacing(10)
        
        scrolled_scripts = Gtk.ScrolledWindow()
        scrolled_scripts.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_scripts.add(self.script_flow)
        script_paned.pack1(scrolled_scripts, True, False)
        
        # Add sample script sections.
        generic_section = self.create_script_section(
            script_title="Generic Script",
            script_name="process_image.py",
            parameters=[("Brightness", "1.0")]
        )
        ocr_section = self.create_script_section(
            script_title="OCR Script",
            script_name="ocr_script.py",
            parameters=[("Language", "eng"), ("Confidence", "0.8")]
        )
        self.script_flow.add(generic_section)
        self.script_flow.add(ocr_section)
        
        # Bottom pane: Global preview area.
        preview_scrolled = Gtk.ScrolledWindow()
        preview_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        preview_frame = Gtk.Frame(label="Last Captured Image")
        preview_frame.set_shadow_type(Gtk.ShadowType.IN)
        preview_frame.set_margin_top(10)
        preview_scrolled.add(preview_frame)
        
        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        preview_box.set_border_width(5)
        preview_frame.add(preview_box)
        
        self.last_capture_label = Gtk.Label(label="No capture yet")
        self.last_capture_label.set_xalign(0)
        preview_box.pack_start(self.last_capture_label, False, False, 0)
        
        self.global_preview = Gtk.Image()
        self.global_preview.set_hexpand(True)
        self.global_preview.set_vexpand(True)
        preview_box.pack_start(self.global_preview, True, True, 0)
        
        script_paned.pack2(preview_scrolled, False, False)
        
        notebook.append_page(script_paned, Gtk.Label(label="Scripts"))
        
        self.show_all()

    def on_script_paned_allocate(self, widget, allocation):
        # Set the divider position to half the height of the pane.
        widget.set_position(allocation.height // 2)

    def create_script_section(self, script_title, script_name, parameters):
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        section.set_border_width(5)
        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{script_title}</b>")
        title_label.set_xalign(0)
        section.pack_start(title_label, False, False, 0)
        
        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        section.pack_start(grid, False, False, 0)
        section.param_entries = []
        for i, (param_label, default) in enumerate(parameters):
            lbl = Gtk.Label(label=param_label + ":")
            lbl.set_xalign(1)
            entry = Gtk.Entry()
            entry.set_text(default)
            section.param_entries.append(entry)
            grid.attach(lbl, 0, i, 1, 1)
            grid.attach(entry, 1, i, 1, 1)
        
        btn = Gtk.Button(label=f"Run {script_title}")
        btn.connect("clicked", self.on_run_script, script_name, section)
        section.pack_start(btn, False, False, 0)
        return section

    def update_global_preview(self, pixbuf, capture_name):
        self.last_pixbuf = pixbuf
        self.last_capture_name = capture_name
        self.last_capture_label.set_text(f"Last Capture: {capture_name}")
        if pixbuf:
            orig_width = pixbuf.get_width()
            # Scale preview to half of screen width.
            target_width = self.screen_width // 2
            scale_factor = target_width / float(orig_width) if orig_width else 1
            new_height = int(pixbuf.get_height() * scale_factor)
            scaled = pixbuf.scale_simple(target_width, new_height, GdkPixbuf.InterpType.HYPER)
            self.global_preview.set_from_pixbuf(scaled)

    def show_preview_dialog(self, pixbuf, title="Preview"):
        dialog = Gtk.Dialog(title=title, transient_for=self, flags=0)
        dialog.set_default_size(800, 600)
        content_area = dialog.get_content_area()
        content_area.set_hexpand(True)
        content_area.set_vexpand(True)
        dialog.original_pixbuf = pixbuf
        
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_hexpand(True)
        container.set_vexpand(True)
        content_area.add(container)
        
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.set_hexpand(True)
        image.set_vexpand(True)
        container.pack_start(image, True, True, 0)
        
        def on_size_allocate(widget, allocation):
            orig = dialog.original_pixbuf
            if orig:
                new_width = allocation.width
                new_height = allocation.height
                scaled = orig.scale_simple(new_width, new_height, GdkPixbuf.InterpType.HYPER)
                image.set_from_pixbuf(scaled)
        container.connect("size-allocate", on_size_allocate)
        
        dialog.show_all()
        return dialog

    def on_capture_full_clicked(self, button):
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
        self.update_global_preview(pb, "Full Screen")
        self.show_preview_dialog(pb, title="Full Screen Preview")

    def populate_window_list(self):
        for child in self.flowbox.get_children():
            self.flowbox.remove(child)
        screen = Wnck.Screen.get_default()
        screen.force_update()
        windows = screen.get_windows()
        for win in windows:
            title = win.get_name()
            if title and not win.is_minimized():
                xid = win.get_xid()
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
                        new_width = self.screen_width // 4  # one-quarter of screen width
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
        self.update_global_preview(pb, button.get_label())
        self.show_preview_dialog(pb, title="Window Capture Preview")

    def on_run_script(self, button, script_name, container):
        if self.last_pixbuf is None:
            print("No capture available!")
            return
        temp_input = "last_capture.png"
        self.last_pixbuf.savev(temp_input, "png", [], [])
        params = []
        if container is not None and hasattr(container, "param_entries"):
            params = [entry.get_text() for entry in container.param_entries]
        subprocess.run(["python3", script_name, temp_input, "processed.png"] + params)
        try:
            pb_processed = GdkPixbuf.Pixbuf.new_from_file("processed.png")
            self.show_preview_dialog(pb_processed, title=f"{script_name} Preview")
        except Exception as e:
            print("Error loading processed image:", e)

    def on_process_clicked(self, button):
        self.on_run_script(button, "process_image.py", None)

if __name__ == "__main__":
    app = ScreenshotApp()
    app.connect("destroy", Gtk.main_quit)
    Gtk.main()

