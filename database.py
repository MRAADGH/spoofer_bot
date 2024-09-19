import uuid
import sqlite3
import datetime

def create_database():
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()

    # Create the users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id TEXT PRIMARY KEY,
            user TEXT,
            pass TEXT,
            exp TEXT,
            license INTEGER,
            solde INTEGER
        )
    ''')

    # Create the transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            order_id TEXT PRIMARY KEY,
            chat_id TEXT,
            type TEXT,
            amount REAL,
            currency TEXT,
            track_id TEXT,
            status TEXT,
            date TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES users (chat_id)
        )
    ''')

    conn.commit()
    conn.close()

    print("Base de données créée avec succès.")

def add_transaction(chat_id, payment_type, amount, currency, track_id, status, order_id):
    # order_id = f"ORD-{payment_type.upper()}-{uuid.uuid4()}"
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO transactions (order_id, chat_id, type, amount, currency, track_id, status, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, chat_id, payment_type, amount, currency, track_id, status, datetime.datetime.now()))
    
    conn.commit()
    conn.close()
    
    return order_id

def update_transaction_status(track_id, new_status):
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE transactions
        SET status = ?
        WHERE track_id = ?
    ''', (new_status, track_id))
    
    conn.commit()
    conn.close()

def update_transaction_by_order_id(order_id, track_id, new_status, amount, currency):
    # Connect to the SQLite database
    conn = sqlite3.connect('utilisateurs.db')
    cursor = conn.cursor()

    # Update the transaction details based on the order_id
    cursor.execute('''
        UPDATE transactions 
        SET track_id = ?, status = ?, amount = ?, currency = ?
        WHERE order_id = ?
    ''', (track_id, new_status, amount, currency, order_id))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def get_chat_id(track_id):
    try:
        conn = sqlite3.connect('utilisateurs.db')
        cursor = conn.cursor()

        cursor.execute("SELECT chat_id FROM transactions WHERE track_id = ?", (track_id,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return None
    except sqlite3.Error as e:
        print(f"Error occurred: {e}")
        return None
    
    finally:
        conn.close()

def get_chat_id_by_order_id(order_id):
    try:
        conn = sqlite3.connect('utilisateurs.db')
        cursor = conn.cursor()

        cursor.execute("SELECT chat_id FROM transactions WHERE order_id = ?", (order_id,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return None
    except sqlite3.Error as e:
        print(f"Error occurred: {e}")
        return None
    
    finally:
        conn.close()

def get_status_by_order_id(order_id):
    try:
        conn = sqlite3.connect('utilisateurs.db')
        cursor = conn.cursor()

        cursor.execute("SELECT status FROM transactions WHERE order_id = ?", (order_id,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return None
    except sqlite3.Error as e:
        print(f"Error occurred: {e}")
        return None
    
    finally:
        conn.close()

def get_order_id(track_id):
    try:
        conn = sqlite3.connect('utilisateurs.db')
        cursor = conn.cursor()

        cursor.execute("SELECT order_id FROM transactions WHERE track_id = ?", (track_id,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return None
    except sqlite3.Error as e:
        print(f"Error occurred: {e}")
        return None
    
    finally:
        conn.close()


if __name__ == "__main__":
    create_database()
