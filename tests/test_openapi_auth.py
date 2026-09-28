"""The fork preserves upstream's per-camera OpenAPI authentication fix."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from debug_tools.bootstrap import _bootstrap_integration_modules

API = _bootstrap_integration_modules()["api"]


class DeviceAuthorizationTests(unittest.TestCase):
    def test_device_signature_and_client_fields_are_forwarded(self):
        device = {"snNum": "0000cam123456", "deviceSignature": "synthetic-token", "t": 123}
        client = SimpleNamespace(devices={"camera": device}, user_id=42)
        self.assertEqual(
            API.MeariApiClient._device_config_auth(client, "cam123456"),
            {"token": "synthetic-token", "clientid": "42", "t": "123"},
        )

    def test_unmatched_or_unsigned_camera_does_not_borrow_other_token(self):
        client = SimpleNamespace(
            devices={"camera": {"snNum": "0000cam123456", "deviceSignature": "synthetic-token"}},
            user_id=42,
        )
        self.assertEqual(API.MeariApiClient._device_config_auth(client, "other"), {})
        client.devices["camera"].pop("deviceSignature")
        self.assertEqual(API.MeariApiClient._device_config_auth(client, "cam123456"), {})


if __name__ == "__main__":
    unittest.main()
