import sys
sys.dont_write_bytecode = True
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from database_func import parkdb
import ocr
import threading,  time, shutil,  datetime, serial,  platform, os, signal,  json,  cv2, subprocess

if platform.system() == "Windows":
    run_me = "python"
elif platform.system() == "Linux":
    run_me = "python3"
else:
    run_me = "python3"

def force_quit():
    pid = os.getpid()
    if platform.system() == "Windows":
        os.system(f"taskkill /F /PID {pid}")
    else:
        os.kill(pid, signal.SIGKILL)

class VideoGet:
    def __init__(self, source=0):
        self.stream = cv2.VideoCapture(source)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):    
        threading.Thread(target=self.get, args=()).start()
        return self

    def get(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()

    def stop(self):
        self.stopped = True
        self.stream.release()

class VideoShow:
    def __init__(self, root, video_getter):
        self.root = root
        self.video_getter = video_getter
        self.video_feed_label = tk.Label(self.root)
        self.video_feed_label.pack(side="top", fill="both", expand=True)

    def update_video_feed(self):
        try:
            frame = self.video_getter.frame
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, _ = frame.shape
                new_width = (height * 16) // 9
                if new_width < width:
                    start = (width - new_width) // 2
                    frame = frame[:, start:start + new_width]
                else:
                    new_height = (width * 9) // 16
                    start = (height - new_height) // 2
                    frame = frame[start:start + new_height, :]
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image)
                self.video_feed_label.configure(image=photo)
                self.video_feed_label.image = photo
        except Exception as e:
            print(f"Error updating video feed: {e}")
        self.root.after(10, self.update_video_feed)

    def start_showing(self):
        self.show_thread = threading.Thread(target=self.update_video_feed)
        self.show_thread.start()

    def stop_showing(self):
        self.video_getter.stop()
        self.show_thread.join()

class ConfigWindow:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.root.title("Configuration")
        self.root.geometry("350x300")

        self.entrance_label = tk.Label(self.root, text="Chọn camera cho LUỒNG XE VÀO:")
        self.entrance_label.pack(pady=10)
        self.entrance_dropdown = ttk.Combobox(self.root, values=self.app.get_video_devices())
        self.entrance_dropdown.pack(pady=10)

        self.exit_label = tk.Label(self.root, text="Chọn camera cho LUỒNG XE RA:")
        self.exit_label.pack(pady=10)
        self.exit_dropdown = ttk.Combobox(self.root, values=self.app.get_video_devices())
        self.exit_dropdown.pack(pady=10)

        self.serial_label = tk.Label(self.root, text="Chọn cổng Serial cho đầu đọc thẻ:")
        self.serial_label.pack(pady=10)
        self.serial_dropdown = ttk.Combobox(self.root, values=self.app.get_serial_ports())
        self.serial_dropdown.pack(pady=10)

        self.save_button = tk.Button(self.root, text="Lưu cài đặt", command=self.save_configuration)
        self.save_button.pack(pady=10)

    def save_configuration(self):
        entrance_camera = self.entrance_dropdown.get()
        exit_camera = self.exit_dropdown.get()
        serial_port = self.serial_dropdown.get()

        config = {
            'entrance_camera': entrance_camera,
            'exit_camera': exit_camera,
            'serial_port': serial_port
        }

        self.app.apply_configuration(config)
        self.root.destroy()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("ViePlateReg")

        self.load_configuration()

        self.card_data = None

        db = "parking.db"      
        parkdb.connect(db)
        parkdb.create_card_tabel(db)
        parkdb.create_activity_table(db)
        parkdb.create_log_table(db)

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

        # Video feed for entrance
        entrance_video_getter = VideoGet(source=self.entrance_camera)
        entrance_video_show = VideoShow(entrance_frame, entrance_video_getter)
        entrance_video_getter.start()
        entrance_video_show.start_showing()
        self.entrance_video_feed = entrance_video_getter

        # Video feed for exit
        exit_video_getter = VideoGet(source=self.exit_camera)
        exit_video_show = VideoShow(exit_frame, exit_video_getter)
        exit_video_getter.start()
        exit_video_show.start_showing()
        self.exit_video_feed = exit_video_getter

        # Section Nút XE VÀO
        entrance_button_frame = tk.Frame(entrance_frame, highlightbackground="black", highlightthickness=1)
        entrance_button_frame.pack(side="bottom", pady=5)

        entrance_allow_button = tk.Button(entrance_button_frame, text="CHO PHÉP XE VÀO (F7)", bg="blue", fg="white", font=("Arial", 14), command= lambda: self.allow_entrance_vehicle(self.card_data))
        entrance_allow_button.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        entrance_cancel_button = tk.Button(entrance_button_frame, text="HUỶ XE VÀO (F8)", bg="red", fg="white", font=("Arial", 14), command=self.cancel_entrance_registration)
        entrance_cancel_button.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        
        # 3 dòng kết quả nhận diện xe vào
        entrance_result_label = tk.Label(entrance_button_frame, text="KẾT QUẢ NHẬN DIỆN XE VÀO", bg="blue", fg="white", font=("Arial Bold", 14))
        entrance_result_label.grid(row=0, column=1, padx=15, pady=5, sticky="ew")

        entrance_ocr_label = tk.Label(entrance_button_frame, text="DDDL-DDDDD", bg="yellow", fg="red", font=("Arial Bold", 27))
        entrance_ocr_label.grid(row=1, column=1, padx=15, pady=5, sticky="ew")
        self.entrance_ocr_label = entrance_ocr_label

        entrance_time_label = tk.Label(entrance_button_frame, text="Giờ vào: DD/MM/YY HH:MM", bg="aqua", fg="black", font=("Arial", 14))
        entrance_time_label.grid(row=2, column=1, padx=15, pady=5, sticky="ew")
        self.entrance_time_label = entrance_time_label

        # Frame chứa kết quả nhận diện xe vào, chiều cao bằng tổng chiều cao của 3 dòng kết quả trên
        ocr_entrance_result_frame = tk.Frame(entrance_button_frame, bg="black")
        ocr_entrance_result_frame.grid(row=0, column=0, rowspan=3, padx=5, pady=5, sticky="nsew")
        # Set uniform height for all the rows in the grid
        entrance_button_frame.grid_rowconfigure((0, 1, 2), weight=1, uniform="equal")
        # Adjust the frame to maintain a 16:9 aspect ratio
        ocr_entrance_result_frame.bind("<Configure>", lambda e: ocr_entrance_result_frame.configure(width=int(ocr_entrance_result_frame.winfo_height() * 16 / 9)))
        self.ocr_entrance_result_frame = ocr_entrance_result_frame
        self.old_entrance_result_frame = ocr_entrance_result_frame

        # Frame đọc thẻ xe vào
        entrance_card_label = tk.Label(entrance_button_frame, text="Đọc thẻ NULL - Mã thẻ: XX XX XX XX", bg="yellow", fg="black", font=("Arial Bold", 15))
        entrance_card_label.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.entrance_card_label = entrance_card_label

        config_button = tk.Button(entrance_button_frame, font=("Arial", 14), bg="burlywood", fg="black", text="Cài đặt", command=self.open_config_window)
        config_button.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        # END Section Nút XE VÀO

        # Section Nút XE RA
        exit_button_frame = tk.Frame(exit_frame, highlightbackground="black", highlightthickness=1)
        exit_button_frame.pack(side="bottom", pady=5)

        exit_allow_button = tk.Button(exit_button_frame, text="CHO PHÉP XE RA (F11)", bg="blue", fg="white", font=("Arial", 14), command=lambda: self.allow_exit_vehicle(self.card_data))
        exit_allow_button.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        
        exit_cancel_button = tk.Button(exit_button_frame, text="HUỶ XE RA (F12)", bg="red", fg="white", font=("Arial", 14), command=self.cancel_exit_registration)
        exit_cancel_button.grid(row=4, column=0, padx=5, pady=5, sticky="ew")

        # 3 dòng kết quả nhận diện xe ra
        exit_result_label = tk.Label(exit_button_frame, text="KẾT QUẢ XE RA TRÙNG KHỚP", bg="green", fg="white", font=("Arial Bold", 14))
        exit_result_label.grid(row=0, column=1, padx=15, pady=5, sticky="ew")

        exit_ocr_label = tk.Label(exit_button_frame, text="DDDL-DDDDD", bg="yellow", fg="red", font=("Arial Bold", 27))
        exit_ocr_label.grid(row=1, column=1, padx=15, pady=5, sticky="ew")
        self.exit_ocr_label = exit_ocr_label

        exit_time_label = tk.Label(exit_button_frame, text="Giờ ra: DD/MM/YY HH:MM", bg="aqua", fg="black", font=("Arial", 14))
        exit_time_label.grid(row=2, column=1, padx=15, pady=5, sticky="ew")
        self.exit_time_label = exit_time_label

        # Frame chứa kết quả nhận diện xe ra, chiều cao bằng tổng chiều cao của 3 dòng kết quả trên
        ocr_exit_result_frame = tk.Frame(exit_button_frame, bg="black")
        ocr_exit_result_frame.grid(row=0, column=0, rowspan=3, padx=5, pady=5, sticky="nsew")
        # Set uniform height for all the rows in the grid
        exit_button_frame.grid_rowconfigure((0, 1, 2), weight=1, uniform="equal")
        # Adjust the frame to maintain a 16:9 aspect ratio
        ocr_exit_result_frame.bind("<Configure>", lambda e: ocr_exit_result_frame.configure(width=int(ocr_exit_result_frame.winfo_height() * 16 / 9)))
        self.ocr_exit_result_frame = ocr_exit_result_frame
        self.old_exit_result_frame = self.ocr_exit_result_frame

        # Frame đọc thẻ xe ra
        exit_card_label = tk.Label(exit_button_frame, text="Đọc thẻ NULL - Mã thẻ: XX XX XX XX", bg="yellow", fg="black", font=("Arial Bold", 15))
        exit_card_label.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.exit_card_label = exit_card_label

        exit_button = tk.Button(exit_button_frame, bg="red", fg="white", font=("Arial", 14), text="Thoát", command=self.on_close)
        exit_button.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        # END Section Nút XE RA

        self.is_reading_enabled = True
        self.entrance_snapshot_filename = None
        self.start_serial_thread()
        self.root.bind("<F7>", lambda event: self.allow_entrance_vehicle(self.card_data))
        self.root.bind("<F8>", lambda event: self.cancel_entrance_registration())
        self.root.bind("<F11>", lambda event: self.allow_exit_vehicle(self.card_data))
        self.root.bind("<F12>", lambda event: self.cancel_exit_registration())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.root.attributes("-fullscreen", True)
        self.root.resizable(False, False)

    def get_serial_ports(self):
        # Return a list of available serial ports
        try:
            import serial.tools.list_ports
            return [port.device for port in serial.tools.list_ports.comports()]
        except ImportError:
            # Handle if the serial module is not installed
            print("Serial module not found.")
            return []

    def read_serial_data(self):
        # Read data from the serial port and update card labels
        while self.is_capturing:
            if self.serial_port:
                try:
                    ser = serial.Serial(self.serial_port, baudrate=115200)
                    while True:
                        serial_output = ser.readline().decode().strip()
                        self.card_data = serial_output
                        print("Serial Data:", serial_output)
                        self.check_card(serial_output)
                except serial.SerialException as e:
                    print(f"Error reading serial data: {e}")
                time.sleep(0.1)
    
    # Read the card, use the parkdb to check if the card is exist or not, if yes then check if it's in the parking_activity or not. If no, run update_entrance_card_labels. If yes, run update_exit_card_labels
    def check_card(self, card_data):
        if not self.is_reading_enabled:  # Check if entrance updates are enabled
            return
        if card_data == "" or card_data == "START!":  # Assuming an empty string indicates the card has been removed
            return
        else:
            if parkdb.check_card_exists("parking.db", card_data):
                print("Card exists")
                if parkdb.check_card_active("parking.db", card_data):
                    print("Card is active")
                    self.update_exit_card_labels(card_data)
                    self.is_reading_enabled = False
                else:
                    print("Card is not active")
                    self.update_entrance_card_labels(card_data)
                    self.is_reading_enabled = False
            else:
                # Messagebox to notify that the card is not exist
                messagebox.showerror("Lỗi", f"Thẻ {card_data} không tồn tại trong hệ thống!")

    # Allow the vehicle to enter the parking lot (get card data from the card reader too)
    def allow_entrance_vehicle(self, card_data):
        self.move_entrance_snapshot_to_logs()
        parkdb.insert_park_activity("parking.db", 1, card_data)
        print("Entrance vehicle allowed")
        self.is_reading_enabled = True  # Enable card updates
        self.entrance_ocr_label.config(text="DDDL-DDDDD")
        self.entrance_card_label.config(text="Đọc thẻ NULL - Mã thẻ: XX XX XX XX")
        self.entrance_time_label.config(text="Giờ vào: DD/MM/YY HH:MM")
        self.restore_entrance_result_frame()

    def cancel_entrance_registration(self):
        try:
            if self.entrance_snapshot_filename:
                self.delete_entrance_snapshot()
                print("Snapshot deleted.")
        except Exception as e:
            print(f"Error deleting snapshot: {e}")
        print("Entrance registration canceled")
        self.is_reading_enabled = True  # Enable card updates
        self.entrance_ocr_label.config(text="DDDL-DDDDD")
        self.entrance_card_label.config(text="Đọc thẻ NULL - Mã thẻ: XX XX XX XX")
        self.entrance_time_label.config(text="Giờ vào: DD/MM/YY HH:MM")
        self.restore_entrance_result_frame()

    def allow_exit_vehicle(self, card_data):
        self.move_exit_snapshot_to_logs()
        parkdb.remove_park_activity("parking.db", card_data)
        print("Exit vehicle allowed")
        self.is_reading_enabled = True  # Enable card updates
        self.exit_ocr_label.config(text="DDDL-DDDDD")
        self.exit_card_label.config(text="Đọc thẻ NULL - Mã thẻ: XX XX XX XX")
        self.exit_time_label.config(text="Giờ vào: DD/MM/YY HH:MM")
        # Restore the old ocr
        self.restore_exit_result_frame()

    def cancel_exit_registration(self):
        try:
            if self.exit_snapshot_filename:
                self.delete_exit_snapshot()
                print("Snapshot deleted.")
        except Exception as e:
            print(f"Error deleting snapshot: {e}")
        print("Exit registration canceled")
        self.is_reading_enabled = True  # Enable card updates
        self.exit_ocr_label.config(text="DDDL-DDDDD")
        self.exit_card_label.config(text="Đọc thẻ NULL - Mã thẻ: XX XX XX XX")
        self.exit_time_label.config(text="Giờ vào: DD/MM/YY HH:MM")
        # Restore the old ocr
        self.restore_exit_result_frame()

    def restore_exit_result_frame(self):
        self.ocr_exit_result_frame = self.old_exit_result_frame

    def restore_entrance_result_frame(self):
        self.ocr_entrance_result_frame = self.old_entrance_result_frame

    def update_entrance_card_labels(self, card_data):
        # Take a picture of the vehicle (get the frame from the video feed)
        frame = self.entrance_video_feed.stream.read()[1]
        # Save the image to a folder
        try:
            os.makedirs("temp", exist_ok=True)
            timestamp = datetime.datetime.now().strftime('%d-%m-%y %H_%M_%S')
            self.entrance_snapshot_filename = os.path.join("temp", f"{timestamp}_IN.jpg")
            cv2.imwrite(self.entrance_snapshot_filename, frame)
            print("Image saved:", self.entrance_snapshot_filename)
        except Exception as e:
            print(f"Error saving image: {e}")

        try:
            # The result is a list, so we need to pick the first result of the list only
            ocr_entrance_result = ocr.extract_text(self.entrance_snapshot_filename)
            print("OCR result:", ocr_entrance_result)
            self.entrance_ocr_label.config(text=ocr_entrance_result)
            # Insert image temp/extracted.jpg to ocr_entrance_result_frame
            extracted_image_path = "temp/extracted.jpg"
            extracted_image = Image.open(extracted_image_path)
            width, height = extracted_image.size
            new_width = int(self.old_entrance_result_frame.winfo_width())
            new_height = int(new_width * 9 / 16)
            # Resize the extracted image
            resized_image = extracted_image.resize((new_width, new_height))
            resized_photo = ImageTk.PhotoImage(resized_image)

            for widget in self.ocr_entrance_result_frame.winfo_children():
                widget.destroy()

            # Insert the image to ocr_entrance_result_frame
            image_label = tk.Label(self.ocr_entrance_result_frame, image=resized_photo)
            image_label.image = resized_photo
            image_label.pack(fill="both", expand=True)
        except Exception as e:
            print(f"Error extracting Entrance text or displaying image: {e}")

        self.is_reading_enabled = False
        # Update the card labels with the new card data
        self.entrance_card_label.config(text=f"Đọc thẻ OK - Mã thẻ: {card_data}")
        # You may also update other relevant information, e.g., timestamps
        self.entrance_time_label.config(text=f"Giờ vào: {datetime.datetime.now().strftime('%d/%m/%y %H:%M')}")

    def update_exit_card_labels(self, card_data):
        # Take a picture of the vehicle (get the frame from the video feed)
        frame = self.exit_video_feed.stream.read()[1]
        # Save the image to a folder
        try:
            os.makedirs("temp", exist_ok=True)
            timestamp = datetime.datetime.now().strftime('%d-%m-%y %H_%M_%S')
            self.exit_snapshot_filename = os.path.join("temp", f"{timestamp}_OUT.jpg")
            cv2.imwrite(self.exit_snapshot_filename, frame)
            print("Image saved:", self.exit_snapshot_filename)
        except Exception as e:
            print(f"Error saving image: {e}")

        try:
            ocr_exit_result = ocr.extract_text(self.exit_snapshot_filename)
            print("OCR result:", ocr_exit_result)
            self.exit_ocr_label.config(text=ocr_exit_result)
            # Insert image temp/extracted.jpg to ocr_exit_result_frame
            extracted_image_path = "temp/extracted.jpg"
            extracted_image = Image.open(extracted_image_path)
            width, height = extracted_image.size
            # Calculate the new size based on the aspect ratio of the old ocr result frame
            new_width = int(self.old_exit_result_frame.winfo_width())
            new_height = int(new_width * 9 / 16)
            resized_image = extracted_image.resize((new_width, new_height))
            resized_photo = ImageTk.PhotoImage(resized_image)

            for widget in self.ocr_exit_result_frame.winfo_children():
                widget.destroy()

            # Insert the image to ocr_exit_result_frame
            image_label = tk.Label(self.ocr_exit_result_frame, image=resized_photo)
            image_label.image = resized_photo
            image_label.pack(fill="both", expand=True)

        except Exception as e:
            print(f"Error extracting Exit text or displaying image: {e}")

        self.is_reading_enabled = False
        # Update the card labels with the new card data
        self.exit_card_label.config(text=f"Đọc thẻ OK - Mã thẻ: {card_data}")
        # You may also update other relevant information, e.g., timestamps
        self.exit_time_label.config(text=f"Giờ ra: {datetime.datetime.now().strftime('%d/%m/%y %H:%M')}")

    def move_entrance_snapshot_to_logs(self):
        try:
            # Move the snapshot to the "logs" folder and reset the temporary variable
            if self.entrance_snapshot_filename:
                logs_folder = "logs"
                os.makedirs(logs_folder, exist_ok=True)
                # Create a folder named with the file name (without extension)
                filename_without_extension = os.path.splitext(os.path.basename(self.entrance_snapshot_filename))[0]
                destination_folder = os.path.join(logs_folder, filename_without_extension)
                os.makedirs(destination_folder, exist_ok=True)
                # Move the snapshot to the folder
                destination_filename = os.path.join(destination_folder, os.path.basename(self.entrance_snapshot_filename))
                shutil.move(self.entrance_snapshot_filename, destination_filename)
                # Move the extracted image to the folder
                extracted_image_path = "temp/extracted.jpg"
                destination_extracted_image_path = os.path.join(destination_folder, os.path.basename(extracted_image_path))
                shutil.move(extracted_image_path, destination_extracted_image_path)
                self.entrance_snapshot_filename = None
                print("Snapshot moved to logs folder.")
        except Exception as e:
            print(f"Error moving snapshot to logs folder: {e}")

    def move_exit_snapshot_to_logs(self):
        try:
            # Move the snapshot to the "logs" folder and reset the temporary variable
            if self.exit_snapshot_filename:
                logs_folder = "logs"
                os.makedirs(logs_folder, exist_ok=True)
                # Create a folder named with the file name (without extension)
                filename_without_extension = os.path.splitext(os.path.basename(self.exit_snapshot_filename))[0]
                destination_folder = os.path.join(logs_folder, filename_without_extension)
                os.makedirs(destination_folder, exist_ok=True)
                # Move the snapshot to the folder
                destination_filename = os.path.join(destination_folder, os.path.basename(self.exit_snapshot_filename))
                shutil.move(self.exit_snapshot_filename, destination_filename)
                # Move the extracted image to the folder
                extracted_image_path = "temp/extracted.jpg"
                destination_extracted_image_path = os.path.join(destination_folder, os.path.basename(extracted_image_path))
                shutil.move(extracted_image_path, destination_extracted_image_path)
                self.exit_snapshot_filename = None
                print("Snapshot moved to logs folder.")
        except Exception as e:
            print(f"Error moving snapshot to logs folder: {e}")

    def delete_entrance_snapshot(self):
        try:
            # Delete the snapshot if it exists and reset the temporary variable
            if self.entrance_snapshot_filename:
                os.remove(self.entrance_snapshot_filename)
                self.entrance_snapshot_filename = None
                print("Entrance snapshot deleted.")
            # Delete the extracted image if it exists
            extracted_image_path = "temp/extracted.jpg"
            if os.path.exists(extracted_image_path):
                os.remove(extracted_image_path)
                print("Extracted image deleted.")
        except Exception as e:
            print(f"Error deleting entrance snapshot: {e}")

    def delete_exit_snapshot(self):
        try:
            # Delete the snapshot if it exists and reset the temporary variable
            if self.exit_snapshot_filename:
                os.remove(self.exit_snapshot_filename)
                self.exit_snapshot_filename = None
                print("Exit snapshot deleted.")
            # Delete the extracted image if it exists
            extracted_image_path = "temp/extracted.jpg"
            if os.path.exists(extracted_image_path):
                os.remove(extracted_image_path)
                print("Extracted image deleted.")
        except Exception as e:
            print(f"Error deleting Exit snapshot: {e}")

    def start_serial_thread(self):
        self.is_capturing = True
        self.serial_thread = threading.Thread(target=self.read_serial_data)
        self.serial_thread.start()

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
                self.serial_port = config.get('serial_port', None)
                print("Configuration loaded.")
                print("Entrance camera:", self.entrance_camera)
                print("Exit camera:", self.exit_camera)
                print("Serial port:", self.serial_port)
        except (FileNotFoundError, json.JSONDecodeError):
            # Use default values if file not found or decoding error
            self.entrance_camera = 0
            self.exit_camera = 0
            self.serial_port = None
            print("Default configuration loaded.")

    def apply_configuration(self, config):
        self.entrance_camera = config.get('entrance_camera', 0)
        self.exit_camera = config.get('exit_camera', 1)
        self.serial_port = config.get('serial_port', None)
        self.save_configuration()

    def save_configuration(self):
        config = {
            'entrance_camera': self.entrance_camera,
            'exit_camera': self.exit_camera,
            'serial_port': self.serial_port
        }

        with open("config.json", 'w') as file:
            json.dump(config, file)
            print("Configuration saved.")

    def on_close(self):
        # Ask the user if they want to exit
        if messagebox.askyesno("Thoát", "Bạn có chắc chắn muốn thoát?"):
            self.save_configuration()
            self.root.destroy()
            force_quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
