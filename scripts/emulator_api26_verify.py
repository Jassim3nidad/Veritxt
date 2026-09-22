"""Focused API 26 emulator checks; synthetic inputs, no research performance."""
import json
from pathlib import Path
import subprocess
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ADB = ["adb", "-s", "emulator-5556"]
PACKAGE = "ph.smishguard.dev"


def command(*args):
    return subprocess.run(ADB + list(args), check=True, capture_output=True,
                          timeout=180).stdout.decode(errors="replace").strip()


def main():
    assert command("shell", "getprop", "ro.kernel.qemu") == "1"
    assert command("shell", "getprop", "ro.build.version.sdk") == "26"
    assert command("shell", "getprop", "sys.boot_completed") == "1"
    original = {key: command("shell", "settings", "get", scope, key)
                for scope, key in [("global", "airplane_mode_on"), ("global", "wifi_on"),
                                   ("system", "font_scale")]}
    original["wifi_enabled"] = "Wi-Fi is enabled" in command("shell", "dumpsys", "wifi")
    results = {"api": 26, "variant": "development", "status": "incomplete"}
    def radio_setting(action, enabled):
        # This API 26 image denies svc wifi/data to shell; use ordinary Settings UI.
        command("shell", "am", "start", "-a", "android.settings." + action)
        command("shell", "uiautomator", "dump", "/sdcard/smishguard-settings.xml")
        tree = ET.fromstring(command("shell", "cat", "/sdcard/smishguard-settings.xml"))
        if action == "AIRPLANE_MODE_SETTINGS":
            parents = {child: parent for parent in tree.iter() for child in parent}
            tree = next(n for n in tree.iter("node") if n.get("text") == "Airplane mode")
            while not any(n.get("class") == "android.widget.Switch" for n in tree.iter("node")):
                tree = parents[tree]
        switches = [n for n in tree.iter("node") if n.get("class") == "android.widget.Switch"
                    and n.get("checkable") == "true" and n.get("resource-id", "").endswith(":id/switch_widget")]
        assert len(switches) == 1, "Expected one standard Settings switch"
        node = switches[0]
        if (node.get("checked") == "true") != enabled:
            left, top, right, bottom = map(int, re.findall(r"\d+", node.get("bounds")))
            command("shell", "input", "tap", str((left + right)//2), str((top + bottom)//2))
    try:
        command("install", "-r", str(ROOT / "android/app/build/outputs/apk/development/app-development.apk"))
        command("install", "-r", str(ROOT / "android/app/build/outputs/apk/androidTest/development/app-development-androidTest.apk"))
        command("shell", "pm", "clear", PACKAGE)
        radio_setting("AIRPLANE_MODE_SETTINGS", True)
        radio_setting("WIFI_SETTINGS", False)
        assert command("shell", "settings", "get", "global", "airplane_mode_on") == "1"
        # API 26 can retain wifi_on=3 (disabled by airplane mode); inspect service state.
        assert "Wi-Fi is disabled" in command("shell", "dumpsys", "wifi")
        results["offline_setup"] = "Airplane mode on; Wi-Fi service disabled via standard Settings"
        for label, classes, key in [
            ("offline_parity_and_invalid_models", "SuppliedModelTest", "offline"),
            ("development_flow_and_accessibility", "DevelopmentFlowTest,ph.smishguard.AccessibilityTest", "largeFont"),
        ]:
            if key == "largeFont":
                command("shell", "settings", "put", "system", "font_scale", "2.0")
            output = command("shell", "am", "instrument", "-w", "-e", "class",
                             "ph.smishguard." + classes, "-e", key, "true",
                             PACKAGE + ".test/ph.smishguard.SoftwareTestRunner")
            results[label] = output
            assert "OK (2 tests)" in output and "FAILURES!!!" not in output, output
            print(label + ": passed", flush=True)
        results["status"] = "passed"
    finally:
        command("shell", "settings", "put", "system", "font_scale", original["font_scale"] if original["font_scale"] != "null" else "1.0")
        radio_setting("AIRPLANE_MODE_SETTINGS", original["airplane_mode_on"] == "1")
        radio_setting("WIFI_SETTINGS", original["wifi_enabled"])
        results["scope"] = "Focused API 26 emulator checks only; not SMS delivery, physical-device or research results. Offline setup and test outcomes recorded separately."
        (ROOT / "docs/api26-results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    command("shell", "pm", "clear", PACKAGE)


if __name__ == "__main__":
    main()
