import os
from views.base_view import BaseView
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QToolButton
from PySide6.QtCore import QSize, Qt

# Padding added around the icon inside each button (px, both sides)
_BTN_PADDING = 0
# Maximum dimension (height or width) for button icons
_MAX_ICON_DIM = 300

_BTN_STYLESHEET = """
    QToolButton {
        background-color: #949494;
        border: none;
        border-radius: 50px;
        padding: 0px;
    }
    QToolButton:hover {
        background-color: #bdbdbd;
        border: none;
    }
    QToolButton:pressed {
        background-color: #bdbdbd;
        border: none;
    }
"""


class MainMenuView(BaseView):
    def __init__(self):
        super().__init__(os.path.join("ui", "main_menu", "main_menu.ui"))
        self._setup_header_logos()
        self._setup_buttons()

    def _setup_buttons(self):
        """Set icon-only style, correct size (preserving aspect ratio) and dark background on each button."""
        base = os.path.join("resources", "images")
        button_images = {
            "btnSettings":      os.path.join(base, "settings.png"),
            "btnExperiment":    os.path.join(base, "ExpModule.png"),
            "btnVisualization": os.path.join(base, "VerData.png"),
            "btnAnalysis":      os.path.join(base, "DataAnali.png"),
        }

        for btn_name, img_path in button_images.items():
            btn = self.ui.findChild(QToolButton, btn_name)
            if btn is None:
                continue

            # --- Icon-only, no text ---
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

            # --- Size: preserve aspect ratio of the actual image ---
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                img_w = pixmap.width()
                img_h = pixmap.height()
                if img_w >= img_h:
                    icon_w = _MAX_ICON_DIM
                    icon_h = int(img_h * _MAX_ICON_DIM / img_w)
                else:
                    icon_h = _MAX_ICON_DIM
                    icon_w = int(img_w * _MAX_ICON_DIM / img_h)
                btn.setIconSize(QSize(icon_w, icon_h))
                btn.setFixedSize(icon_w + _BTN_PADDING * 2, icon_h + _BTN_PADDING * 2)

            # --- Background color that contrasts with #E0E0E0 ---
            btn.setStyleSheet(_BTN_STYLESHEET)
