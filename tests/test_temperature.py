import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


spec = importlib.util.spec_from_file_location(
    'monitor', Path(__file__).resolve().parents[1] / 'src' / 'monitor.py')
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class TemperatureTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def sensor(self, name, files):
        hw = self.root / 'hwmon0'
        hw.mkdir()
        (hw / 'name').write_text(name)
        for filename, content in files.items():
            (hw / filename).write_text(content)

    def test_amd_tctl(self):
        self.sensor('k10temp', {'temp1_label': 'Tctl', 'temp1_input': '42625'})
        self.assertEqual(monitor.read_cpu_temperature(self.root), 42.625)

    def test_amd_prefers_die_temperature_over_control_temperature(self):
        self.sensor('k10temp', {'temp1_label': 'Tctl', 'temp1_input': '65000',
                                'temp2_label': 'Tdie', 'temp2_input': '55000'})
        self.assertEqual(monitor.read_cpu_temperature(self.root), 55)

    def test_intel_prefers_package_temperature(self):
        self.sensor('coretemp', {'temp1_label': 'Core 0', 'temp1_input': '40000',
                                 'temp2_label': 'Package id 0', 'temp2_input': '45000'})
        self.assertEqual(monitor.read_cpu_temperature(self.root), 45)

    def test_invalid_reading_falls_back_to_next_channel(self):
        self.sensor('k10temp', {'temp1_label': 'Tctl', 'temp1_input': '45000',
                                'temp2_label': 'Tdie', 'temp2_input': 'invalid'})
        self.assertEqual(monitor.read_cpu_temperature(self.root), 45)

    def test_gpu_sensor_is_not_used_as_cpu_temperature(self):
        self.sensor('amdgpu', {'temp1_input': '39000'})
        self.assertIsNone(monitor.read_cpu_temperature(self.root))


if __name__ == '__main__':
    unittest.main()
