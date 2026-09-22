# Physical device testing after official resolution

Target: Xiaomi M2103K19G, Android 13 / MIUI 14.0.6, user-reported. Current state: `secure_frp_mode=1`, `user_setup_complete=1`, `device_provisioned=1`; restart did not resolve it. Xiaomi support is being contacted. This is blocked by device state, not an established APK defect. No new installation attempt was made in this session. Support correspondence remains private.

Start only after Xiaomi officially resolves the restriction and ordinary authorized installation is available. Never change protected settings, bypass FRP, unlock/flash, remove accounts or factory-reset for this checklist. Preserve existing app data until owner authorization for uninstall/reinstall. Record actual tester/device/build, APK hash, timestamp and a private evidence reference after each observation, not in advance.

| Test | Expected observation | Status |
|---|---|---|
| Downloaded APK SHA-256 | Matches the exact local package checksum; mismatch is investigated before install | Pending |
| Ordinary installation | Package manager reports success; capture only narrow error if unsuccessful | Pending |
| First launch | Experimental warning and model status visible; no crash | Pending |
| Permission denial / permanent denial | Paste/share remains usable; settings accurately reflect access | Pending |
| Permission grant where allowed | Actual restricted-SMS/notification availability recorded; no bypass | Pending |
| Paste and share | Fictional English/Filipino/Taglish, empty and long input handled as documented | Pending |
| Real single-part SMS | Safe team-authored message reaches normal messaging app; experimental detector emits no automatic warning | Pending |
| Real multipart SMS / dual SIM if available | Record carrier delivery and assembly without real private content | Pending |
| Lock-screen notifications | No experimental automatic-model warning expected; approved future warning behavior requires separate build and authorization | Pending |
| Background, battery saver, reboot, force-stop/reopen | Record vendor/OS behavior, not detector accuracy | Pending |
| Airplane mode plus Wi-Fi off | Manual scanning still works | Pending |
| Rotation/process recreation | Session text cleared; no raw text restoration or logs | Pending |
| Accessibility | TalkBack labels, focus, font scale, landscape and controls reviewed | Pending |
| Latency/memory | Record device conditions, warm/cold runs, N and method; no emulator substitution | Pending |
| Uninstall/reinstall | Only after owner approves data removal; first-launch/reset behavior verified | Pending |

Keep every unperformed row Pending. A failing install does not mark inference or other unexecuted tests Failed. Treat unexpected security or installer errors as a reason to stop and document, not to retry repeatedly.
