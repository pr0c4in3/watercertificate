import sqlite3
from typing import Optional

class login_db:
    def __init__(self, db_name: str = 'login.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL
                )
            ''')

    def register_user(self, username: str, password: str) -> bool:
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT INTO users (username, password)
                    VALUES (?, ?)
                ''', (username, password))
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate_user(self, username: str, password: str) -> bool:
        cur = self.conn.cursor()
        cur.execute('''
            SELECT * FROM users
            WHERE username = ? AND password = ?
        ''', (username, password))
        return cur.fetchone() is not None


class ca_db:
    def __init__(self, db_name: str = 'ca.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS certificates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    image_name TEXT NOT NULL,
                    watermark TEXT NOT NULL,
                    watermark_key TEXT NOT NULL,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            ''')

    def add_certificate(self, username: str, image_path: str, image_name: str, watermark: str, watermark_key: str):
        with self.conn:
            self.conn.execute('''
                INSERT INTO certificates (username, image_path, image_name, watermark, watermark_key)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, image_path, image_name, watermark, watermark_key))

    def get_certificate(self, image_name: str) -> Optional[dict]:
        cur = self.conn.cursor()
        cur.execute('''
            SELECT * FROM certificates
            WHERE image_name = ?
        ''', (image_name,))
        row = cur.fetchone()
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'image_path': row[2],
                'image_name': row[3],
                'watermark': row[4],
                'watermark_key': row[5]
            }
        return None

# Example usage
if __name__ == "__main__":
    login_manager = login_db()
    ca_manager = ca_db()

    # Register a new user
    if login_manager.register_user('user1', 'password123'):
        print('User registered successfully.')
    else:
        print('Username already exists.')

    # Authenticate user
    if login_manager.authenticate_user('user1', 'password123'):
        print('Authentication successful.')
    else:
        print('Authentication failed.')

    # Add a new certificate
    ca_manager.add_certificate('user1', '/path/to/image', 'image1.png', 'watermark_data', 'watermark_key123')

    # Retrieve a certificate
    cert = ca_manager.get_certificate('image1.png')
    if cert:
        print(f'Certificate found: {cert}')
    else:
        print('Certificate not found.')
