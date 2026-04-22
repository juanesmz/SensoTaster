import os
import numpy as np
import csv
from PySide6.QtCore import QObject

class EMGController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view

    def load_data(self, directory):
        """
        Loads EMG data from CSV files in the 'EMG' subdirectory and updates the chart.
        """
        emg_path = os.path.join(directory, "EMG")
        if not os.path.isdir(emg_path):
            return

        # Get up to 6 CSV files
        csv_files = sorted([f for f in os.listdir(emg_path) if f.lower().endswith(".csv")])
        
        all_channels_data = []
        
        # The EMGChartWidget expects 6 channels
        for i in range(6):
            if i < len(csv_files):
                file_path = os.path.join(emg_path, csv_files[i])
                data = self._read_emg_column(file_path)
                if len(data) > 0:
                    self.view.curves[i].setData(data)
                    self.view.curves[i].show()
                else:
                    self.view.curves[i].hide()
            else:
                self.view.curves[i].hide()

        self.view.plot_widget.autoRange()

    def _read_emg_column(self, file_path):
        """Helper to read the EMG_Value column from a CSV file."""
        values = []
        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as f:
                # Peek at the first line to see if it's empty or has headers
                reader = csv.DictReader(f)
                for row in reader:
                    if 'EMG_Value' in row and row['EMG_Value']:
                        try:
                            values.append(float(row['EMG_Value']))
                        except ValueError:
                            pass
        except Exception as e:
            print(f"Error reading CSV {file_path}: {e}")
            
        return np.array(values) if values else np.zeros(0)
