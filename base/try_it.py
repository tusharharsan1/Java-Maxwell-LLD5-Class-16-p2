"""Run this file to see what your code does:   python try_it.py
It builds an empty shop in memory, saves three users, reads them back, and then meets a user with a kind that nobody knows.
Nothing is saved on disk, and nothing needs the internet. Do not change this file."""
import sqlite3

try:
    from app.family import Customer, Seller, UnknownKind, create_tables, load_all, save
except Exception as exc:  # a mistake in the file above would stop the import
    raise SystemExit(f"a file has a problem -> {type(exc).__name__}: {exc}")

conn = sqlite3.connect(":memory:")
conn.execute("PRAGMA foreign_keys = ON")  # SQLite checks the links between tables only when this is ON
create_tables(conn)
SAVED = [
    Customer("u1", "asha@shopnest.com", "12 MG Road, Pune"),
    Seller("u2", "ravi@shopnest.com", "Ravi Watches"),
    Customer("u3", "mina@shopnest.com", "4 Park Street, Kolkata"),
]


def show(label, make_text):
    try:
        print(f"  {label:<40}: {make_text()}")
    except Exception as exc:
        print(f"  {label:<40}: something is wrong -> {type(exc).__name__}: {exc}")


def count(sql):
    return conn.execute(sql).fetchone()[0]


print("Task 1: save writes two rows for each user")
for user in SAVED:
    try:
        save(conn, user)
    except Exception as exc:
        print(f"  save stopped for {user.email} -> {type(exc).__name__}: {exc}")
show("rows in users", lambda: count("SELECT COUNT(*) FROM users"))
show("rows in customer", lambda: count("SELECT COUNT(*) FROM customer"))
show("rows in seller", lambda: count("SELECT COUNT(*) FROM seller"))
show("customer rows with their user", lambda: count("SELECT COUNT(*) FROM customer c JOIN users u ON u.id = c.id AND u.kind = 'customer'"))
show("seller rows with their user", lambda: count("SELECT COUNT(*) FROM seller s JOIN users u ON u.id = s.id AND u.kind = 'seller'"))

print("Task 2: load_all builds the class from the word in `kind`")
loaded = []
try:
    loaded = load_all(conn)
except Exception as exc:
    print(f"  load_all stopped -> {type(exc).__name__}: {exc}")
for number, user in enumerate(loaded, 1):
    show(str(number), lambda user=user: f"{type(user).__name__} {user.email}")
show("same objects as the ones saved", lambda: loaded == sorted(SAVED, key=lambda u: u.email))

print("A user with a kind that nobody knows")
conn.execute("INSERT INTO users (id, email, kind) VALUES ('u9', 'zed@shopnest.com', 'admin')")
try:
    result = load_all(conn)
    show("load_all", lambda: f"no error, it gave {len(result)} users")
except UnknownKind as exc:
    show("load_all", lambda: f"UnknownKind -> {exc}")
except Exception as exc:
    show("load_all", lambda: f"something is wrong -> {type(exc).__name__}: {exc}")
