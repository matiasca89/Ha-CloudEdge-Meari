"""Offline regression coverage for Arenti IoT sensor wire units."""

from __future__ import annotations

import importlib
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "cloudplus"


def sensor_module():
    """Load the real sensor/entity modules without a Home Assistant install."""
    stubs = {}
    paths = {
        "custom_components": ROOT.parent,
        "custom_components.cloudplus": ROOT,
        "homeassistant": None,
        "homeassistant.components": None,
        "homeassistant.config_entries": None,
        "homeassistant.core": None,
        "homeassistant.helpers": None,
        "homeassistant.helpers.entity_platform": None,
    }
    for name, path in paths.items():
        module = types.ModuleType(name)
        module.__path__ = [str(path)] if path else []
        stubs[name] = module
    for name in ("homeassistant.components.sensor", "homeassistant.const",
                 "homeassistant.helpers.entity"):
        stubs[name] = types.ModuleType(name)
    components = stubs["homeassistant.components.sensor"]
    components.SensorDeviceClass = SimpleNamespace(TEMPERATURE="temperature", HUMIDITY="humidity", BATTERY="battery")
    components.SensorEntity = type("SensorEntity", (), {})
    components.SensorStateClass = SimpleNamespace(MEASUREMENT="measurement")
    stubs["homeassistant.const"].PERCENTAGE = "%"
    stubs["homeassistant.const"].UnitOfTemperature = SimpleNamespace(CELSIUS="°C")
    stubs["homeassistant.config_entries"].ConfigEntry = type("ConfigEntry", (), {})
    stubs["homeassistant.core"].HomeAssistant = type("HomeAssistant", (), {})
    stubs["homeassistant.core"].callback = lambda fn: fn
    stubs["homeassistant.helpers.entity_platform"].AddEntitiesCallback = object
    stubs["homeassistant.helpers.entity"].Entity = type("Entity", (), {})
    stubs["custom_components.cloudplus.coordinator"] = types.ModuleType(
        "custom_components.cloudplus.coordinator"
    )
    vars(stubs["custom_components.cloudplus.coordinator"])["CloudEdgeMeariCoordinator"] = object
    stubs["custom_components.cloudplus.const"] = types.ModuleType(
        "custom_components.cloudplus.const"
    )
    vars(stubs["custom_components.cloudplus.const"])["DOMAIN"] = "cloudplus"
    with patch.dict(sys.modules, stubs):
        # Do not reuse modules imported with another test's stub classes.
        for name in ("custom_components.cloudplus.sensor", "custom_components.cloudplus.entity"):
            sys.modules.pop(name, None)
        try:
            yield importlib.import_module("custom_components.cloudplus.sensor")
        finally:
            for name in ("custom_components.cloudplus.sensor", "custom_components.cloudplus.entity",
                         "custom_components.cloudplus.meari_commands"):
                sys.modules.pop(name, None)


class IotSensorUnitTests(unittest.TestCase):
    def test_temperature_millidegrees_are_celsius(self):
        for module in sensor_module():
            spec = next(s for s in module.IOT_SENSORS if s.name == "Temperature")
            coordinator = SimpleNamespace(device_uuid="test", device_name="test",
                                          device_model="test", available=True,
                                          get_iot_value=lambda code: "21600")
            sensor = module.CloudEdgeMeariIotSensor(coordinator, None, spec)
            self.assertEqual(sensor.native_value, 21.6)
            self.assertEqual(sensor._attr_native_unit_of_measurement, "°C")

    def test_humidity_stays_whole_percent(self):
        for module in sensor_module():
            spec = next(s for s in module.IOT_SENSORS if s.name == "Humidity")
            coordinator = SimpleNamespace(device_uuid="test", device_name="test",
                                          device_model="test", available=True,
                                          get_iot_value=lambda code: "69")
            sensor = module.CloudEdgeMeariIotSensor(coordinator, None, spec)
            self.assertEqual(sensor.native_value, 69.0)

    def test_invalid_humidity_is_unavailable(self):
        for module in sensor_module():
            spec = next(s for s in module.IOT_SENSORS if s.name == "Humidity")
            coordinator = SimpleNamespace(device_uuid="test", device_name="test",
                                          device_model="test", available=True,
                                          get_iot_value=lambda code: "255")
            sensor = module.CloudEdgeMeariIotSensor(coordinator, None, spec)
            self.assertIsNone(sensor.native_value)
            self.assertFalse(sensor.available)

    def test_invalid_temperature_is_unavailable(self):
        for module in sensor_module():
            spec = next(s for s in module.IOT_SENSORS if s.name == "Temperature")
            coordinator = SimpleNamespace(device_uuid="test", device_name="test",
                                          device_model="test", available=True,
                                          get_iot_value=lambda code: "255000")
            sensor = module.CloudEdgeMeariIotSensor(coordinator, None, spec)
            self.assertIsNone(sensor.native_value)
            self.assertFalse(sensor.available)


if __name__ == "__main__":
    unittest.main()
