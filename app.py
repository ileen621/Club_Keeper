from flask import Flask, render_template, request, redirect, url_for
import sqlite3

DB_FILE = 'membership.db'


def connect_db():
    """連到 SQLite，並啟用 dict-like row 存取。"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


with connect_db() as conn:
    cur = conn.cursor()

    # 建表：若不存在就建立 members 表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS members (
            iid        INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    NOT NULL UNIQUE,
            email      TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,
            phone      TEXT,
            birthdate  TEXT
        )
    """)

    # 預設 admin：先查再插入
    cur.execute(
        "SELECT 1 FROM members WHERE username=? OR email=?",
        ('admin', 'admin@example.com')
    )
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO members "
            "(username, email, password, phone, birthdate) "
            "VALUES (?, ?, ?, ?, ?)",
            ('admin', 'admin@example.com', 'admin123',
             '0912345678', '1990-01-01')
        )

    conn.commit()


app = Flask(__name__)


@app.template_filter('add_stars')
def add_stars(s):
    
    return f'★{s}★!'


@app.route('/')
def index():
    """首頁：顯示 index.html。"""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        birthdate = request.form.get('birthdate', '')

        # 基本空值檢查
        if username == '' or email == '' or password == '':
            return render_template(
                'error.html',
                error_message='請輸入用戶名、電子郵件和密碼'
            )

        conn = connect_db()
        cur = conn.cursor()

        # 檢查用戶名或 Email 是否重複
        cur.execute(
            "SELECT 1 FROM members WHERE username=? OR email=?",
            (username, email)
        )
        if cur.fetchone():
            conn.close()
            return render_template(
                'error.html',
                error_message='用戶名或電子郵件已存在'
            )

        # 插入新會員
        cur.execute(
            "INSERT INTO members "
            "(username, email, password, phone, birthdate) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, email, password, phone, birthdate)
        )
        conn.commit()
        conn.close()

        # 註冊成功後轉到登入頁
        return redirect(url_for('login'))

    # GET：顯示註冊表單
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email == '' or password == '':
            return render_template(
                'error.html',
                error_message='請輸入電子郵件和密碼'
            )

        conn = connect_db()
        cur = conn.cursor()

        # 查詢帳密
        cur.execute(
            "SELECT iid, username FROM members "
            "WHERE email=? AND password=?",
            (email, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            return redirect(url_for('welcome', iid=user['iid']))
        else:
            return render_template(
                'error.html',
                error_message='電子郵件或密碼錯誤'
            )

    return render_template('login.html')


@app.route('/welcome/<int:iid>')
def welcome(iid):
    # Welcome頁顯示會員資料或錯誤
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM members WHERE iid = ?", (iid,))
    user = cur.fetchone()
    conn.close()

    if user:
        return render_template('welcome.html', user=user)
    else:
        return render_template(
            'error.html',
            error_message='用戶不存在'
        )


@app.route('/edit_profile/<int:iid>', methods=['GET', 'POST'])
def edit_profile(iid):                #修改基本資料:顯示現有資料，更新
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        birthdate = request.form.get('birthdate', '')

        if email == '' or password == '':
            return render_template(
                'error.html',
                error_message='請輸入電子郵件和密碼'
            )

        conn = connect_db()
        cur = conn.cursor()

        # 檢查 Email 是否被他人使用
        cur.execute(
            "SELECT 1 FROM members WHERE email=? AND iid<>?",
            (email, iid)
        )
        if cur.fetchone():
            conn.close()
            return render_template(
                'error.html',
                error_message='電子郵件已被使用'
            )

        # 更新會員資料
        cur.execute(
            "UPDATE members "
            "SET email=?, password=?, phone=?, birthdate=? "
            "WHERE iid=?",
            (email, password, phone, birthdate, iid)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('welcome', iid=iid))

    # 載入原本資料
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM members WHERE iid = ?", (iid,))
    user = cur.fetchone()
    conn.close()

    if user:
        return render_template('edit_profile.html', user=user)
    else:
        return render_template(
            'error.html',
            error_message='用戶不存在'
        )


@app.route('/delete/<int:iid>')
def delete_user(iid): 
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM members WHERE iid = ?", (iid,))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))
