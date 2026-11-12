"""Tests for app/family.py (standard library only). Run them from the folder that holds `app/` and `tests/`:

    python -m unittest -v          (pytest works too)

The tests check what the README says: save writes two rows for each user with the same id, a customer never gets a row
in `seller` (and a seller never gets a row in `customer`), load_all gives every user back as an object of its real
class, sorted by email, the WORD IN `kind` decides the class, and a word that nobody knows gives UnknownKind with one exact text."""
import dataclasses
import inspect
import os
import random
import sqlite3
import tempfile
import unittest

from app import family
from app.family import Customer, Seller, UnknownKind, User, create_tables, load_all, save

# The users of try_it.py
ASHA = Customer("u1", "asha@shopnest.com", "12 MG Road, Pune")
RAVI = Seller("u2", "ravi@shopnest.com", "Ravi Watches")
MINA = Customer("u3", "mina@shopnest.com", "4 Park Street, Kolkata")
FAMILY = [ASHA, RAVI, MINA]
# The state of the connection: foreign keys checked (like try_it.py) and not checked (the default of sqlite3).
FOREIGN_KEYS = [True, False]
# Texts that break an INSERT that is built by gluing text together, and texts of other languages.
HARD_TEXTS = [
    "O'Neil's Corner", 'The "Big" Shop', "100% cotton, 50% silk", "x'); DROP TABLE users; --", "café ☕", "ショップ", "", "  spaces  ",
]


def new_connection(foreign_keys=True, path=":memory:"):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = " + ("ON" if foreign_keys else "OFF"))
    create_tables(conn)
    return conn


def count(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()[0]


def random_family(seed, size):
    """A new family for each seed (so that no answer can be written into the code): customers and sellers in a mixed order,
    with emails that are all different and ids that are not 'u1', 'u2'."""
    rng = random.Random(seed)
    people = []
    for number in range(size):
        user_id = "id-%04x" % rng.randrange(0x10000) + "-%d" % number
        email = "%s%03d@shopnest.com" % (rng.choice(["amy", "bo", "cy", "di", "ed", "flo"]), number)
        if rng.random() < 0.5:
            people.append(Customer(user_id, email, rng.choice(HARD_TEXTS) or "no address"))
        else:
            people.append(Seller(user_id, email, rng.choice(HARD_TEXTS) or "no shop"))
    rng.shuffle(people)
    return people


def add_raw_user(conn, user_id, email, kind, shipping_address=None, shop_name=None):
    """Put rows in the tables by hand, to make a shop that `save` would never make."""
    conn.execute("INSERT INTO users (id, email, kind) VALUES (?, ?, ?)", (user_id, email, kind))
    if shipping_address is not None:
        conn.execute("INSERT INTO customer (id, shipping_address) VALUES (?, ?)", (user_id, shipping_address))
    if shop_name is not None:
        conn.execute("INSERT INTO seller (id, shop_name) VALUES (?, ?)", (user_id, shop_name))
    conn.commit()


class ShopTestCase(unittest.TestCase):
    def connection(self, foreign_keys=True):
        conn = new_connection(foreign_keys)
        self.addCleanup(conn.close)
        return conn

    def saved(self, users, foreign_keys=True):
        conn = self.connection(foreign_keys)
        for user in users:
            save(conn, user)
        return conn


# ======================================================================================================================
# The lines that are already finished must still be there.
# ======================================================================================================================
class FinishedPartsTests(ShopTestCase):
    def test_the_classes_and_their_words_are_unchanged(self):
        """Customer and Seller are Users, with their fields in the order of the README, and the words 'customer' and 'seller'."""
        self.assertTrue(issubclass(Customer, User))
        self.assertTrue(issubclass(Seller, User))
        self.assertEqual([f.name for f in dataclasses.fields(Customer)], ["id", "email", "shipping_address"])
        self.assertEqual([f.name for f in dataclasses.fields(Seller)], ["id", "email", "shop_name"])
        self.assertEqual(Customer("a", "b", "c").kind, "customer")
        self.assertEqual(Seller("a", "b", "c").kind, "seller")

    def test_unknown_kind_is_a_value_error_with_its_own_name(self):
        """UnknownKind is its own class (a kind of ValueError), so that it can be told apart from other errors."""
        self.assertTrue(issubclass(UnknownKind, ValueError))
        self.assertIsNot(UnknownKind, ValueError)

    def test_the_names_of_the_functions_and_their_parameters_are_unchanged(self):
        """save(conn, user), load_all(conn) and create_tables(conn) keep their names and their parameters."""
        self.assertEqual(list(inspect.signature(save).parameters), ["conn", "user"])
        self.assertEqual(list(inspect.signature(load_all).parameters), ["conn"])
        self.assertEqual(list(inspect.signature(create_tables).parameters), ["conn"])

    def test_the_three_tables_have_the_columns_of_the_readme(self):
        """create_tables makes users(id, email, kind), customer(id, shipping_address) and seller(id, shop_name)."""
        conn = self.connection()
        wanted = {
            "users": ["id", "email", "kind"],
            "customer": ["id", "shipping_address"],
            "seller": ["id", "shop_name"],
        }
        for table, columns in wanted.items():
            self.assertEqual([row[1] for row in conn.execute(f"PRAGMA table_info({table})")], columns)


# ======================================================================================================================
# Task 1: save writes two rows.
# ======================================================================================================================
class SaveTests(ShopTestCase):
    def test_every_user_gets_one_row_in_users_with_its_email_and_its_word(self):
        """The row in `users` has the id, the email and the word of the class (the line that is already written)."""
        conn = self.saved(FAMILY)
        self.assertEqual(
            conn.execute("SELECT id, email, kind FROM users ORDER BY id").fetchall(),
            [("u1", "asha@shopnest.com", "customer"), ("u2", "ravi@shopnest.com", "seller"), ("u3", "mina@shopnest.com", "customer")],
        )

    def test_a_customer_gets_a_row_in_customer_with_the_same_id(self):
        """The row of a customer is in the table `customer`: the same id as in `users`, and the shipping address."""
        for foreign_keys in FOREIGN_KEYS:
            with self.subTest(foreign_keys=foreign_keys):
                conn = self.saved(FAMILY, foreign_keys)
                self.assertEqual(
                    conn.execute("SELECT id, shipping_address FROM customer ORDER BY id").fetchall(),
                    [("u1", "12 MG Road, Pune"), ("u3", "4 Park Street, Kolkata")],
                )

    def test_a_seller_gets_a_row_in_seller_with_the_same_id(self):
        """The row of a seller is in the table `seller`: the same id as in `users`, and the shop name."""
        for foreign_keys in FOREIGN_KEYS:
            with self.subTest(foreign_keys=foreign_keys):
                conn = self.saved(FAMILY, foreign_keys)
                self.assertEqual(conn.execute("SELECT id, shop_name FROM seller").fetchall(), [("u2", "Ravi Watches")])

    def test_the_numbers_of_rows_are_3_2_and_1(self):
        """Three users give 3 rows in users, 2 in customer and 1 in seller: two rows for each user, in `users` and in its own table."""
        conn = self.saved(FAMILY)
        self.assertEqual(count(conn, "SELECT COUNT(*) FROM users"), 3)
        self.assertEqual(count(conn, "SELECT COUNT(*) FROM customer"), 2)
        self.assertEqual(count(conn, "SELECT COUNT(*) FROM seller"), 1)

    def test_a_customer_never_gets_a_row_in_seller(self):
        """Only customers saved: the table `seller` stays empty."""
        conn = self.saved([ASHA, MINA])
        self.assertEqual(count(conn, "SELECT COUNT(*) FROM customer"), 2)
        self.assertEqual(count(conn, "SELECT COUNT(*) FROM seller"), 0)

    def test_a_seller_never_gets_a_row_in_customer(self):
        """Only sellers saved: the table `customer` stays empty."""
        conn = self.saved([RAVI, Seller("u8", "kim@shopnest.com", "Kim Bags")])
        self.assertEqual(count(conn, "SELECT COUNT(*) FROM seller"), 2)
        self.assertEqual(count(conn, "SELECT COUNT(*) FROM customer"), 0)

    def test_the_row_of_the_child_has_the_id_of_its_own_user_not_of_another_one(self):
        """Every child row joins to a row in `users` of the SAME kind: no child row is left without its user, and none is mixed up."""
        people = random_family(5, 40)
        conn = self.saved(people)
        self.assertEqual(
            count(conn, "SELECT COUNT(*) FROM customer c JOIN users u ON u.id = c.id AND u.kind = 'customer'"),
            sum(1 for p in people if p.kind == "customer"),
        )
        self.assertEqual(
            count(conn, "SELECT COUNT(*) FROM seller s JOIN users u ON u.id = s.id AND u.kind = 'seller'"),
            sum(1 for p in people if p.kind == "seller"),
        )
        for person in people:
            table, column = ("customer", "shipping_address") if person.kind == "customer" else ("seller", "shop_name")
            self.assertEqual(
                conn.execute(f"SELECT {column} FROM {table} WHERE id = ?", (person.id,)).fetchall(),
                [(getattr(person, column),)],
                person,
            )

    def test_texts_with_quotes_and_other_hard_characters_are_saved_as_they_are(self):
        """Apostrophes, quotes, %, a line that looks like SQL, other languages and an empty text: saved and read back unchanged."""
        for number, text in enumerate(HARD_TEXTS):
            with self.subTest(text=text):
                conn = self.connection()
                customer = Customer("c%d" % number, "c%d@shopnest.com" % number, text)
                seller = Seller("s%d" % number, "s%d@shopnest.com" % number, text)
                save(conn, customer)
                save(conn, seller)
                self.assertEqual(count(conn, "SELECT COUNT(*) FROM users"), 2)
                self.assertEqual(conn.execute("SELECT shipping_address FROM customer").fetchall(), [(text,)])
                self.assertEqual(conn.execute("SELECT shop_name FROM seller").fetchall(), [(text,)])

    def test_save_does_not_change_the_object(self):
        """The object that is saved is the same after the save."""
        conn = self.connection()
        customer = Customer("u1", "a@shopnest.com", "Here")
        save(conn, customer)
        self.assertEqual((customer.id, customer.email, customer.shipping_address, customer.kind), ("u1", "a@shopnest.com", "Here", "customer"))

    def test_the_saved_rows_are_committed_so_that_another_connection_sees_them(self):
        """save ends with a commit: a second connection to the same file sees the rows of both tables."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "shop.db")
            first = new_connection(path=path)
            self.addCleanup(first.close)
            save(first, ASHA)
            save(first, RAVI)
            second = sqlite3.connect(path, timeout=0.2)
            self.addCleanup(second.close)
            try:
                self.assertEqual(count(second, "SELECT COUNT(*) FROM users"), 2)
                self.assertEqual(count(second, "SELECT COUNT(*) FROM customer"), 1)
                self.assertEqual(count(second, "SELECT COUNT(*) FROM seller"), 1)
            except sqlite3.OperationalError as exc:
                self.fail(f"another connection cannot read the shop (is the save committed?): {exc}")


# ======================================================================================================================
# Task 2: load_all builds the class from the word in `kind`.
# ======================================================================================================================
class LoadAllTests(ShopTestCase):
    def test_the_example_of_the_readme(self):
        """Asha and Mina come back as Customers and Ravi as a Seller, sorted by email, and equal to the objects that were saved."""
        for foreign_keys in FOREIGN_KEYS:
            with self.subTest(foreign_keys=foreign_keys):
                conn = self.saved(FAMILY, foreign_keys)
                loaded = load_all(conn)
                self.assertEqual([(type(u).__name__, u.email) for u in loaded],
                                 [("Customer", "asha@shopnest.com"), ("Customer", "mina@shopnest.com"), ("Seller", "ravi@shopnest.com")])
                self.assertEqual(loaded, sorted(FAMILY, key=lambda u: u.email))

    def test_every_user_is_an_object_of_its_real_class(self):
        """The class is exactly Customer or Seller (not User, not a dictionary, not a tuple), and it is a User."""
        conn = self.saved(FAMILY)
        for user in load_all(conn):
            self.assertIn(type(user), (Customer, Seller))
            self.assertIsInstance(user, User)
        by_email = {u.email: u for u in load_all(conn)}
        self.assertIs(type(by_email["ravi@shopnest.com"]), Seller)
        self.assertIs(type(by_email["asha@shopnest.com"]), Customer)

    def test_the_fields_of_a_seller_are_in_the_right_places(self):
        """The id, the email and the shop name of a seller are not mixed up."""
        conn = self.saved([RAVI])
        seller = load_all(conn)[0]
        self.assertEqual((seller.id, seller.email, seller.shop_name), ("u2", "ravi@shopnest.com", "Ravi Watches"))

    def test_the_result_is_a_list(self):
        """load_all gives a list (not a tuple, not a generator)."""
        conn = self.saved(FAMILY)
        self.assertIsInstance(load_all(conn), list)

    def test_an_empty_shop_gives_an_empty_list(self):
        """No user at all: the answer is [] and not None, and not an error."""
        conn = self.connection()
        self.assertEqual(load_all(conn), [])

    def test_only_customers_and_only_sellers(self):
        """A shop with one kind only still works."""
        self.assertEqual(load_all(self.saved([MINA, ASHA])), [ASHA, MINA])
        sellers = [Seller("s2", "zoe@shopnest.com", "Zoe Shoes"), Seller("s1", "abe@shopnest.com", "Abe Belts")]
        self.assertEqual(load_all(self.saved(sellers)), [sellers[1], sellers[0]])

    def test_the_users_are_sorted_by_email_whatever_the_order_of_the_saves(self):
        """Saved in the order z, m, a, c: they come back a, c, m, z."""
        people = [
            Customer("1", "z@shopnest.com", "Z road"), Seller("2", "m@shopnest.com", "M shop"),
            Customer("3", "a@shopnest.com", "A road"), Seller("4", "c@shopnest.com", "C shop"),
        ]
        loaded = load_all(self.saved(people))
        self.assertEqual([u.email for u in loaded], ["a@shopnest.com", "c@shopnest.com", "m@shopnest.com", "z@shopnest.com"])
        self.assertEqual([type(u).__name__ for u in loaded], ["Customer", "Seller", "Seller", "Customer"])

    def test_save_and_load_all_together_give_back_what_was_saved(self):
        """Many different families, with hard texts: what comes out is equal to what went in (same classes, same fields)."""
        for seed in range(1, 11):
            for foreign_keys in FOREIGN_KEYS:
                with self.subTest(seed=seed, foreign_keys=foreign_keys):
                    people = random_family(seed, 5 + seed * 6)
                    loaded = load_all(self.saved(people, foreign_keys))
                    self.assertEqual(loaded, sorted(people, key=lambda u: u.email))
                    self.assertEqual([type(u) for u in loaded], [type(u) for u in sorted(people, key=lambda u: u.email)])

    def test_load_all_gives_a_new_list_each_time_and_changes_nothing(self):
        """Two calls give two equal lists (users are not added to an old list), and the tables are the same afterwards."""
        conn = self.saved(FAMILY)
        first = load_all(conn)
        second = load_all(conn)
        self.assertEqual(first, second)
        self.assertEqual(len(second), 3)
        self.assertIsNot(first, second)
        self.assertEqual((count(conn, "SELECT COUNT(*) FROM users"), count(conn, "SELECT COUNT(*) FROM customer"), count(conn, "SELECT COUNT(*) FROM seller")), (3, 2, 1))


# ======================================================================================================================
# Task 2: the word in `kind` decides, and a word that nobody knows gives UnknownKind.
# ======================================================================================================================
class UnknownKindTests(ShopTestCase):
    def test_an_unknown_word_stops_load_all_with_the_exact_text_of_the_readme(self):
        """kind 'admin' gives UnknownKind and the text:  kind 'admin' does not match any of: 'customer', 'seller'."""
        conn = self.saved(FAMILY)
        add_raw_user(conn, "u9", "zed@shopnest.com", "admin")
        with self.assertRaises(UnknownKind) as caught:
            load_all(conn)
        self.assertEqual(str(caught.exception), "kind 'admin' does not match any of: 'customer', 'seller'")

    def test_the_real_word_is_in_the_text(self):
        """Other words give other texts: the word of the row is put in, with quotes around it."""
        for word in ["admin", "manager", "staff", "Seller", "CUSTOMER", "customer ", "", "sellers"]:
            with self.subTest(word=word):
                conn = self.connection()
                add_raw_user(conn, "x1", "x@shopnest.com", word)
                with self.assertRaises(UnknownKind) as caught:
                    load_all(conn)
                self.assertEqual(str(caught.exception), "kind %r does not match any of: 'customer', 'seller'" % word)

    def test_new_words_that_the_code_has_never_seen_give_the_same_error(self):
        """Words made up at random (so that they cannot be written into the code) all give UnknownKind with their own word."""
        rng = random.Random(99)
        for _ in range(15):
            word = "role" + str(rng.randrange(10 ** 6))
            conn = self.saved([ASHA, RAVI])
            add_raw_user(conn, "q1", "q@shopnest.com", word)
            with self.assertRaises(UnknownKind) as caught:
                load_all(conn)
            self.assertEqual(str(caught.exception), "kind '%s' does not match any of: 'customer', 'seller'" % word)

    def test_the_error_is_unknown_kind_and_not_a_plain_value_error(self):
        """The class of the error is UnknownKind itself."""
        conn = self.connection()
        add_raw_user(conn, "x1", "x@shopnest.com", "admin")
        with self.assertRaises(UnknownKind) as caught:
            load_all(conn)
        self.assertIs(type(caught.exception), UnknownKind)

    def test_a_bad_row_among_good_rows_stops_load_all_and_gives_no_half_list(self):
        """Amy (customer), Bob (admin) and Cat (seller): load_all raises. It does not skip Bob and it does not return Amy alone."""
        conn = self.connection()
        add_raw_user(conn, "1", "amy@shopnest.com", "customer", shipping_address="Amy Road")
        add_raw_user(conn, "2", "bob@shopnest.com", "admin")
        add_raw_user(conn, "3", "cat@shopnest.com", "seller", shop_name="Cat Shop")
        with self.assertRaises(UnknownKind) as caught:
            load_all(conn)
        self.assertIn("'admin'", str(caught.exception))

    def test_a_bad_row_at_the_start_and_at_the_end_is_found_too(self):
        """The unknown word is found at the first place of the sorted list and at the last place."""
        for email in ("aaa@shopnest.com", "zzz@shopnest.com"):
            with self.subTest(email=email):
                conn = self.saved(FAMILY)
                add_raw_user(conn, "bad", email, "ghost")
                with self.assertRaises(UnknownKind):
                    load_all(conn)

    def test_the_word_decides_even_if_the_row_has_a_child_row(self):
        """kind 'admin' with a row in `seller` (and in `customer`) is still an unknown kind: the full box does not make it a seller."""
        conn = self.connection()
        add_raw_user(conn, "1", "a@shopnest.com", "admin", shop_name="Looks Like A Shop")
        with self.assertRaises(UnknownKind) as caught:
            load_all(conn)
        self.assertEqual(str(caught.exception), "kind 'admin' does not match any of: 'customer', 'seller'")
        conn = self.connection()
        add_raw_user(conn, "1", "a@shopnest.com", "admin", shipping_address="Looks Like An Address", shop_name="Also A Shop")
        with self.assertRaises(UnknownKind):
            load_all(conn)

    def test_the_word_decides_even_if_the_child_row_is_missing(self):
        """kind 'seller' with no row in `seller` is still a Seller (the box is empty, but the word says seller). No error."""
        conn = self.connection()
        add_raw_user(conn, "1", "a@shopnest.com", "seller")
        add_raw_user(conn, "2", "b@shopnest.com", "customer", shipping_address="B Road")
        loaded = load_all(conn)
        self.assertEqual([type(u).__name__ for u in loaded], ["Seller", "Customer"])
        self.assertEqual((loaded[0].id, loaded[0].email), ("1", "a@shopnest.com"))

    def test_a_seller_with_a_row_in_customer_too_is_still_a_seller(self):
        """kind 'seller' whose id is in both child tables: the word decides, so it is a Seller with its shop name."""
        conn = self.connection()
        add_raw_user(conn, "1", "a@shopnest.com", "seller", shipping_address="Some Road", shop_name="Real Shop")
        loaded = load_all(conn)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0], Seller("1", "a@shopnest.com", "Real Shop"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
