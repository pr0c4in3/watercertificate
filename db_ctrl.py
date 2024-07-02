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
    
    def debug_user(self) -> list: #DEBUG:负责查询user表
        cur = self.conn.cursor()
        cur.execute('''
            SELECT * FROM users
        ''')
        rows = cur.fetchall()
        users = []
        for row in rows:
            users.append({
                'username': row[0],
                'password': row[1],
            })
        return users


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
                    image_name TEXT UNIQUE,
                    watermark TEXT NOT NULL,
                    watermark_key TEXT NOT NULL,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            ''')

    def add_certificate(self, username: str, image_path: str, image_name: str, watermark: str, watermark_key: str):
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT INTO certificates (username, image_path, image_name, watermark, watermark_key)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, image_path, image_name, watermark, watermark_key))
                return True
        except sqlite3.IntegrityError:
            return False
        

    def get_certificate_by_user(self, username: str) -> list:
        cur = self.conn.cursor()
        cur.execute('''
            SELECT * FROM certificates
            WHERE username = ?
        ''', (username,))
        rows = cur.fetchall()
        certificates = []
        for row in rows:
            certificates.append({
                'id': row[0],
                'username': row[1],
                'image_path': row[2],
                'image_name': row[3],
                'watermark': row[4],
                'watermark_key': row[5]
            })
        return certificates

    
    def get_certificate_by_wm(self, watermark: str) -> Optional[dict]:
        cur = self.conn.cursor()
        cur.execute('''
            SELECT * FROM certificates
            WHERE watermark = ?
        ''', (watermark,))
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


if __name__ == "__main__":
    login_manager = login_db()
    ca_manager = ca_db()

    #DEBUG，检查之前的注册是否成功
    print('debug:')
    print(login_manager.debug_user())






    # # 示例
    # print('')
    # print('example:')
    # # 用户注册
    # if login_manager.register_user('user1', 'password123'):
    #     print('User registered successfully.')
    # else:
    #     print('Username already exists.')

    # # 登录
    # if login_manager.authenticate_user('user1', 'password123'):
    #     print('Authentication successful.')
    # else:
    #     print('Authentication failed.')

    # # 添加证书，这里已经添加过一次了，再添加会破坏unique完整性（修改后的代码检测到异常后会返回false继续运行）
    # add1=ca_manager.add_certificate('user1', '/path/to/image', 'image1.png', 'watermark_data', 'watermark_key123')
    # add2=ca_manager.add_certificate('user1', '/path/to/image', 'image2.png', 'test', '123456')
    # print('add1',add1,'add2',add2)
    # # 查询证书
    # cert = ca_manager.get_certificate_by_user('user1')
    # if cert:
    #     print(f'Certificate found: ')
    #     for item in cert:
    #         print(item['image_name'])
    # else:
    #     print('Certificate not found.')
    # cert2 = ca_manager.get_certificate_by_wm('test')
    # u=cert2['username']
    # if cert2:
    #     print(f'Certificate found: {u}')
    # else:
    #     print('Certificate not found.')
