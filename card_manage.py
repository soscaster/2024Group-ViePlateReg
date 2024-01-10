import sys
sys.dont_write_bytecode = True
import tkinter as tk
from tkinter import ttk, messagebox
from database_func import parkdb
import threading, time, serial, json, os, signal, platform

def force_quit():
    pid = os.getpid()
    if platform.system() == "Windows":
        os.system(f"taskkill /F /PID {pid}")
    else:
        os.kill(pid, signal.SIGKILL)

class CardDatabaseWindow:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.root.title("Card Database Management")
        self.root.geometry("400x350")

        self.load_configuration()
        db = "parking.db"      
        parkdb.connect(db)
        parkdb.create_card_tabel(db)
        parkdb.create_activity_table(db)
        parkdb.create_log_table(db)

        frame = tk.Frame(self.root, highlightbackground="black", highlightthickness=1)
        frame.pack(fill="both", expand=True)

        frame.columnconfigure(1, weight=1)  # Make column 1 expandable

        self.card_list_label = tk.Label(frame, text="Card List:")
        self.card_list_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.card_listbox = tk.Listbox(frame)
        self.card_listbox.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        # Add a scrollbar to the listbox
        self.card_scrollbar = tk.Scrollbar(frame)
        self.card_scrollbar.grid(row=1, column=2, sticky="nsew")
        self.card_listbox.config(yscrollcommand=self.card_scrollbar.set)
        self.card_scrollbar.config(command=self.card_listbox.yview)

        # Label to display the card ID read from the serial port
        self.card_id_label = tk.Label(frame, text="Card ID:", font=("Arial Bold", 16))
        self.card_id_label.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.add_card_button = tk.Button(frame, text="Add Card", command=self.insert_card)
        self.add_card_button.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        self.remove_card_button = tk.Button(frame, text="Remove Card", command=self.remove_card)
        self.remove_card_button.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        self.load_card_list()
        self.start_serial_thread()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # No resizing the window
        self.root.resizable(False, False)

    def load_card_list(self):
        # Load the list of cards from the database and populate the listbox
        self.card_listbox.delete(0, tk.END)
        card_list = parkdb.get_card_list("parking.db")
        for card in card_list:
            self.card_listbox.insert(tk.END, card[0])

    def insert_card(self):
        try:
            card_id = self.card_id_label.cget("text")
            # Prompt the user to confirm the insertion (must set parent to this window)
            if card_id == "Đang chờ thẻ..." or card_id == "Card ID:" or card_id == "":  # No card detected
                messagebox.showinfo("Thông báo", "Vui lòng đưa thẻ vào.", parent=self.root)
                return
            if not messagebox.askyesno("Thêm thẻ", f"Bạn có chắc chắn muốn thêm thẻ {card_id}?", parent=self.root):
                return
            parkdb.insert_cards("parking.db", card_id)
            self.load_card_list()
        except Exception as e:
            print(f"Error inserting card: {e}")

    def remove_card(self):
        selected_card = self.card_listbox.curselection()
        if selected_card:
            # Prompt the user to confirm the deletion
            if not messagebox.askyesno("Xóa thẻ", "Bạn có chắc chắn muốn xóa thẻ này?", parent=self.root):
                return
            card_id = self.card_listbox.get(selected_card[0])
            parkdb.remove_cards("parking.db", card_id)
            self.load_card_list()
        else:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một thẻ để xóa.", parent=self.root)

    def load_configuration(self):
        try:
            with open("config.json", 'r') as file:
                config = json.load(file)
                # Get the entrance and exit camera from the config file (convert to int)
                self.serial_port = config.get('serial_port', None)
                print("Configuration loaded.")
                print("Serial port:", self.serial_port)
        except (FileNotFoundError, json.JSONDecodeError):
            # Use default values if file not found or decoding error
            self.serial_port = None
            print("Default configuration loaded.")

    def read_serial_data(self):
        while self.is_capturing:
            if self.serial_port:
                try:
                    ser = serial.Serial(self.serial_port, baudrate=115200)
                    while True:
                        serial_output = ser.readline().decode().strip()
                        print("Serial Data:", serial_output)
                        self.update_card_id_label(serial_output)
                except serial.SerialException as e:
                    print(f"Error reading serial data: {e}")
                time.sleep(0.1)

    def update_card_id_label(self, card_data):
        if card_data == "":  # Assuming an empty string indicates the card has been removed
            # Reset the card labels to their original state
            self.card_id_label.config(text="Đang chờ thẻ...")
        else:
            self.card_id_label.config(text=f"{card_data}")
            # Schedule the next update after a delay (e.g., 1000 milliseconds)
            self.root.after(3000, self.update_card_id_label, "")

    def start_serial_thread(self):
        self.is_capturing = True
        self.serial_thread = threading.Thread(target=self.read_serial_data)
        self.serial_thread.start()

    def on_close(self):
        # Ask the user if they want to exit
        if messagebox.askyesno("Thoát", "Bạn có chắc chắn muốn thoát?"):
            self.root.destroy()
            force_quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = CardDatabaseWindow(root, None)
    root.mainloop()
