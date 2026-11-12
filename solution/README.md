# A Family in Tables at ShopNest

## Problem Statement
ShopNest has two kinds of users. A **customer** has an email and a shipping address. A **seller** has an email and a shop name. In code, a `Customer` *is a* `User` and a `Seller` *is a* `User`, but a table has no *extends*. In class you met three ways to store such a family in tables, and the safest start is **joined tables**: one table `users` holds what every user has (`id`, `email` and a word `kind`), and each kind has its own small table with its own columns. The `id` of a child row is the **same id** as the row of the same user in `users`. In this problem you write both sides, in plain Python with **SQLite** (a small database that lives inside Python, so there is nothing to install and nothing to start): **saving** one user takes two rows, and **reading back** uses the word in `kind` to build the right class, and gives one clear error for a word that nobody knows. You need about 8 lines of code, in 2 small tasks. There is no server, no internet and no key.

## Requirements
### The three tables (already made by `create_tables`)
| Table | Columns | What it holds |
|---|---|---|
| `users` | `id`, `email`, `kind` | one row for every user, whatever its kind |
| `customer` | `id` (also a link to `users.id`), `shipping_address` | one row for every customer |
| `seller` | `id` (also a link to `users.id`), `shop_name` | one row for every seller |

### The classes (already written)
| Class | Fields, in this order | The word in `kind` |
|---|---|---|
| `Customer` | `id`, `email`, `shipping_address` | `"customer"` |
| `Seller` | `id`, `email`, `shop_name` | `"seller"` |

Each object knows its word: `user.kind` gives `"customer"` for a `Customer`, and `"seller"` for a `Seller`.

### What `save(conn, user)` does (Task 1)
It saves one `Customer` or one `Seller` in **two rows**:
| Step | The row | Written already? |
|---|---|---|
| 1 | `users`: (`id`, `email`, `kind`) | **yes** (the first line of `save`) |
| 2 | for a customer: `customer`: (`id`, `shipping_address`). For a seller: `seller`: (`id`, `shop_name`) | **no** (Task 1) |

The row of step 2 gets the **same `id`** as the row of step 1. A seller must not get a row in `customer`, and a customer must not get a row in `seller`.

### What `load_all(conn)` does (Task 2)
It gives back a list of all users, **sorted by email**, and each one is an object of its **real class**. The SELECT that reads the three tables is already written (`SELECT_ALL`).
| The word in `kind` | What goes in the list |
|---|---|
| `customer` | `Customer(id, email, shipping_address)` (written already) |
| `seller` | `Seller(id, email, shop_name)` |
| any other word, for example `admin` | nothing: `load_all` stops with `UnknownKind` and the text `kind 'admin' does not match any of: 'customer', 'seller'` (with the real word in the place of `admin`) |

### The rules
- **The same id in both rows.** The child row can only be found again through the id of its user.
- **The word in `kind` decides the class.** Do not guess the class from the box that is empty. A row of an unknown kind must give the error, whatever else the row holds.
- **One clear error.** An unknown word gives `UnknownKind` with that text, and not a half-built list or another kind of error.
- **Sorted by email** (the SELECT already does it: keep the order).

To achieve these requirements we need to do 2 things:
- **Task 1:** finish `save`: the row of the child.
- **Task 2:** finish `load_all`: the seller, and the unknown word.

## Instructions
1. Open `app/family.py`. We need to finish two functions: `save` has one TODO note (`TODO 1`) and `load_all` has one (`TODO 2`). The first lines of each function are already written, and they are your examples.
2. **Task 1** is `TODO 1`: the second row of `save`. **Task 2** is `TODO 2`: the seller and the unknown word in `load_all`.
3. Do not modify the classes, `UnknownKind`, `CREATE_TABLES`, `SELECT_ALL`, `create_tables`, the names of the two functions and their parameters, or the lines that are already written. Feel free to add new functions if required.
4. Run `python try_it.py` from this folder (the one that contains `app/` and `try_it.py`) to see what your code does. When both tasks are finished, you should see exactly this:
   ```
   Task 1: save writes two rows for each user
     rows in users                           : 3
     rows in customer                        : 2
     rows in seller                          : 1
     customer rows with their user           : 2
     seller rows with their user             : 1
   Task 2: load_all builds the class from the word in `kind`
     1                                       : Customer asha@shopnest.com
     2                                       : Customer mina@shopnest.com
     3                                       : Seller ravi@shopnest.com
     same objects as the ones saved          : True
   A user with a kind that nobody knows
     load_all                                : UnknownKind -> kind 'admin' does not match any of: 'customer', 'seller'
   ```
   Before you start, `try_it.py` already runs: `users` has 3 rows, `customer` and `seller` have none, and only the customers come back.
5. Your code will be checked with the test file `tests/test_family.py`. It checks the cases in the Requirements above and the rules. While you write your code, use `python try_it.py` (instruction 4) to check your work.
6. You do not need to install anything, and you do not need a server, the internet or a key. Only Python's standard library is used (`sqlite3` is a part of it). It works with Python 3.8 or newer.
7. Hints (all of these use ideas from class):
   - **Task 1 (TODO 1).** `conn.execute("INSERT INTO table (a, b) VALUES (?, ?)", (x, y))` puts one row in a table. A `Customer` has `user.shipping_address`, and a `Seller` has `user.shop_name`:
     ```python
     if user.kind == "customer":
         conn.execute("INSERT INTO customer (id, shipping_address) VALUES (?, ?)", (user.id, user.shipping_address))
     elif user.kind == "seller":
         conn.execute("INSERT INTO seller (id, shop_name) VALUES (?, ?)", (user.id, user.shop_name))
     ```
   - **Task 2 (TODO 2).** The loop already gives you five names for each row: `user_id, email, kind, shipping_address, shop_name`. Continue the `if` that is already there with `elif` and `else`. `raise UnknownKind("text")` stops the function with that text. An f-string such as `f"kind {kind!r} ..."` puts the real word in the text, with quotes around it:
     ```python
     elif kind == "seller":
         users.append(Seller(user_id, email, shop_name))
     else:
         raise UnknownKind(f"kind {kind!r} does not match any of: 'customer', 'seller'")
     ```
   - **If something looks wrong.** If `rows in seller` is `0` after the saves, the seller branch is missing in `save`. If `save stopped ... -> IntegrityError: FOREIGN KEY constraint failed`, the second row has another id than the first one: use `user.id` for both. If `same objects as the ones saved` is `False`, a seller is missing or has the wrong fields in `load_all`. If the last line says `no error, it gave 4 users`, the unknown word did not stop `load_all`: the last branch must `raise`. If it says `something is wrong -> ValueError`, raise `UnknownKind` and not `ValueError`. If the text is different from the one in this README, copy it exactly.
