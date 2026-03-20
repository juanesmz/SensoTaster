# SensoTaster

Plataforma de evaluación sensorial asistida por instrumentación. Integra sensores EMG, de gas, micrófono y cámara para capturar y analizar las respuestas sensoriales de panelistas durante experimentos de degustación.

## Requisitos previos

| Herramienta | Versión mínima |
|-------------|---------------|
| Python      | 3.12          |
| Conda       | 24.x          |

## Configuración del entorno

### 1. Crear el entorno de Conda

```bash
conda create -n PEMSA python=3.12 -y
```

### 2. Activar el entorno

```bash
conda activate PEMSA
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Ejecución

Con el entorno **PEMSA** activado, ejecuta la aplicación desde la raíz del proyecto:

```bash
python main.py
```

## Estructura del proyecto

```
SensoTaster/
├── main.py                  # Punto de entrada de la aplicación
├── config.py                # Configuración global
├── requirements.txt         # Dependencias con versiones exactas
├── controllers/             # Lógica de control (MVC)
│   ├── app_controller.py
│   ├── login_controller.py
│   ├── main_menu_controller.py
│   ├── analysis_controller.py
│   ├── visualization_controller.py
│   └── experiment/          # Controladores por tipo de sensor
├── views/                   # Vistas Qt (MVC)
│   ├── base_view.py
│   └── experiment/          # Vistas de cada sensor
├── models/                  # Modelos de datos
├── ui/                      # Archivos .ui de Qt Designer
├── services/                # Servicios (audio, cámara, EMG, gas, almacenamiento)
├── navigation/              # Sistema de navegación/rutas
├── utils/                   # Utilidades y workers
├── resources/               # Imágenes, estilos e íconos
├── emg_writer/              # Firmware Arduino para el sensor EMG
└── tests/                   # Tests unitarios
```

## Tecnologías

- **PySide6** — Interfaz gráfica (Qt for Python)
- **Matplotlib** — Gráficas en tiempo real
- **NumPy** — Procesamiento numérico de señales
- **PySerial** — Comunicación serial con sensores
