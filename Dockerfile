FROM fedora:40

ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN dnf -y update && \
    dnf install -y \
        python3 \
        python3-pip \
        python3-devel \
        python3-tkinter \
        gnome-screenshot \
        xorg-x11-server-Xvfb \
        libX11 \
        libXext \
        libXrandr \
        libXcursor \
        libXcomposite \
        libXdamage \
        libXfixes \
        libXi \
        libXtst \
        libXScrnSaver \
        gtk3 \
        cairo \
        gdk-pixbuf2 \
        glib2 \
        dbus-glib \
        libjpeg-turbo \
        libpng \
        freetype \
        lcms2 \
        libtiff \
        libwebp \
        tcl \
        tk \
        && dnf clean all

RUN pip3 install --no-cache-dir \
    pyautogui \
    pillow \
    opencv-python \
    pytesseract \
    pynput

WORKDIR /app

COPY . /app

ENV DISPLAY=:99

CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 & python3 gtk-app/main.py"]
