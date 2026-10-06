import sqlite3
from pathlib import Path

DB_PATH = Path("bibliogen.db")

def get_connection():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def initialize_database():
    c = get_connection()
    c.execute("""CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, author TEXT, publisher TEXT,
        publication_year INTEGER, subject TEXT, isbn TEXT,
        language TEXT, resource_type TEXT, keywords TEXT)""")
    c.commit(); c.close()

def add_book(title, author="", publisher="", publication_year=None,
             subject="", isbn="", language="", resource_type="كتاب", keywords=""):
    c = get_connection()
    cur = c.execute("""INSERT INTO books
        (title,author,publisher,publication_year,subject,isbn,language,resource_type,keywords)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (title,author,publisher,publication_year,subject,isbn,language,resource_type,keywords))
    c.commit(); book_id = cur.lastrowid; c.close(); return book_id

def get_all_books():
    c = get_connection()
    rows = c.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
    c.close(); return [dict(r) for r in rows]

def count_books():
    c = get_connection()
    n = c.execute("SELECT COUNT(*) AS n FROM books").fetchone()["n"]
    c.close(); return n

def seed_demo_books():
    if count_books(): return
    data = [
        ("مدخل إلى علم المكتبات والمعلومات","أحمد محمد","دار المعرفة",2024,
         "علم المكتبات والمعلومات","978000000001","العربية","كتاب","مكتبات، معلومات، تنظيم المعلومات"),
        ("مبادئ تنظيم المعلومات","محمد علي","دار العلوم",2023,
         "تنظيم المعلومات والفهرسة","978000000002","العربية","كتاب","فهرسة، تصنيف، ميتاداتا"),
        ("المعايير الحديثة للوصف الببليوغرافي","سارة أحمد","المكتبة الأكاديمية",2022,
         "الوصف الببليوغرافي وRDA","978000000003","العربية","كتاب","RDA، وصف ببليوغرافي، بيانات وصفية"),
        ("الاسترجاع الذكي للمعلومات","يوسف خالد","دار الفكر",2024,
         "استرجاع المعلومات والذكاء الاصطناعي","978000000004","العربية","كتاب","استرجاع المعلومات، ذكاء اصطناعي، بحث دلالي"),
        ("الذكاء الاصطناعي في المكتبات","ليلى حسن","دار المستقبل",2025,
         "الذكاء الاصطناعي والمكتبات","978000000005","العربية","كتاب","ذكاء اصطناعي، مكتبات، RAG، نماذج لغوية")
    ]
    for b in data: add_book(*b)
