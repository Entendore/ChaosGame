"""
Chaos Game Fractal Generator — Entry Point
"""

import sys
import os
import logging

# Configure terminal logging BEFORE any other local imports
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)-8s %(name)-18s - %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stderr
)
logger = logging.getLogger("App")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"


def main():
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtCore import Qt

    logger.info("Initializing application...")
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Chaos Game Fractal Generator")
    app.setApplicationVersion("2.0.0")

    from main_window import ChaosGameMainWindow
    window = ChaosGameMainWindow()
    window.show()
    
    logger.info("GUI ready.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()