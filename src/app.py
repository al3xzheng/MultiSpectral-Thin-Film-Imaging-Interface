import sys
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup, QGridLayout, QScrollArea
)
from PySide6.QtGui import QPixmap, QDoubleValidator, QFont
from PySide6.QtCore import Qt, Signal, QObject, QThread
from pathlib import Path

# External dependencies for hardware control and G-code logic
from gcode_placeholders import GCodePlaceholders
import serial

# TODO: implement graceful thread ends to prevent "zombie" processes on exit.

# ---------------- Mode Selection ----------------
class ModeSelector(QWidget):
    """
    UI Component for selecting the print pattern.
    Uses a scrollable grid to display mode names and preview images.
    """
    mode_selected = Signal(str)

    def __init__(self, modes):
        super().__init__()
        outer_layout = QVBoxLayout()

        title = QLabel("Select a Mode")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(title)

        subtitle = QLabel("Choose one of the Print modes below to continue:")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(subtitle)

        # Scroll area ensures the UI remains accessible even with many modes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner_widget = QWidget()
        grid = QGridLayout()
        inner_widget.setLayout(grid)
        scroll.setWidget(inner_widget)

        self.group = QButtonGroup(self)
        num_modes = len(modes)
        cols = min(2, num_modes) # Organize into 2 columns for symmetry

        # Dynamically build the UI based on the modes dictionary provided
        for i, (name, img_path) in enumerate(modes.items()):
            row, col = divmod(i, cols)

            container = QVBoxLayout()
            container.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Preview Image Handling
            pic = QLabel()
            pixmap = QPixmap(str(img_path))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.SmoothTransformation)
                pic.setPixmap(pixmap)
            else:
                pic.setText("[Image not found]")
                pic.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn = QRadioButton(name)
            # Map each button's toggle event to emit the specific mode name
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
        self.setLayout(outer_layout)

    def on_select(self, name, checked):
        """Notify the main window which mode has been chosen."""
        if checked:
            self.mode_selected.emit(name)


# ---------------- Parameter Inputs ----------------
class ParameterInput(QWidget):
    """
    UI Form for entering physical dimensions and printer settings.
    Uses validation to ensure research data integrity (numeric inputs only).
    """
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

        # Dynamically create labels and text fields for all requested parameters
        for i, label in enumerate(labels):
            lbl = QLabel(label)
            edit = QLineEdit()
            edit.setValidator(QDoubleValidator()) # Force numeric input at the UI level
            self.inputs[label] = edit
            grid.addWidget(lbl, i, 0)
            grid.addWidget(edit, i, 1)

        outer_layout.addLayout(grid)

        confirm = QPushButton("Confirm Parameters")
        confirm.clicked.connect(self.on_confirm)
        outer_layout.addWidget(confirm, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(outer_layout)

    def on_confirm(self):
        """Gather values from UI, cast to integers, and emit to the main application."""
        values = {k: self.inputs[k].text() for k in self.inputs}
        for k in values:
            values[k] = int(values[k]) # Note: Conversion will fail if field is empty
        self.parameters_confirmed.emit(values)

# ---------------- Worker Threads ----------------

#TODO implement timer with timer synchronization in backend and start/stop conditions.
class TimerWorker(QWidget):
    """
    Background timer logic. Inheriting from QWidget is unusual for a worker; 
    typically QObject is used for non-GUI background tasks.
    """
    time_changed = Signal(int)

    def __init__(self):
        # Local signal definitions (standard Qt practice uses class-level signals)
        tick = Signal(float)       # emits the elapsed time
        finished = Signal()

    def __init__(self):
        super().__init__()
        self._running = False

    def start_timer(self):
        """Infinite loop for timing; must be run in a separate QThread to avoid UI freezing."""
        self._running = True
        start = time.time()

        while self._running:
            elapsed = time.time() - start
            self.tick.emit(elapsed)
            time.sleep(0.1)   # 10 Hz update frequency

        self.finished.emit()

    def stop_timer(self):
        """Break the while loop to stop the timer."""
        self._running = False

#TODO serial port monitoring thread.
class SerialWorker(QObject):
    """
    Dedicated thread for monitoring the Serial Port (Microcontroller communication).
    This prevents the GUI from lagging while waiting for hardware data.
    """
    start_signal = Signal()
    stop_signal = Signal()
    finished = Signal()

    def __init__(self, port):
        super().__init__()
        self._running = True
        # Establish connection to hardware (e.g., Arduino/Printer)
        self.port = serial.Serial(port, 115200, timeout=0.1)

    def run(self):
        """Continuous polling of the serial buffer."""
        while self._running:
            line = self.port.readline().decode().strip()

            # Hardware-to-Software triggers
            if line == "START":
                self.start_signal.emit()
            elif line == "STOP":
                self.stop_signal.emit()

        self.finished.emit()

    def stop(self):
        """Stop the background polling loop."""
        self._running = False


# ---------------- Main Window ----------------
class MainWindow(QMainWindow):
    """
    Main controller for the research interface. 
    Coordinates signals between the UI, the Serial port, and the Timer.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("G-Code Writer")

        self.selected_mode = None
        self.parameters = None

        # --- UI LAYOUT SETUP ---
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

        # Paths for pattern visualization images
        modes = {
            "1": Path(__file__).parent.parent / "data" / "Scan1.png",
            "2": Path(__file__).parent.parent / "data" / "Scan2.png",
            "3": Path(__file__).parent.parent / "data" / "Scan3.png",
            "4": Path(__file__).parent.parent / "data" / "Scan4.png",
        }

        # Instantiate sub-widgets
        self.mode_selector = ModeSelector(modes)
        self.mode_selector.mode_selected.connect(self.on_mode_selected)

        self.param_input = ParameterInput(["X_initial", "Y_initial", "Z_initial", "ΔX", "ΔY", "ΔZ", "XBound", "YBound", "ZBound","Speed", "Acceleration", "Jerk", "n_x", "n_y"])
        self.param_input.parameters_confirmed.connect(self.on_params_confirmed)

        content_layout.addWidget(self.mode_selector)
        content_layout.addSpacing(40)
        content_layout.addWidget(self.param_input)
        main_layout.addLayout(content_layout)

        # Generate Button: Disabled until all inputs are validated
        self.generate_btn = QPushButton("Generate G-code")
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self.on_generate_gcode)

        # Initialize the hardware communication thread
        self.setup_serial()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.generate_btn)
        main_layout.addLayout(btn_layout)

        # Coordinate system reference image
        image_label = QLabel()
        pixmap = QPixmap(str(Path(__file__).parent.parent / "data" / "coords.png"))
        image_label.setPixmap(pixmap)
        image_label.setScaledContents(True)
        image_label.setFixedSize(120, 120)

        bottom_left_layout = QHBoxLayout()
        bottom_left_layout.addWidget(image_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        bottom_left_layout.addStretch()
        main_layout.addLayout(bottom_left_layout)

        central.setLayout(main_layout)
        self.setCentralWidget(central)
        self.resize(1000, 800)
        self.setMinimumSize(800, 600)

        # TODO Timer Display Label 
        self.label = QLabel("0.0")
        Timerlayout = QVBoxLayout()
        Timerlayout.addWidget(self.label)
        self.setLayout(Timerlayout)

        self.thread = None
        self.worker = None

    #TODO
    def start_timer(self):
        """
        Threading logic: Moves the TimerWorker to a new QThread.
        This allows the clock to tick without stuttering the UI.
        """
        self.thread = QThread()
        self.worker = TimerWorker()

        # move worker to thread to avoid affinity issues
        self.worker.moveToThread(self.thread)

        # Signals connecting the background thread to UI updates
        self.thread.started.connect(self.worker.start_timer)
        self.worker.tick.connect(self.update_label)

        # Thread cleanup instructions
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    #TODO
    def stop_timer(self):
        if self.worker:
            self.worker.stop_timer()

    #TODO
    def update_label(self, elapsed):
        """Update the UI label with the time received from the worker thread."""
        self.label.setText(f"{elapsed:.2f}")

    #TODO
    def setup_serial(self):
        """
        Initializes the Serial listener thread.
        Links hardware 'START/STOP' signals to the software timer functions.
        """
        self.serial_thread = QThread()
        self.serial_worker = SerialWorker("COM3")

        self.serial_worker.moveToThread(self.serial_thread)
        self.serial_thread.started.connect(self.serial_worker.run)

        # Cross-worker signal routing
        self.serial_worker.start_signal.connect(self.start_timer)
        self.serial_worker.stop_signal.connect(self.stop_timer)

        self.serial_thread.start()

    #TODO WITH new threads that are labeled TODO
    def closeEvent(self, event):
        """Mandatory cleanup: Ensures background threads are killed before the app closes."""
        self.serial_worker.stop()
        self.serial_thread.quit()
        self.serial_thread.wait()
        if self.worker:
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
        """Gatekeeper: Button is only usable once all experimental data is provided."""
        if self.selected_mode and self.parameters:
            self.generate_btn.setEnabled(True)

    def on_generate_gcode(self):
        """Bridge between UI and the G-code calculation backend."""
        # Instantiate backend logic with user-provided parameters
        self.generateGcode = GCodePlaceholders(int(self.selected_mode), **(self.parameters))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())