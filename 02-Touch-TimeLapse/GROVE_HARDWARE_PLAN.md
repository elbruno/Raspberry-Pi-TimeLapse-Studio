# Grove Expansion Plan for Touch TimeLapse

This plan covers integration of:

- **Grove Dual Button** (start/stop trigger)
- **Grove WS2813 status light** using either:
  - RGB LED Stick (10 LEDs), or
  - RGB LED Ring (20 LEDs)

Target platform: **Raspberry Pi 4 + Grove Base Hat + 3.5" touchscreen**.

---

## 1) Hardware wiring baseline

## Recommended initial wiring (safe defaults)

- **Grove Dual Button** → Digital port exposing **BCM 5 + BCM 6**
- **Grove WS2813 Ring/Stick** → PWM port signal on **BCM 12**

Notes:

- Grove Base Hat is 3.3V logic; use Grove-native modules only.
- WS2813 module type (ring vs stick) is selected in config via `grove_light.pixel_count`:
  - Stick = 10
  - Ring = 20

---

## 2) UX behavior (target)

- **Button 1** toggles capture:
  - idle/stopped → start
  - capturing → stop
- **Button 2** reserved for future action (session mark / menu / shutdown)

- WS2813 status color map:
  - idle: blue
  - capturing: green
  - stopped: amber
  - error: red
  - optional white flash on each successful capture

---

## 3) Software rollout phases

### Phase A (implemented in this branch)

- Add optional hardware adapters:
  - `grove_dual_button.py`
  - `grove_status_light.py`
- Add config sections:
  - `grove_button`
  - `grove_light`
- Integrate into `timelapse_touch.py` and `capture_engine.py` with graceful no-hardware fallback.
- Add automated tests for config + adapters.

### Phase B (next)

- Add settings UI controls for Grove button/light toggles and pin selection.
- Add in-app diagnostics panel:
  - show detected pins/devices
  - button press test mode
  - LED color test mode

### Phase C (field hardening)

- Long-run stress tests (8h+ captures).
- Touchscreen + GPIO coexistence verification across boot/autostart.
- Improve error surfaces and recovery prompts in UI.

---

## 4) Validation checklist on Pi

1. Start app without hardware attached: app should run normally.
2. Attach dual button only: pressing button1 toggles start/stop.
3. Attach LED stick/ring only: state colors update and capture flash works.
4. Attach both: ensure no missed button events during capture.
5. Reboot and run via desktop shortcut/autostart.

---

## 5) Config template

```yaml
grove_button:
  enabled: true
  pin_button1: 5
  pin_button2: 6
  debounce_ms: 250
  start_stop_button: button1

grove_light:
  enabled: true
  pin: 12
  pixel_count: 10  # use 20 for ring
  brightness: 48
  capture_flash: true
```

---

## 6) Ring vs Stick decision guide

- **Stick (10)**: compact, lower power, good for simple status.
- **Ring (20)**: better visibility, clearer animation at a distance.

Recommendation: start with **Stick (10)** for lower load, then test Ring (20) and compare visibility in your real shooting setup.
