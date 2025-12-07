import sys
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup, QGridLayout, QScrollArea
)
from PySide6.QtGui import QPixmap, QDoubleValidator, QFont
from PySide6.QtCore import Qt, Signal, QObject, QThread
from pathlib import Path

# The backend
from gcode_placeholders import GCodePlaceholders
import serial
# from RunTimer import Timer


#TODO implement graceful thread ends.

# ---------------- Mode Selection ----------------
class ModeSelector(QWidget):
    mode_selected = Signal(str)

    def __init__(self, modes):
        super().__init__()
        outer_layout = QVBoxLayout()
        # outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Select a Mode")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(title)

        subtitle = QLabel("Choose one of the Print modes below to continue:")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # scroll.setAlignment(Qt.AlignmentFlag.AlignTop)
        #scroll.setMinimumSize(600, 400)
        inner_widget = QWidget()
        grid = QGridLayout()
        # grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner_widget.setLayout(grid)
        scroll.setWidget(inner_widget)
        # outer_layout.addWidget(scroll)

        self.group = QButtonGroup(self)
        num_modes = len(modes)
        cols = min(2, num_modes)

        for i, (name, img_path) in enumerate(modes.items()):
            row, col = divmod(i, cols)

            container = QVBoxLayout()
            container.setAlignment(Qt.AlignmentFlag.AlignCenter)

            pic = QLabel()
            pixmap = QPixmap(str(img_path))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.SmoothTransformation)
                pic.setPixmap(pixmap)
            else:
                pic.setText("[Image not found]")
                pic.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn = QRadioButton(name)
            btn.toggled.connect(lambda checked, n=name: self.on_select(n, checked))
            self.group.addButton(btn)

            container.addWidget(pic)
            container.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            cell = QWidget()
            cell.setLayout(container)
            grid.addWidget(cell, row, col)

        inner_widget.setLayout(grid)
        scroll.setWidget(inner_widget)
        outer_layout.addWidget(scroll)
        # outer_layout.addStretch()
        self.setLayout(outer_layout)

    def on_select(self, name, checked):
        if checked:
            self.mode_selected.emit(name)


# ---------------- Parameter Inputs ----------------
class ParameterInput(QWidget):
    parameters_confirmed = Signal(dict)

    def __init__(self, labels):
        super().__init__()
        outer_layout = QVBoxLayout()
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Enter Print Parameters")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(title)

        subtitle = QLabel("Provide parameters below [ X < 245, Y < 245, Z < 200, ΔD/k = 0 (mod k)]:")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inputs = {}

        for i, label in enumerate(labels):
            lbl = QLabel(label)
            edit = QLineEdit()
            edit.setValidator(QDoubleValidator())
            self.inputs[label] = edit
            grid.addWidget(lbl, i, 0)
            grid.addWidget(edit, i, 1)

        outer_layout.addLayout(grid)

        confirm = QPushButton("Confirm Parameters")
        confirm.clicked.connect(self.on_confirm)
        outer_layout.addWidget(confirm, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(outer_layout)

    def on_confirm(self):
        values = {k: self.inputs[k].text() for k in self.inputs}
        for k in values:
            values[k] = int(values[k])
        self.parameters_confirmed.emit(values)

class TimerWorker(QWidget):

    time_changed = Signal(int)

    def __init__(self):
        tick = Signal(float)       # emits the elapsed time
        finished = Signal()

    def __init__(self):
        super().__init__()
        self._running = False

    def start_timer(self):
        self._running = True
        start = time.time()

        while self._running:
            elapsed = time.time() - start
            self.tick.emit(elapsed)
            time.sleep(0.1)   # 10 Hz update; adjust as needed

        self.finished.emit()

    def stop_timer(self):
        self._running = False

class SerialWorker(QObject):

    start_signal = Signal()
    stop_signal = Signal()
    finished = Signal()

    def __init__(self, port):
        super().__init__()
        self._running = True
        self.port = serial.Serial(port, 115200, timeout=0.1)

    def run(self):
        while self._running:
            line = self.port.readline().decode().strip()

            if line == "START":
                self.start_signal.emit()

            elif line == "STOP":
                self.stop_signal.emit()

            # time.sleep(0.01)

        self.finished.emit()

    def stop(self):
        self._running = False


# ---------------- Main Window ----------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("G-Code Writer")

        self.selected_mode = None
        self.parameters = None

        central = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        title = QLabel("3D-Printer Print Pattern Configuration")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Use this interface to select a print mode and define the print parameters")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(20)

        content_layout = QHBoxLayout()
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        modes = {
            "1": Path(__file__).parent.parent / "data" / "Scan1.png",
            "2": Path(__file__).parent.parent / "data" / "Scan2.png",
            "3": Path(__file__).parent.parent / "data" / "Scan3.png",
            "4": Path(__file__).parent.parent / "data" / "Scan4.png",
        }

        self.mode_selector = ModeSelector(modes)
        self.mode_selector.mode_selected.connect(self.on_mode_selected)

        self.param_input = ParameterInput(["X_initial", "Y_initial", "Z_initial", "ΔX", "ΔY", "ΔZ", "XBound", "YBound", "ZBound","Speed", "Acceleration", "Jerk", "n_x", "n_y"])
        self.param_input.parameters_confirmed.connect(self.on_params_confirmed)

        # self.timer_display = TimerDisplay()
        # self.timer_display.time_changed.connect(self.on_mode_selected)

        content_layout.addWidget(self.mode_selector)
        content_layout.addSpacing(40)
        content_layout.addWidget(self.param_input)
        main_layout.addLayout(content_layout)
        # main_layout.addWidget(self.timer_display)

        # Gcode button
        self.generate_btn = QPushButton("Generate G-code")
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self.on_generate_gcode)

        self.setup_serial()

        # Align bottom-right
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.generate_btn)
        main_layout.addLayout(btn_layout)

        image_label = QLabel()
        pixmap = QPixmap(str(Path(__file__).parent.parent / "data" / "coords.png"))
        image_label.setPixmap(pixmap)
        image_label.setScaledContents(True)
        image_label.setFixedSize(120, 120)

        bottom_left_layout = QHBoxLayout()
        bottom_left_layout.addWidget(image_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        bottom_left_layout.addStretch()
        main_layout.addLayout(bottom_left_layout)
        # -----------------------------------

        # main_layout.addStretch()
        central.setLayout(main_layout)
        self.setCentralWidget(central)
        self.resize(1000, 800)
        self.setMinimumSize(800, 600)

        self.label = QLabel("0.0")
        # self.start_btn = QPushButton("Start")
        # self.stop_btn = QPushButton("Stop")

        Timerlayout = QVBoxLayout()
        Timerlayout.addWidget(self.label)
        # layout.addWidget(self.start_btn)
        # layout.addWidget(self.stop_btn)
        self.setLayout(Timerlayout)

        self.thread = None
        self.worker = None

        # self.start_btn.clicked.connect(self.start_timer)
        # self.stop_btn.clicked.connect(self.stop_timer)

    def start_timer(self):
        self.thread = QThread()
        self.worker = TimerWorker()

        # move worker to thread
        self.worker.moveToThread(self.thread)

        # wire up thread start → worker start
        self.thread.started.connect(self.worker.start_timer)

        # worker emits tick → update GUI
        self.worker.tick.connect(self.update_label)

        # cleanup
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def stop_timer(self):
        if self.worker:
            self.worker.stop_timer()

    def update_label(self, elapsed):
        self.label.setText(f"{elapsed:.2f}")

    def setup_serial(self):
        self.serial_thread = QThread()
        self.serial_worker = SerialWorker("COM3")

        self.serial_worker.moveToThread(self.serial_thread)
        self.serial_thread.started.connect(self.serial_worker.run)

        # hook serial messages to timer
        self.serial_worker.start_signal.connect(self.start_timer)
        self.serial_worker.stop_signal.connect(self.stop_timer)

        self.serial_thread.start()

    def closeEvent(self, event):
        # Make sure to stop threads on exit
        self.serial_worker.stop()
        self.serial_thread.quit()
        self.serial_thread.wait()
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)

    def on_mode_selected(self, mode):
        self.selected_mode = mode
        self.check_ready()

    def on_params_confirmed(self, params):
        self.parameters = params
        self.check_ready()

    def check_ready(self):
        """Enable button only when both selections are ready."""
        if self.selected_mode and self.parameters:
            self.generate_btn.setEnabled(True)

    def on_generate_gcode(self):
        # del self.generateGcode
        self.generateGcode = GCodePlaceholders(int(self.selected_mode), **(self.parameters))
        # self.generateGcode = GCodePlaceholders(desired thing).
        # self.generate_gcode(self.selected_mode, **self.parameters)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
