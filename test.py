import sys
sys.dont_write_bytecode = True
import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import json

class VideoFeed:
    def __init__(self, root, video_source=0):
        self.root = root
        self.video_source = video_source
        self.video_capture = cv2.VideoCapture(self.video_source)
        self.video_feed_label = tk.Label(self.root)
        self.video_feed_label.pack(side="top", fill="both", expand=True)

        self.update_video_feed()

    def update_video_feed(self):
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, _ = frame.shape
            new_width = (height * 16) // 9
            if new_width < width:
                start = (width - new_width) // 2
                frame = frame[:, start:start+new_width]
            else:
                new_height = (width * 9) // 16
                start = (height - new_height) // 2
                frame = frame[start:start+new_height, :]
            image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image)
            self.video_feed_label.configure(image=photo)
            self.video_feed_label.image = photo
        self.root.after(10, self.update_video_feed)

class ConfigWindow:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.root.title("Configuration")
        self.root.geometry("350x250")

        self.entrance_label = tk.Label(self.root, text="Chọn camera cho LUỒNG XE VÀO:")
        self.entrance_label.pack(pady=10)
        self.entrance_dropdown = ttk.Combobox(self.root, values=self.app.get_video_devices())
        self.entrance_dropdown.pack(pady=10)

        self.exit_label = tk.Label(self.root, text="Chọn camera cho LUỒNG XE RA:")
        self.exit_label.pack(pady=10)
        self.exit_dropdown = ttk.Combobox(self.root, values=self.app.get_video_devices())
        self.exit_dropdown.pack(pady=10)

        self.save_button = tk.Button(self.root, text="Lưu cài đặt", command=self.save_configuration)
        self.save_button.pack(pady=10)

    def save_configuration(self):
        entrance_camera = self.entrance_dropdown.get()
        exit_camera = self.exit_dropdown.get()

        config = {
            'entrance_camera': entrance_camera,
            'exit_camera': exit_camera
        }

        self.app.apply_configuration(config)
        self.root.destroy()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("ViePlateReg")

        self.load_configuration()

        entrance_frame = tk.Frame(self.root, bg="white")
        entrance_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        entrance_frame.pack_propagate(0)

        exit_frame = tk.Frame(self.root, bg="white")
        exit_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        exit_frame.pack_propagate(0)

        entrance_label = tk.Label(entrance_frame, text="LUỒNG XE VÀO", bg="yellow", font=("Arial", 18))
        entrance_label.pack(side="top", fill="both", expand=True)

        exit_label = tk.Label(exit_frame, text="LUỒNG XE RA", bg="yellow", font=("Arial", 18))
        exit_label.pack(side="top", fill="both", expand=True)

        self.entrance_video_feed = VideoFeed(entrance_frame, video_source=self.entrance_camera)
        self.exit_video_feed = VideoFeed(exit_frame, video_source=self.exit_camera)

        button_frame = tk.Frame(self.root)
        button_frame.pack(side="top", pady=5)

        exit_button = tk.Button(button_frame, text="Thoát", command=self.root.destroy)
        exit_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        config_button = tk.Button(button_frame, text="Cài đặt", command=self.open_config_window)
        config_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        entrance_button_frame = tk.Frame(entrance_frame)
        entrance_button_frame.pack(side="bottom", pady=5)

        entrance_allow_button = tk.Button(entrance_button_frame, text="CHO PHÉP XE VÀO", command=self.allow_entrance_vehicle)
        entrance_allow_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        entrance_cancel_button = tk.Button(entrance_button_frame, text="HUỶ XE VÀO", command=self.cancel_entrance_registration)
        entrance_cancel_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        exit_button_frame = tk.Frame(exit_frame)
        exit_button_frame.pack(side="bottom", pady=5)

        exit_allow_button = tk.Button(exit_button_frame, text="CHO PHÉP XE RA", command=self.allow_exit_vehicle)
        exit_allow_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        exit_cancel_button = tk.Button(exit_button_frame, text="HUỶ XE RA", command=self.cancel_exit_registration)
        exit_cancel_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.root.attributes("-fullscreen", True)
        self.root.resizable(False, False)

    def allow_entrance_vehicle(self):
        # Thay sau
        print("Entrance vehicle allowed")

    def cancel_entrance_registration(self):
        # Thay sau
        print("Entrance registration canceled")

    def allow_exit_vehicle(self):
        # Thay sau
        print("Exit vehicle allowed")

    def cancel_exit_registration(self):
        # Thay sau
        print("Exit registration canceled")

    def open_config_window(self):
        config_window = tk.Toplevel(self.root)
        ConfigWindow(config_window, self)
        config_window.resizable(False, False)

    def get_video_devices(self):
        devices = []
        for i in range(5):  # Check the first 5 devices (adjust as needed)
            if cv2.VideoCapture(i).isOpened():
                devices.append(str(i))  # Append only the ID
        return devices

    def load_configuration(self):
        try:
            with open("config.json", 'r') as file:
                config = json.load(file)
                # Get the entrance and exit camera from the config file (convert to int)
                self.entrance_camera = int(config.get('entrance_camera', 0))
                self.exit_camera = int(config.get('exit_camera', 1))
                print("Configuration loaded.")
                print("Entrance camera:", self.entrance_camera)
                print("Exit camera:", self.exit_camera)
        except (FileNotFoundError, json.JSONDecodeError):
            # Use default values if file not found or decoding error
            self.entrance_camera = 0
            self.exit_camera = 0
            print("Default configuration loaded.")

    def apply_configuration(self, config):
        self.entrance_camera = config.get('entrance_camera', 0)
        self.exit_camera = config.get('exit_camera', 1)
        self.save_configuration()

    def save_configuration(self):
        config = {
            'entrance_camera': self.entrance_camera,
            'exit_camera': self.exit_camera
        }

        with open("config.json", 'w') as file:
            json.dump(config, file)
            print("Configuration saved.")

    def on_close(self):
        self.save_configuration()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
