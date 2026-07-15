# Gesture-Operated Steering Controller (GestOSC)

Mime a steering wheel with your hands to control games, apps and anything else that is compatible with an XBox 360 controller.

## How it works

Point a camera towards your two hands and mime a steering wheel. Rotating your hands just as you would when driving to turn.

This tool uses the left joystick to turn; ensure the keybind is bound for turning in whichever game you are using. It currently auto-accelerates using the A button (future updates may evolve this into controlled acceleration).

## Set-up

### Windows
Create a virtual environment and install the Python dependencies from the `requirements.txt` file.
```ps1
python3 -m venv venv
.\venv\Scripts\Activate.ps1
$env:VGAMEPAD_SKIP_VIGEMBUS_INSTALL="true" # Prevents using old ViGEmBus installer
pip3 install -r requirements.txt
```

Download the `hand_landmarker.task` file from Google's APIs at [https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task). Place it in the same directory as `gesture-handler.py`.
```ps1
curl -O "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
```

Run `python3 gesture-handler.py` while in the virtual environment to load the custom controller. Make sure to reload your desired apps after enabling this controller since, just as with regular XBox controllers, some apps (especially through Steam) only register controller inputs if they are connected before opening the app.

### Linux
Same as for [Windows](#windows), except that `.\venv\bin\activate` should be run instead of `.\venv\Scripts\Activate.ps1` and `$env:VGAMEPAD_SKIP_VIGEMBUS_INSTALL="true"` can be omitted.

## Build executable
Follow the [set-up steps](#set-up), then run the following command in the Python virtual environment
```bash
python3 -m nuitka gesture-handler.py
```

See the build log for the executable's final location.

## Note

GestOSC is based on a project I took part in for the CuHacking Hackathon. The project tracked points on a paper plate which acted as a physical steering wheel.

## Licensing

As required by section 3.2 of the [Mozilla Public License 2.0 (MPL 2.0)](https://www.mozilla.org/en-US/MPL/2.0/#distribution-of-executable-form) used by the `certifi` python package, you can find the source code for `certifi` at [https://github.com/certifi/python-certifi](https://github.com/certifi/python-certifi).
