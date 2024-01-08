import sys
sys.dont_write_bytecode = True
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import json
import sqlite3
import threading

class VideoFeed:
    def __init__(self, root, video_source=0):
        self.root = root
        self.video_source = video_source
        self.video_capture = cv2.VideoCapture(self.video_source)
        self.video_feed_label = tk.Label(self.root)
        self.video_feed_label.pack(side="top", fill="both", expand=True)

        self.start_capturing()

    def update_video_feed(self):
        try:
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
        except Exception as e:
            print(f"Error updating video feed: {e}")
        self.root.after(10, self.update_video_feed)

    def start_capturing(self):
        self.is_capturing = True
        self.capture_thread = threading.Thread(target=self.update_video_feed)
        self.capture_thread.start()

    def stop_capturing(self):
        self.is_capturing = False
        self.capture_thread.join()
        self.video_capture.release()

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

        entrance_frame = tk.Frame(self.root, highlightbackground="black", highlightthickness=1)
        entrance_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        entrance_frame.pack_propagate(0)

        exit_frame = tk.Frame(self.root, highlightbackground="black", highlightthickness=1)
        exit_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        exit_frame.pack_propagate(0)

        entrance_label = tk.Label(entrance_frame, text="LUỒNG XE VÀO", bg="yellow", font=("Arial", 18))
        entrance_label.pack(side="top", fill="both", expand=True)

        exit_label = tk.Label(exit_frame, text="LUỒNG XE RA", bg="yellow", font=("Arial", 18))
        exit_label.pack(side="top", fill="both", expand=True)

        self.entrance_video_feed = VideoFeed(entrance_frame, video_source=self.entrance_camera)
        self.exit_video_feed = VideoFeed(exit_frame, video_source=self.exit_camera)

        # Section Nút XE VÀO
        entrance_button_frame = tk.Frame(entrance_frame, highlightbackground="black", highlightthickness=1)
        entrance_button_frame.pack(side="bottom", pady=5)

        entrance_allow_button = tk.Button(entrance_button_frame, text="CHO PHÉP XE VÀO (F7)", bg="blue", fg="white", font=("Arial", 14), command=self.allow_entrance_vehicle)
        entrance_allow_button.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        entrance_cancel_button = tk.Button(entrance_button_frame, text="HUỶ XE VÀO (F8)", bg="red", fg="white", font=("Arial", 14), command=self.cancel_entrance_registration)
        entrance_cancel_button.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        
        # 3 dòng kết quả nhận diện xe vào
        entrance_result_label = tk.Label(entrance_button_frame, text="KẾT QUẢ NHẬN DIỆN XE VÀO", bg="blue", fg="white", font=("Arial Bold", 14))
        entrance_result_label.grid(row=0, column=1, padx=15, pady=5, sticky="ew")

        entrance_ocr_label = tk.Label(entrance_button_frame, text="DDDL-DDDDD", bg="yellow", fg="red", font=("Arial Bold", 27))
        entrance_ocr_label.grid(row=1, column=1, padx=15, pady=5, sticky="ew")

        entrance_time_label = tk.Label(entrance_button_frame, text="Giờ vào: DD/MM/YY HH:MM", bg="aqua", fg="black", font=("Arial", 14))
        entrance_time_label.grid(row=2, column=1, padx=15, pady=5, sticky="ew")

        # Frame chứa kết quả nhận diện xe vào, chiều cao bằng tổng chiều cao của 3 dòng kết quả trên
        ocr_entrance_result_frame = tk.Frame(entrance_button_frame, bg="black")
        ocr_entrance_result_frame.grid(row=0, column=0, rowspan=3, padx=5, pady=5, sticky="nsew")
        # Set uniform height for all the rows in the grid
        entrance_button_frame.grid_rowconfigure((0, 1, 2), weight=1, uniform="equal")
        # Adjust the frame to maintain a 16:9 aspect ratio
        ocr_entrance_result_frame.bind("<Configure>", lambda e: ocr_entrance_result_frame.configure(width=int(ocr_entrance_result_frame.winfo_height() * 16 / 9)))

        # Frame đọc thẻ xe vào
        entrance_card_frame = tk.Label(entrance_button_frame, text="Đọc thẻ NULL - Mã thẻ: XXX", bg="yellow", fg="black", font=("Arial Bold", 15))
        entrance_card_frame.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        config_button = tk.Button(entrance_button_frame, font=("Arial", 14), bg="burlywood", fg="black", text="Cài đặt", command=self.open_config_window)
        config_button.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        # END Section Nút XE VÀO

        # Section Nút XE RA
        exit_button_frame = tk.Frame(exit_frame, highlightbackground="black", highlightthickness=1)
        exit_button_frame.pack(side="bottom", pady=5)

        exit_allow_button = tk.Button(exit_button_frame, text="CHO PHÉP XE RA (F11)", bg="blue", fg="white", font=("Arial", 14), command=self.allow_exit_vehicle)
        exit_allow_button.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        
        exit_cancel_button = tk.Button(exit_button_frame, text="HUỶ XE RA (F12)", bg="red", fg="white", font=("Arial", 14), command=self.cancel_exit_registration)
        exit_cancel_button.grid(row=4, column=0, padx=5, pady=5, sticky="ew")

        # 3 dòng kết quả nhận diện xe ra
        exit_result_label = tk.Label(exit_button_frame, text="KẾT QUẢ XE RA TRÙNG KHỚP", bg="green", fg="white", font=("Arial Bold", 14))
        exit_result_label.grid(row=0, column=1, padx=15, pady=5, sticky="ew")

        exit_ocr_label = tk.Label(exit_button_frame, text="DDDL-DDDDD", bg="yellow", fg="red", font=("Arial Bold", 27))
        exit_ocr_label.grid(row=1, column=1, padx=15, pady=5, sticky="ew")

        exit_time_label = tk.Label(exit_button_frame, text="Giờ ra: DD/MM/YY HH:MM", bg="aqua", fg="black", font=("Arial", 14))
        exit_time_label.grid(row=2, column=1, padx=15, pady=5, sticky="ew")

        # Frame chứa kết quả nhận diện xe ra, chiều cao bằng tổng chiều cao của 3 dòng kết quả trên
        ocr_exit_result_frame = tk.Frame(exit_button_frame, bg="black")
        ocr_exit_result_frame.grid(row=0, column=0, rowspan=3, padx=5, pady=5, sticky="nsew")
        # Set uniform height for all the rows in the grid
        exit_button_frame.grid_rowconfigure((0, 1, 2), weight=1, uniform="equal")
        # Adjust the frame to maintain a 16:9 aspect ratio
        ocr_exit_result_frame.bind("<Configure>", lambda e: ocr_exit_result_frame.configure(width=int(ocr_exit_result_frame.winfo_height() * 16 / 9)))
        
        # Frame đọc thẻ xe ra
        exit_card_frame = tk.Label(exit_button_frame, text="Đọc thẻ NULL - Mã thẻ: XXX", bg="yellow", fg="black", font=("Arial Bold", 15))
        exit_card_frame.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        exit_button = tk.Button(exit_button_frame, bg="red", fg="white", font=("Arial", 14), text="Thoát", command=self.on_close)
        exit_button.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        # END Section Nút XE RA

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
        # Ask the user if they want to exit
        if messagebox.askyesno("Thoát", "Bạn có chắc chắn muốn thoát?"):
            self.entrance_video_feed.stop_capturing()  # Stop capturing before closing
            self.exit_video_feed.stop_capturing()
            self.save_configuration()
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
