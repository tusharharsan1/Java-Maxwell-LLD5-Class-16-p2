import sqlite3
from dataclasses import dataclass
from typing import List


class UnknownKind(ValueError):
    """Already finished. It is raised when the word in the column `kind` is not one that the shop knows."""


@dataclass
class User:
    """Already finished. What every user has."""
    id: str
    email: str


@dataclass
class Customer(User):
    """Already finished. A customer is a user with a shipping address."""
    shipping_address: str
    kind = "customer"  # not a field: it is the word that is stored in the column `kind`


@dataclass
class Seller(User):
    """Already finished. A seller is a user with a shop name."""
    shop_name: str
    kind = "seller"


# Already finished. The family in three tables ("joined tables"). The `id` of a child table is also a link to `users.id`.
CREATE_TABLES = """
CREATE TABLE users (id TEXT NOT NULL PRIMARY KEY, email TEXT NOT NULL, kind TEXT NOT NULL);
CREATE TABLE customer (id TEXT NOT NULL PRIMARY KEY REFERENCES users (id), shipping_address TEXT NOT NULL);
CREATE TABLE seller (id TEXT NOT NULL PRIMARY KEY REFERENCES users (id), shop_name TEXT NOT NULL);
"""

# Already finished. One SELECT that asks for every user, with the own columns of both kinds (an empty box where the kind does not fit).
SELECT_ALL = """
SELECT users.id, users.email, users.kind, customer.shipping_address, seller.shop_name
FROM users
LEFT OUTER JOIN customer ON users.id = customer.id
LEFT OUTER JOIN seller ON users.id = seller.id
ORDER BY users.email
"""


def create_tables(conn: sqlite3.Connection) -> None:
    """Already finished."""
    conn.executescript(CREATE_TABLES)


def save(conn: sqlite3.Connection, user: User) -> None:
    """Save one Customer or one Seller: one row in `users`, and one row in the table of its own kind, with the SAME id."""
    conn.execute("INSERT INTO users (id, email, kind) VALUES (?, ?, ?)", (user.id, user.email, user.kind))  # Already finished: the shared row.
    # TODO 1 (Task 1): the row of the child, with the same id as the row in `users`.
    #   - a customer (user.kind is "customer"): insert (the id, the shipping address) into the table `customer`
    #   - a seller (user.kind is "seller"): insert (the id, the shop name) into the table `seller`
    conn.commit()  # Already finished.


def load_all(conn: sqlite3.Connection) -> List[User]:
    """Read every user back, sorted by email. Each one must be an object of its real class."""
    users = []
    for user_id, email, kind, shipping_address, shop_name in conn.execute(SELECT_ALL).fetchall():
        if kind == "customer":
            users.append(Customer(user_id, email, shipping_address))  # Already finished. It is your example for a customer.
        # TODO 2 (Task 2): the word in `kind` decides the class.
        #   - "seller": add a Seller (the id, the email, the shop name)
        #   - any other word: raise UnknownKind with the text  kind 'admin' does not match any of: 'customer', 'seller'
        #     (with the real word in the place of admin)
    return users
