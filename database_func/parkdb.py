import sqlite3
from datetime import datetime

def connect(db_name):
    c = sqlite3.connect(db_name)
    return c

def create_card_tabel(db_name):
    c = connect(db_name)
    cur = c.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS cards_info 
                (card_id TEXT, 
                is_active BOOLEAN DEFAULT false, 
                PRIMARY KEY(card_id));''')
    c.close()
    
def create_activity_table(db_name):
    c = connect(db_name)
    cur = c.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS parking_activity 
                (activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT, 
                FOREIGN KEY(card_id) REFERENCES cards_info(card_id));''')
    c.close()
    
def create_log_table(db_name):
    c = connect(db_name)
    cur = c.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS logs 
                (log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT NOT NULL, 
                lp_img_in TEXT NOT NULL, 
                ocr_output TEXT NOT NULL, 
                time_in TIMESTAMP NOT NULL, 
                time_out TIMESTAMP, 
                lp_img_out TEXT, 
                FOREIGN KEY (card_id) REFERENCES cards_info(card_id));''')
    c.close()    

def insert_cards(db_name, id):
    c = connect(db_name)
    cur = c.cursor()
    cur.execute("INSERT INTO cards_info (card_id) VALUES (?)", (id,))
    c.commit()
    c.close()

def remove_cards(db_name, id):
    c = connect(db_name)
    cur = c.cursor()
    cur.execute("DELETE FROM cards_info WHERE card_id = ?", (id,))
    c.commit()
    c.close()
    
def get_card_list(db_name):
    c = connect(db_name)
    cur = c.cursor()
    cur.execute("SELECT card_id FROM cards_info;")
    card_ids = cur.fetchall()
    c.close()
    return card_ids

def get_all_logs(db_name):
    c = connect(db_name)
    cur = c.cursor()
    cur.execute("SELECT * FROM logs;")
    logs = cur.fetchall()
    c.close()
    return logs

def check_card_exists(db_name, card_id):
    c = connect(db_name)
    cur = c.cursor()
    
    cur.execute("SELECT COUNT(*) FROM cards_info WHERE card_id = ?", (card_id,))
    count = cur.fetchone()[0]
    
    if (count):
        return True
    else:
        return False
    
def check_card_active(db_name, card_id):
    c = connect(db_name)
    cur = c.cursor()
    
    cur.execute("SELECT COUNT(*) FROM parking_activity WHERE card_id = ?", (card_id,))
    is_active = cur.fetchone()[0]
    
    if (is_active):
        return True
    else:
        return False
    
    
def insert_park_activity(db_name, activity_id, card_id):
    c = connect(db_name)
    cur = c.cursor()

    if (check_card_active(db_name, card_id)):
        print(f"Card with ID {card_id} is already active.")
        return
    else:
        cur.execute("INSERT INTO parking_activity VALUES (?, ?)", (activity_id, card_id))
        c.commit()
        print("Activity created successfully.")
    c.close()

def delete_parking_activity(db_name, card_id):
    c = connect(db_name)
    cur = c.cursor()
    
    if check_card_exists(db_name, card_id):
        cur.execute("DELETE FROM parking_activity WHERE card_id = ?", (card_id,))
        print("Activity deleted. Now update the status in the cards_info table.")
        cur.execute("UPDATE cards_info SET is_active = false WHERE card_id = ?", (card_id,))
        print("Card status updated.")
        c.commit()
    else:
        print(f"Card with ID {card_id} does not exist")
    c.close()
            
def update_cards_status(db_name, card_id):
    c = connect(db_name)
    cur = c.cursor()

    if check_card_exists(db_name, card_id):
        cur.execute("UPDATE cards_info SET is_active = true WHERE card_id = ?", (card_id,))
        print("Card status updated.")
        c.commit()
    c.commit()
    c.close()

def insert_log(db_name, time_in, card_id, lp_img_in, ocr_output):
    c = connect(db_name)
    cur = c.cursor()
    if check_card_exists(db_name, card_id):
        cur.execute("INSERT INTO logs (card_id, lp_img_in, ocr_output, time_in) VALUES (?, ?, ?, ?)",
                    (card_id, lp_img_in, ocr_output, time_in))
        c.commit()
        print("Log created successfully.")
    else:
        print(f"Card with ID {card_id} does not exist.")
    
    c.close()

def get_log_ocr_output(db_name, card_id):
    c = connect(db_name)
    cur = c.cursor()
    cur.execute("SELECT ocr_output FROM logs WHERE card_id = ? AND time_out IS NULL", (card_id,))
    ocr_output = cur.fetchone()[0]
    c.close()
    return ocr_output

def get_log_image_in(db_name, card_id):
    c = connect(db_name)
    cur = c.cursor()
    cur.execute("SELECT lp_img_in FROM logs WHERE card_id = ? AND time_out IS NULL", (card_id,))
    lp_img_in = cur.fetchone()[0]
    c.close()
    return lp_img_in
    
def update_log_exit(db_name, time_out, card_id, lp_img_out):
    c = connect(db_name)
    cur = c.cursor()

    if check_card_exists(db_name, card_id):
        # Select from logs table where card_id = card_id and time_out = null
        cur.execute("SELECT COUNT(*) FROM logs WHERE card_id = ? AND time_out IS NULL", (card_id,))
        count = cur.fetchone()[0]

        if count > 0:
            cur.execute("UPDATE logs SET time_out = ?, lp_img_out = ? WHERE card_id = ? AND time_out IS NULL", (time_out, lp_img_out, card_id))
            c.commit()
            print("Log updated successfully.")
        else:
            print(f"No active log entry found for card with ID {card_id}.")
    else:
        print(f"Card with ID {card_id} does not exist.")

    c.close()



# db = "parking.db"        
# create_card_tabel(db)
# create_activity_table(db)
# create_log_table(db)
# insert_cards(db, 1)
# insert_cards(db, 2)
# insert_park_activity(db, 1, 1)
# update_cards_status(db)
# insert_log(db, 1, 1, "imgin", "12345")
# update_log_exit(db, 1, "imgout")
# delete_parking_activity(db, 1)

