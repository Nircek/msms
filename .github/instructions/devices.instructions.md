---
applyTo: "msms/connectivity/devices/**/*.py"
description: "Device driver registration and implementation pattern"
---

# Device Driver Pattern

## Philosophy
- Encapsulate hardware quirks inside each driver while exposing consistent, typed readings to the rest of the app.

## Required implementation
```python
@register_device(initials="XX", short_display_name="Device Name")
class MyDevice(DeviceBase):
    @classmethod
    def can_handle(cls, idn_parts: GpibIdnParts) -> bool:
        # Match against *IDN? response tuple (vendor, model, serial, version)
        pass

    def initialize(self) -> None:
        # Device setup commands (called once after connection)
        pass

    def update(self) -> dict[str, str]:
        # Return latest readings (called periodically)
        return {"column_name": self.query_resource("SCPI?")}
```

## Device discovery
- Auto-detects via `*IDN?` matching in `can_handle()`
- New devices auto-register when imported
- Device initials (`MM`, `LS`, `LI`) used for console logging prefixes

## Abstractions
- Only the `connectivity` module can interact with VISA
- Device-specific logic belongs exclusively in that device's file under `connectivity/devices/`
- Each reading returns `float` (valid) or `str` (error/warning message)
