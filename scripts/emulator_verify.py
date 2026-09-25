"""Repeatable API 36 emulator-only checks. Never runs against a physical phone.

Build app + androidTest APKs first. Uses synthetic SMS; the emulator messaging
provider may retain them, although SmishGuard must not. No research metrics.
"""
import argparse
import io
import json
from pathlib import Path
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = "ph.smishguard"
PACKAGE = NAMESPACE
RUNNER = PACKAGE + ".test/ph.smishguard.SoftwareTestRunner"


def main():
    global PACKAGE, RUNNER
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", default="emulator-5554")
    parser.add_argument("--variant", choices=["debug", "development"], default="debug")
    parser.add_argument("--diagnostics", action="store_true", help="Save test-only failure screenshots/state under ignored deliverables")
    parser.add_argument("--output", type=Path, help="Optional separate sanitized verification record")
    args = parser.parse_args()
    PACKAGE = NAMESPACE + (".dev" if args.variant == "development" else "")
    RUNNER = PACKAGE + ".test/" + NAMESPACE + ".SoftwareTestRunner"
    adb = ["adb", "-s", args.serial]
    def command(*parts, timeout=60):
        return subprocess.run(adb + list(parts), check=True, capture_output=True, timeout=timeout).stdout
    if command("shell", "getprop", "ro.kernel.qemu").strip() != b"1":
        raise SystemExit("Only a verified emulator is supported; no physical-device state will be changed.")
    if command("shell", "getprop", "sys.boot_completed").strip() != b"1":
        raise SystemExit("Wait for emulator boot completion.")
    if b"Application Not Responding" in command("shell", "dumpsys", "window"):
        raise SystemExit("Resolve the emulator's system ANR dialog before verification; app focus is required.")
    prior_airplane = command("shell", "settings", "get", "global", "airplane_mode_on").strip() == b"1"
    prior_wifi = command("shell", "settings", "get", "global", "wifi_on").strip() == b"1"
    prior_font = command("shell", "settings", "get", "system", "font_scale").decode().strip()
    results = {"variant": args.variant, "api": command("shell", "getprop", "ro.build.version.sdk").decode().strip()}
    target = ROOT / ("docs/development-emulator-results.json" if args.variant == "development" else "docs/emulator-results.json")
    if args.output is not None:
        target = args.output
    results["status"] = "incomplete"
    def run_test(label, classes, extra=()):
        diagnostics = ("-e", "diagnostics", "true") if args.diagnostics else ()
        output = command("shell", "am", "instrument", "-w", "-e", "class", classes, *extra, *diagnostics, RUNNER, timeout=180).decode(errors="replace")
        results[label] = output.strip()
        if "FAILURES!!!" in output or "OK (" not in output or "INSTRUMENTATION_FAILED" in output:
            if args.diagnostics:
                destination = ROOT / "deliverables/api36-reliability" / ("specialized-" + str(time.time_ns()))
                destination.mkdir(parents=True, exist_ok=True)
                (destination / "instrumentation.log").write_text(output, encoding="utf-8")
                for name in ("accessibility", "result-flow"):
                    for suffix in ("txt", "png"):
                        capture = subprocess.run(adb + ["exec-out", "run-as", PACKAGE, "cat", f"files/reliability/{name}.{suffix}"], capture_output=True, timeout=30)
                        if capture.returncode == 0:
                            (destination / f"{name}.{suffix}").write_bytes(capture.stdout)
            raise RuntimeError(label + " failed:\n" + output)
        results[label] = output.strip()
        print(label + ": passed", flush=True)
    try:
        command("install", "-r", str(ROOT / f"android/app/build/outputs/apk/{args.variant}/app-{args.variant}.apk"))
        command("install", "-r", str(ROOT / f"android/app/build/outputs/apk/androidTest/{args.variant}/app-{args.variant}-androidTest.apk"))
        command("shell", "pm", "clear", PACKAGE)
        command("shell", "cmd", "uimode", "night", "no")
        run_test("ui_lifecycle_decoding", ",".join(NAMESPACE + "." + c for c in (["FlowsTest", "PrivacyLifecycleTest", "SmsDecodingTest", "ModelInitializationTest"] + (["DevelopmentFlowTest", "CompactResultTest", "AssessabilityModelTest"] if args.variant == "development" else []))))
        run_test("notification_denied", NAMESPACE + ".NotificationBehaviorTest#runtimeDenialSuppressesWarning", ("-e", "denied", "true"))
        command("shell", "cmd", "connectivity", "airplane-mode", "enable")
        command("shell", "svc", "wifi", "disable")
        run_test("offline_sklearn_exports", NAMESPACE + ".OfflineModelTest" + ("," + NAMESPACE + ".SuppliedModelTest" if args.variant == "development" else ""), ("-e", "offline", "true"))
        command("shell", "cmd", "connectivity", "airplane-mode", "disable")
        command("shell", "pm", "grant", PACKAGE, "android.permission.RECEIVE_SMS")
        command("shell", "pm", "grant", PACKAGE, "android.permission.POST_NOTIFICATIONS")
        # SDK console supports GSM text and raw PDU injection; never send via carrier.
        process = subprocess.Popen(adb + ["shell", "am", "instrument", "-w", "-e", "class", NAMESPACE + ".ModemSmsTest", "-e", "modem", "true", RUNNER], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        def ready(stage):
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                probe = subprocess.run(adb + ["shell", "run-as", PACKAGE, "test", "-f", "files/sms-test-signals/" + stage], capture_output=True, timeout=10)
                if probe.returncode == 0:
                    return
                if process.poll() is not None:
                    break
                time.sleep(.3)
            detail = process.communicate(timeout=5)[0].decode(errors="replace") if process.poll() is not None else "Instrumentation still running"
            raise RuntimeError("SMS test readiness failed: " + stage + "\n" + detail)
        def inject(*parts):
            output = command("emu", "sms", *parts)
            if b"KO:" in output or b"OK" not in output:
                raise RuntimeError("Emulator rejected SMS injection")
        try:
            ready("single")
            inject("send", "5550100", "SGTEST single kumusta")
            ready("multipart")
            # Let the supported text command construct multipart PDUs. The Android
            # test also requires multiple PDUs, so a single oversized SMS cannot pass.
            inject("send", "5550100", "SGTEST multipart " + "kumusta po ñ " * 20)
            ready("disabled")
            inject("send", "5550100", "SGTEST consent off")
            output = process.communicate(timeout=45)[0].decode(errors="replace")
            if "OK (1 test)" not in output or "FAILURES!!!" in output:
                raise RuntimeError(output)
            results["modem_sms"] = output.strip()
            print("modem_sms: passed", flush=True)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
        run_test("notification_granted_and_channel_blocked", NAMESPACE + ".NotificationBehaviorTest#privateNotificationConstructionAndBlockedChannel", ("-e", "granted", "true"))
        command("shell", "settings", "put", "system", "font_scale", "2.0")
        run_test("accessibility_large_text", NAMESPACE + ".AccessibilityTest", ("-e", "largeFont", "true"))
        command("shell", "settings", "put", "system", "font_scale", prior_font if prior_font != "null" else "1.0")
        # Inspect SmishGuard's private files, not Android's separate SMS provider.
        archive = command("exec-out", "run-as", PACKAGE, "tar", "cf", "-", ".")
        inspected = 0
        with tarfile.open(fileobj=io.BytesIO(archive)) as files:
            for entry in files:
                if not entry.isfile():
                    continue
                data = files.extractfile(entry).read()
                for marker in [b"SGTEST", b"SYNTHETIC_PRIVATE_SESSION_MARKER", b"Synthetic Taglish share:", b"Synthetic clipboard:"]:
                    if marker in data:
                        raise AssertionError("Raw fixture persisted in app file: " + entry.name)
                inspected += 1
        results["private_storage"] = {"files_inspected": inspected, "raw_fixture_markers_found": 0}
        results["status"] = "passed"
        print("private_storage: passed", flush=True)
    finally:
        results["scope"] = "Emulator software checks only; not research accuracy or physical-device results"
        target.write_text(json.dumps(results, indent=2), encoding="utf-8")
        command("shell", "settings", "put", "system", "font_scale", prior_font if prior_font != "null" else "1.0")
        command("shell", "cmd", "connectivity", "airplane-mode", "enable" if prior_airplane else "disable")
        command("shell", "svc", "wifi", "enable" if prior_wifi else "disable")
        # A failing test must not leave granted permissions/preferences behind for
        # the ordinary instrumentation suite's denied-permission precondition.
        command("shell", "pm", "clear", PACKAGE)
    results["scope"] = "Emulator software checks only; supplied-model compatibility and synthetic fixtures are not research accuracy or physical-device results"
    target.write_text(json.dumps(results, indent=2), encoding="utf-8")
    # Leave the delivered app clean, with no test consent or blocked test channel.
    command("shell", "am", "start", "-n", PACKAGE + "/" + NAMESPACE + ".MainActivity")
    print("Emulator verification complete; evidence: " + str(target), flush=True)


if __name__ == "__main__":
    main()
