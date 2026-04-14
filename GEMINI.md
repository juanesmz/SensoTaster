# SensoTaster - Project Guidelines

SensoTaster is a sensory evaluation platform designed to capture and analyze sensory responses (EMG, gas, microphone, and camera) during tasting experiments.

## Project Overview

- **Architecture**: Model-View-Controller (MVC) using PySide6.
  - **Models**: Data structures for experiments, measurements, and users (`models/`).
  - **Views**: Qt-based UI components. Most views inherit from `BaseView` and load `.ui` files dynamically via `QUiLoader` (`views/`).
  - **Controllers**: Logic for coordinating views and services (`controllers/`).
- **Navigation**: Centrally managed by a `Router` (singleton) using PySide6 signals (`navigation/router.py`).
- **Services**: Encapsulate hardware interaction and data acquisition (`services/`).
- **UI**: Design files created with Qt Designer (`ui/`).
- **Hardware Integration**:
  - **EMG**: Arduino-based (`emg_writer/` firmware, `emg_service.py`).
  - **Gas**: LabJack LJM (`gas_service.py`).
  - **Audio**: Sounddevice/Soundfile (`audio_service.py`).

## Tech Stack

- **Language**: Python 3.12+
- **GUI Framework**: PySide6 (Qt for Python)
- **Data Visualization**: Matplotlib
- **Numeric Processing**: NumPy
- **Communication**: PySerial (for Arduino/EMG), labjack-ljm (for Gas sensors)

## Development Workflow

### Building and Running

1. **Environment Setup**: Use Conda to create a Python 3.12 environment.
   ```bash
   conda create -n PEMSA python=3.12 -y
   conda activate PEMSA
   pip install -r requirements.txt
   ```
2. **Execution**: Run the application from the root directory.
   ```bash
   python main.py
   ```

### UI Modifications

- **Qt Designer**: Edit `.ui` files in the `ui/` directory.
- **Dynamic Loading**: Views load `.ui` files at runtime. If you add a new widget in Qt Designer, access it in the controller using `self.view.ui.findChild(WidgetType, "objectName")`.
- **BaseView**: All views should inherit from `BaseView` to ensure consistent header logos and layout handling.

### Coding Standards

- **Naming**: Follow PEP 8 (snake_case for functions/variables, PascalCase for classes).
- **Architecture**: Keep business logic in `controllers` or `services`. `views` should only handle UI setup and event forwarding.
- **Signals**: Use PySide6 `Signal` for inter-component communication (especially via the `router`).

## Directory Structure

- `controllers/`: Application logic and view management.
- `models/`: Data models.
- `services/`: Hardware abstraction and data capture services.
- `ui/`: `.ui` files (Qt Designer).
- `views/`: View classes (Python wrappers for UI).
- `navigation/`: Router and navigation logic.
- `resources/`: Images, icons, and QSS styles.
- `utils/`: Helper functions and background workers.
- `emg_writer/`: Arduino firmware for EMG sensing.
