# Gesture-Operated Steering Controller (GestOSC)

# Project info
# nuitka-project: --product-name=GestOSC
# nuitka-project: --file-version=0.1.0
# nuitka-project: --file-description=GestOSC

# Base project config
# nuitka-project: --msvc=latest
# nuitka-project: --follow-imports
# nuitka-project: --mode=standalone
# nuitka-project: --mode=onefile
# nuitka-project: --onefile-windows-splash-screen-image={MAIN_DIRECTORY}/splash-screen.png
# nuitka-project: --output-dir={MAIN_DIRECTORY}/build

# Disable console
# nuitka-project-if: {OS} == "Windows":
#   nuitka-project: --windows-console-mode=hide

# Data files
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/hand_landmarker.task=hand_landmarker.task
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/vigembus_installer/ViGEmBus_1.22.0_x64_x86_arm64.exe=vigembus_installer/ViGEmBus_1.22.0_x64_x86_arm64.exe

# Package configs
# nuitka-project: --user-package-configuration-file={MAIN_DIRECTORY}/nuitka-package.config.yml

# TKInter fix
# nuitka-project: --enable-plugin=tk-inter


# nuitka-project: --output-filename=GestOSC

from threading import Thread
import queue
import tkinter as tk
from tkinter.ttk import Label, Progressbar

import cv2
import time
import math
from os import path, environ, unlink, link
from tempfile import gettempdir
from tkinter import LEFT, NW, TOP, messagebox, Tk, Canvas

import mediapipe as mp
import numpy as np


class SplashScreen:
    def unload_splash():
        if "NUITKA_ONEFILE_PARENT" in environ:
            splash_filename = path.join(
                gettempdir(),
                "onefile_%d_splash_feedback.tmp" % int(environ["NUITKA_ONEFILE_PARENT"]),
            )

            if path.exists(splash_filename):
                unlink(splash_filename)
    
    def load_splash():
        if "NUITKA_ONEFILE_PARENT" in environ:
            splash_filename = path.join(
                gettempdir(),
                "onefile_%d_splash_feedback.tmp" % int(environ["NUITKA_ONEFILE_PARENT"]),
            )

            if path.exists(splash_filename):
                link(splash_filename)

SplashScreen.unload_splash()

class ViGEmBusInstaller:
    """Installer setup for ViGEmBus on Windows if it is not present."""
    
    VIGEMBUS_VERSION = "1.22.0"
    
    def install():
        import platform
        if platform.system() != 'Windows': return 0
        
        from pathlib import Path
        import subprocess
        
        installer_path = Path(__file__).parent.absolute() / "vigembus_installer" / ("ViGEmBus_" + ViGEmBusInstaller.VIGEMBUS_VERSION + "_x64_x86_arm64.exe")
        
        if messagebox.askokcancel(title="GestOSC - ViGEmBus Installation Required", message=f"GestOSC depends on ViGEmBus for gamepad emulation on Windows.\nWould you like to use the bundled installer (version {ViGEmBusInstaller.VIGEMBUS_VERSION})?"):
            subprocess.call([installer_path], shell=True)
        else:
            return -1
    
        return 0

# Ensure ViGEmBus is present; crash gracefully if not
try:
    import vgamepad
except Exception as e:
    if ViGEmBusInstaller.install() != 0: exit(0)
    try:
        import vgamepad
    except:
        messagebox.showerror(title="GestOSC - ViGEmBus Not Found", message="ViGEmBus could not be found!\nSee https://docs.nefarius.at/projects/ViGEm/How-to-Install/#troubleshooting for installation troubleshooting")
        exit(0)

class ErrorLogging:
    run_on_exit = lambda : None


start_time = int(time.time() * 1000)

print("Loading hand model and options...")
model_path = path.join(path.dirname(__file__), "hand_landmarker.task")

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode

class VizUtils:
    WINDOW_NAME = "GestOSC - Hand Tracking"
    
    show_visuals = True
    
    buffered_frame = None

    MARGIN = 10  # pixels
    FONT_SIZE = 1
    FONT_THICKNESS = 1
    HANDEDNESS_TEXT_COLOR = (88, 205, 54) # vibrant green
    
    mp_hands = mp.tasks.vision.HandLandmarksConnections
    mp_drawing = mp.tasks.vision.drawing_utils
    mp_drawing_styles = mp.tasks.vision.drawing_styles
    
    def draw_landmarks_on_image(rgb_image, detection_result):
        hand_landmarks_list = detection_result.hand_landmarks
        handedness_list = detection_result.handedness
        annotated_image = np.copy(rgb_image)

        # Loop through the detected hands to visualize.
        for idx in range(len(hand_landmarks_list)):
            hand_landmarks = hand_landmarks_list[idx]
            handedness = handedness_list[idx]

            # Draw the hand landmarks.
            VizUtils.mp_drawing.draw_landmarks(
                annotated_image,
                hand_landmarks,
                VizUtils.mp_hands.HAND_CONNECTIONS,
                VizUtils.mp_drawing_styles.get_default_hand_landmarks_style(),
                VizUtils.mp_drawing_styles.get_default_hand_connections_style())

            # Get the top left corner of the detected hand's bounding box.
            height, width, _ = annotated_image.shape
            x_coordinates = [landmark.x for landmark in hand_landmarks]
            y_coordinates = [landmark.y for landmark in hand_landmarks]
            text_x = int(min(x_coordinates) * width)
            text_y = int(min(y_coordinates) * height) - VizUtils.MARGIN

            # Draw handedness (left or right hand) on the image.
            cv2.putText(annotated_image, f"{handedness[0].category_name}",
                        (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                        VizUtils.FONT_SIZE, VizUtils.HANDEDNESS_TEXT_COLOR, VizUtils.FONT_THICKNESS, cv2.LINE_AA)

        return annotated_image

class SteeringWheel:
    gamepad: vgamepad.VX360Gamepad = vgamepad.VX360Gamepad()
    
    pos = {
        "Right": {
            "sx": None,
            "sy": None
        },
        "Left": {
            "sx": None,
            "sy": None
        }
    }
    
    def update_controller():
        for handedness in ["Left", "Right"]:
            for axis in ["sx", "sy"]:
                if SteeringWheel.pos[handedness][axis] is None: return
        
        x_diff = SteeringWheel.pos["Right"]["sx"] - SteeringWheel.pos["Left"]["sx"]
        y_diff = SteeringWheel.pos["Right"]["sy"] - SteeringWheel.pos["Left"]["sy"]
        z_diff = math.sqrt(x_diff**2 + y_diff**2)
        
        steering_value = max(min(2*(y_diff/z_diff if z_diff != 0 else 0), 1), -1)
        
        SteeringWheel.gamepad.left_joystick_float(
            x_value_float=steering_value, # -1 = left, +1 = right
            y_value_float=0
        )
        
        SteeringWheel.gamepad.press_button(button=vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_A) # Auto accelerate
        
        SteeringWheel.gamepad.update()

# Create a hand landmarker instance with the live stream mode:
def process_landmarker_res(result: HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    hand_landmarks_list = result.hand_landmarks
    handedness_list = result.handedness

    # Update hand coordinate data
    for idx in range(len(hand_landmarks_list)):
        hand_landmarks = hand_landmarks_list[idx]
        handedness = handedness_list[idx]
        
        x = y = n = 0
        for i in [0, 1, 5, 9, 13, 17]:
            n += 1
            x += hand_landmarks[i].x
            y += hand_landmarks[i].y
        
        if n == 0: continue
        
        x_avg = x / n
        y_avg = y / n
        
        SteeringWheel.pos[handedness[0].category_name]["sx"] = x_avg
        SteeringWheel.pos[handedness[0].category_name]["sy"] = y_avg
    
    # Update the controller if position data may have changed
    if len(hand_landmarks_list) > 0: SteeringWheel.update_controller()
    
    # Update visuals
    if VizUtils.show_visuals:
        annotated_image = VizUtils.draw_landmarks_on_image(output_image.numpy_view(), result)
        VizUtils.buffered_frame = brg_frame = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

#Camera settings
class Camera:
    camera = None
    
    def init_camera():
        print("Setting up camera...")
        width=640
        height=480
        Camera.camera = cv2.VideoCapture(0)
        if not Camera.camera.isOpened():
            ErrorLogging.run_on_exit = lambda : messagebox.showerror(title="GestOSC - No Camera Connected", message="There is no camera connected!\nTry connecting/reconnecting a camera.")
            return -1
        
        Camera.camera.set(cv2.CAP_PROP_FRAME_WIDTH,width)
        Camera.camera.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
        
        return 0
    
    def measurement_loop(landmarker):
        print("Beginning measurement")
        cv2.namedWindow(VizUtils.WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
        while True:
            key = cv2.waitKey(1)
            
            ret, frame = Camera.camera.read()
            if not ret:
                ErrorLogging.run_on_exit = lambda : messagebox.showwarning(title="GestOSC - Camera Disconnected", message="The camera was suddenly disconnected!")
                break
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            if cv2.getWindowProperty(VizUtils.WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break
            
            landmarker.detect_async(mp_image, int(time.time() * 1000) - start_time)
            
            if VizUtils.show_visuals and VizUtils.buffered_frame is not None:
                cv2.imshow(VizUtils.WINDOW_NAME, VizUtils.buffered_frame)
            
            time.sleep(1/125) # Max refresh rate, as per https://github.com/yannbouteiller/vgamepad/issues/39#issuecomment-3100989230
        

        Camera.stop_measurement()
    
    def stop_measurement():
        SteeringWheel.gamepad.reset()
        SteeringWheel.gamepad.update()
        Camera.camera.release()
        cv2.destroyAllWindows()

class LoadingScreen:
    def run(msg: str, func):
        return LoadingScreen(msg, func).res
    
    def __init__(self, msg: str, func):
        self.msg = msg
        self.func = func
        
        self.root = Tk()
        self.root.title(msg)
        self.root.overrideredirect(1)
        self.root.eval('tk::PlaceWindow . center')
        self.root.attributes('-topmost', True)
        
        self.ui()
        self.start()
        
        self.root.mainloop()
    
    def threadable_func(self):
        self.res = self.func()
        self.queue.put("")
    
    def ui(self):
        self.label = Label(self.root, text="GestOSC")
        self.label.pack(side=TOP, anchor=NW)
        self.label = Label(self.root, text=self.msg, font=("TkDefaultFont", 12))
        self.label.pack(side=TOP)
        self.prog_bar = Progressbar(
            self.root, orient="horizontal",
            length=200, mode="indeterminate",
            takefocus=True
            )
        self.prog_bar.pack(side=TOP)
        self.prog_bar.start()

    def start(self):
        self.queue = queue.Queue()
        Thread(target=self.threadable_func, args=()).start()
        self.root.after(0, self.process_queue)

    def process_queue(self):
        if self.queue.empty():
            self.root.after(200, self.process_queue)
        else:
            self.prog_bar.stop()
            self.root.destroy()

def run():
    print("Starting...")
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.LIVE_STREAM,
        num_hands=2,
        result_callback=process_landmarker_res
    )
    with HandLandmarker.create_from_options(options) as landmarker:
        if LoadingScreen.run("Setting up camera...", Camera.init_camera) == 0:
            Camera.measurement_loop(landmarker)

    ErrorLogging.run_on_exit()



if __name__ == "__main__":
    run()