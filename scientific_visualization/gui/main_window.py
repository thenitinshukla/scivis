from PyQt5.QtWidgets import QApplication, QComboBox, QLabel, QMainWindow, QTabWidget, QToolBar, QSpinBox

from .. import style
from .grid_tab import GridTab
from .particles_tab import ParticlesTab
from .tracks_tab import TracksTab
from .three_d_tab import ThreeDTab
from .ml_tab import MLTab
from .ai_tab import AITab
from .surrogate_tab import SurrogateTab
from .data_plotter_tab import DataPlotterTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scientific Visualization (Python) — Simulation Visualization")
        self.resize(1250, 780)
        self.setMinimumSize(760, 480)  # window (and its splitters) stay freely resizable above this

        toolbar = QToolBar("Appearance")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.addWidget(QLabel("  Theme: "))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(style.THEMES.keys()))
        self.theme_combo.currentTextChanged.connect(self.set_theme)
        toolbar.addWidget(self.theme_combo)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("  Font: "))
        self.font_combo = QComboBox()
        self.font_combo.addItems(style.FONT_FAMILIES)
        self.font_combo.setCurrentText(style.current_font_preferences()[0])
        self.font_combo.currentTextChanged.connect(self.set_font)
        toolbar.addWidget(self.font_combo)
        toolbar.addWidget(QLabel("  Size: "))
        self.font_size = QSpinBox()
        self.font_size.setRange(6, 32)
        self.font_size.setValue(int(round(style.current_font_preferences()[1])))
        self.font_size.valueChanged.connect(self.set_font_size)
        toolbar.addWidget(self.font_size)

        self.tabs = QTabWidget()
        self.grid_tab = GridTab()
        self.particles_tab = ParticlesTab()
        self.tracks_tab = TracksTab()
        self.three_d_tab = ThreeDTab()
        self.ml_tab = MLTab()
        self.ai_tab = AITab()
        self.surrogate_tab = SurrogateTab()
        self.data_plotter_tab = DataPlotterTab()
        self.grid_tab.dataset_changed.connect(self.ai_tab.set_dataset)
        self.grid_tab.open_in_3d_requested.connect(self.open_file_in_3d)
        self.three_d_tab.open_in_2d_requested.connect(self.open_file_in_2d)
        self.grid_tab.series_changed.connect(self.ai_tab.set_series)
        self.tabs.addTab(self.grid_tab, "Fields / Grid")
        self.tabs.addTab(self.particles_tab, "Particles")
        self.tabs.addTab(self.tracks_tab, "Tracks")
        self.tabs.addTab(self.three_d_tab, "3D Viewer")
        self.tabs.addTab(self.ml_tab, "Analysis & Modeling")
        self.tabs.addTab(self.ai_tab, "AI Analysis")
        self.tabs.addTab(self.surrogate_tab, "Surrogate Lab")
        self.tabs.addTab(self.data_plotter_tab, "Data Plotter")
        self.setCentralWidget(self.tabs)

        self.set_theme("Light")

    def open_file_in_3d(self, path: str):
        self.three_d_tab._pending_files = [path]
        self.three_d_tab.file_list.clear(); self.three_d_tab.file_list.addItem(path.split("/")[-1]); self.three_d_tab.file_list.setCurrentRow(0)
        self.three_d_tab.apply_selection()
        self.tabs.setCurrentWidget(self.three_d_tab)

    def open_file_in_2d(self, path: str):
        self.grid_tab.files = [path]
        self.grid_tab.file_list.clear(); self.grid_tab.file_list.addItem(path.split("/")[-1]); self.grid_tab.file_list.setCurrentRow(0)
        self.grid_tab.apply_selection()
        self.grid_tab.mode_2d.setChecked(True)
        self.tabs.setCurrentWidget(self.grid_tab)

    def set_font(self, family: str):
        self._apply_font_preferences(family, float(self.font_size.value()))

    def set_font_size(self, size: int):
        self._apply_font_preferences(self.font_combo.currentText(), float(size))

    def _apply_font_preferences(self, family: str, size: float):
        style.set_font_preferences(family, size)
        for tab in (self.grid_tab, self.particles_tab, self.tracks_tab, self.three_d_tab, self.ml_tab, self.ai_tab, self.surrogate_tab, self.data_plotter_tab):
            setter = getattr(tab, "set_typography", None)
            if setter is not None:
                setter(family, size)

    def set_theme(self, name: str):
        """Applies the theme to the whole application (Qt widget chrome)
        as well as to every tab's matplotlib figure, so 'Dark' really means
        the whole app goes dark, not just the plots."""
        app = QApplication.instance()
        if app is not None:
            style.apply_app_theme(app, name)
        for tab in (
            self.grid_tab, self.particles_tab, self.tracks_tab, self.three_d_tab,
            self.ml_tab, self.ai_tab, self.surrogate_tab, self.data_plotter_tab,
        ):
            setter = getattr(tab, "set_theme", None)
            if setter is not None:
                setter(name)
