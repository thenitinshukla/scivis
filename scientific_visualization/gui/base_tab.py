"""
Common scaffolding shared by all tabs (Fields/Grid, Particles, Tracks, and
the 3D viewer), so new tabs/features can be added consistently instead of
each tab re-implementing file dialogs, scroll areas, panel positioning,
and theme handling slightly differently.

Subclasses should:
  1. call `super().__init__(parent)` -- or `super().__init__(parent,
     view_widget=<your own main view widget>)` if the tab's primary view
     isn't a Matplotlib canvas (e.g. a PyVista/QtInteractor 3D viewport;
     see gui/three_d_tab.py)
  2. build their controls into `self.control_layout` (a QVBoxLayout)
  3. call `self.finish_layout()` once at the end of __init__
  4. implement `refresh_plot(self)`

Every subclass gets the same splitter-based layout and the "Panel:
Left/Right/Top/Bottom" placement control for free, so this is the one
place that needs to change to add a layout feature to every tab at once.
"""
from __future__ import annotations

import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QColorDialog, QFileDialog, QHBoxLayout, QListWidget, QMessageBox,
    QPushButton, QScrollArea, QSplitter, QVBoxLayout, QWidget, QComboBox, QLabel,
)

from .. import style
from .plot_canvas import PlotCanvas


class BaseTab(QWidget):
    #: subclasses may override to restrict the file dialog filter text
    file_filter = "HDF5 files (*.h5 *.hdf5);;All files (*)"

    def __init__(self, parent=None, figsize=(6.5, 5.5), view_widget=None):
        super().__init__(parent)
        self.files = []
        self.theme = "Light"
        self.accent_color = QColor(style.DEFAULT_ACCENT["Light"])

        self._splitter = QSplitter(Qt.Horizontal)

        # Scrollable control panel -- this is what prevents controls from
        # being clipped/hidden when the window or panel is resized smaller
        # than the sum of all the option groups.
        control_container = QWidget()
        self.control_layout = QVBoxLayout(control_container)
        self.control_layout.setContentsMargins(6, 6, 6, 6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(control_container)
        scroll.setMinimumWidth(280)
        scroll.setMaximumWidth(16777215)
        self._splitter.addWidget(scroll)

        # Subclasses whose main view isn't a Matplotlib canvas (e.g. the 3D
        # tab's PyVista/QtInteractor viewport) can supply their own widget
        # here and still get the shared splitter, scrollable panel, and
        # panel-position controls below "for free". `self.canvas` is kept
        # as the attribute name for backward compatibility with tabs that
        # do use PlotCanvas.
        self.canvas = view_widget if view_widget is not None else PlotCanvas(figsize=figsize)
        self._splitter.addWidget(self.canvas)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setHandleWidth(8)
        self._splitter.setCollapsible(0, False)
        self._splitter.setSizes([340, 900])

        # Compact panel-placement control. The splitter remains draggable,
        # and the user can also move the controls to any outer side.
        placement_row = QHBoxLayout()
        placement_row.addWidget(QLabel("Panel:"))
        self._panel_position = QComboBox()
        self._panel_position.addItems(["Left", "Right", "Top", "Bottom"])
        self._panel_position.currentTextChanged.connect(self.set_panel_position)
        placement_row.addWidget(self._panel_position)
        placement_row.addStretch(1)
        self.control_layout.insertLayout(0, placement_row)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._splitter)


    def set_panel_position(self, position: str):
        """Move the scrollable controls to any side of the plot."""
        if not hasattr(self, "_splitter") or self._splitter.count() < 2:
            return
        panel = self._splitter.widget(0)
        canvas = self._splitter.widget(1)
        orientation = Qt.Horizontal if position in {"Left", "Right"} else Qt.Vertical
        self._splitter.setOrientation(orientation)
        # Reorder widgets using insertWidget while preserving the live widgets.
        self._splitter.insertWidget(0 if position in {"Left", "Top"} else 1, panel)
        self._splitter.insertWidget(1 if position in {"Left", "Top"} else 0, canvas)
        if orientation == Qt.Horizontal:
            self._splitter.setSizes([340, max(500, self.width() - 360)])
        else:
            self._splitter.setSizes([280, max(320, self.height() - 300)])

    def finish_layout(self):
        """Call once after all controls have been added to control_layout."""
        self.control_layout.addStretch(1)

    # -- reusable control-builders -------------------------------------
    def add_open_buttons(self, folder: bool = True, label: str = "file"):
        """Adds Open File… (and optionally Open Folder…) buttons plus a
        QListWidget that lists whichever files are currently loaded.
        Returns the QListWidget so subclasses can connect selection signals."""
        row = QHBoxLayout()
        open_file_btn = QPushButton(f"Open {label.capitalize()}…")
        open_file_btn.clicked.connect(lambda: self._open_file(label))
        row.addWidget(open_file_btn)
        if folder:
            open_folder_btn = QPushButton("Open Folder…")
            open_folder_btn.clicked.connect(lambda: self._open_folder(label))
            row.addWidget(open_folder_btn)
        self.control_layout.addLayout(row)

        file_list = QListWidget()
        self.control_layout.addWidget(file_list, stretch=1)
        self._file_list = file_list
        return file_list

    def add_color_picker_button(self, on_change, label: str = "Line color…"):
        """A button that opens a QColorDialog and calls on_change(QColor)."""
        btn = QPushButton(label)

        def pick():
            color = QColorDialog.getColor(self.accent_color, self, "Choose color")
            if color.isValid():
                self.accent_color = color
                on_change(color)
        btn.clicked.connect(pick)
        return btn

    def accent_hex(self) -> str:
        return self.accent_color.name()

    # -- file dialogs ----------------------------------------------------
    def _open_file(self, label):
        path, _ = QFileDialog.getOpenFileName(self, f"Open Simulation {label}", "", self.file_filter)
        if not path:
            return
        self.files = [path]
        self._file_list.clear()
        self._file_list.addItem(os.path.basename(path))
        self._file_list.setCurrentRow(0)

    def _open_folder(self, label):
        folder = QFileDialog.getExistingDirectory(self, f"Open folder with Simulation {label}s")
        if not folder:
            return
        files = sorted(
            os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith((".h5", ".hdf5"))
        )
        if not files:
            QMessageBox.warning(self, "No files found", "No .h5/.hdf5 files were found in that folder.")
            return
        self.files = files
        self._file_list.clear()
        for f in files:
            self._file_list.addItem(os.path.basename(f))
        self._file_list.setCurrentRow(0)

    # -- theme -------------------------------------------------------
    def set_typography(self, family: str, size: float):
        style.set_font_preferences(family, size)
        self.refresh_plot()

    def set_theme(self, theme_name: str):
        """Called by the main window when the global app theme changes."""
        self.theme = theme_name
        if hasattr(self.canvas, "set_theme"):
            self.canvas.set_theme(theme_name)
        # keep the default accent in sync unless the user picked a custom one
        if self.accent_color.name().lower() in (
            style.DEFAULT_ACCENT["Light"].lower(), style.DEFAULT_ACCENT["Dark"].lower()
        ):
            self.accent_color = QColor(style.DEFAULT_ACCENT[theme_name])
        self.refresh_plot()

    def refresh_plot(self):
        raise NotImplementedError
