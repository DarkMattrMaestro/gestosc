# Gesture-Operated Steering Controller (GestOSC)

Mime a steering wheel with your hands to control games, apps and anything else that is compatible with an XBox 360 controller.

## How it works

Point a camera towards your two hands and mime a steering wheel. Rotating your hands just as you would when driving to turn.

This tool uses the left joystick to turn; ensure the keybind is bound for turning in whichever game you are using. It currently auto-accelerates using the A button (future updates may evolve this into controlled acceleration).

## Set-up

Load the virtual environment and install the Python dependencies from the `requirements.txt` file.

Download the `hand_landmarker.task` file from Google's APIs at [https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task). Place it in the same directory as `gesture-handler.py`.

Run `python3 gesture-handler.py` while in the virtual environment to load the custom controller. Make sure to reload your desired apps after enabling this controller since, just as with regular XBox controllers, some apps (especially through Steam) only register controller inputs if they are connected before opening the app.

## Note

GestOSC is based on a project I took part in for the CuHacking Hackathon. The project tracked points on a paper plate which acted as a physical steering wheel.