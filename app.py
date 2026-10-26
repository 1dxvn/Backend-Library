import json
import os

from flask import Flask, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

SAMPLE_BOOKS = [
    {"isbn": "9780262033848", "title": "Introduction to Algorithms", "author": "Thomas H. Cormen"},
    {"isbn": "9780132350884", "title": "Clean Code", "author": "Robert C. Martin"},
    {"isbn": "9780451524935", "title": "1984", "author": "George Orwell"},
    {"isbn": "9780060883287", "title": "One Hundred Years of Solitude", "author": "Gabriel Garcia Marquez"},
    {"isbn": "9780141439518", "title": "Pride and Prejudice", "author": "Jane Austen"},
    {"isbn": "9780307474728", "title": "Love in the Time of Cholera", "author": "Gabriel Garcia Marquez"},
    {"isbn": "9780486282114", "title": "Frankenstein", "author": "Mary Shelley"},
    {"isbn": "9780142437230", "title": "Don Quixote", "author": "Miguel de Cervantes"},
    {"isbn": "9780743273565", "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
]


class Book:
    def __init__(self, isbn, title, author):
        self.isbn = isbn
        self.title = title
        self.author = author

    def to_dict(self):
        return {"isbn": self.isbn, "title": self.title, "author": self.author}

    @classmethod
    def from_dict(cls, data):
        return cls(data["isbn"], data["title"], data["author"])


class BSTNode:
    def __init__(self, book):
        self.book = book
        self.left = None
        self.right = None

    def is_leaf(self):
        return self.left is None and self.right is None

    def has_two_children(self):
        return self.left is not None and self.right is not None


class LibraryBST:
    def __init__(self):
        self.root = None
        self.size = 0

    def insert(self, book):
        new_node = BSTNode(book)
        if self.root is None:
            self.root = new_node
            self.size += 1
            return True
        current = self.root
        while True:
            if book.isbn == current.book.isbn:
                return False
            if book.isbn < current.book.isbn:
                if current.left is None:
                    current.left = new_node
                    break
                current = current.left
            else:
                if current.right is None:
                    current.right = new_node
                    break
                current = current.right
        self.size += 1
        return True

    def search(self, isbn):
        comparisons = 0
        current = self.root
        while current is not None:
            comparisons += 1
            if isbn == current.book.isbn:
                return current.book, comparisons
            current = current.left if isbn < current.book.isbn else current.right
        return None, comparisons

    def delete(self, isbn):
        parent, node = self._find_with_parent(isbn)
        if node is None:
            return False
        if node.is_leaf():
            self._replace_child(parent, node, None)
        elif node.has_two_children():
            self._delete_with_successor(node)
        else:
            child = node.left if node.left is not None else node.right
            self._replace_child(parent, node, child)
        self.size -= 1
        return True

    def in_order(self):
        books = []
        stack = []
        current = self.root
        while stack or current is not None:
            while current is not None:
                stack.append(current)
                current = current.left
            current = stack.pop()
            books.append(current.book)
            current = current.right
        return books

    def pre_order(self):
        books = []
        stack = [self.root] if self.root else []
        while stack:
            node = stack.pop()
            books.append(node.book)
            if node.right is not None:
                stack.append(node.right)
            if node.left is not None:
                stack.append(node.left)
        return books

    def height(self):
        return self._height(self.root)

    def serialize(self):
        return self._serialize(self.root)

    def _find_with_parent(self, isbn):
        parent = None
        current = self.root
        while current is not None and current.book.isbn != isbn:
            parent = current
            current = current.left if isbn < current.book.isbn else current.right
        return parent, current

    def _replace_child(self, parent, old_child, new_child):
        if parent is None:
            self.root = new_child
        elif parent.left is old_child:
            parent.left = new_child
        else:
            parent.right = new_child

    def _delete_with_successor(self, node):
        successor_parent = node
        successor = node.right
        while successor.left is not None:
            successor_parent = successor
            successor = successor.left
        node.book = successor.book
        self._replace_child(successor_parent, successor, successor.right)

    def _height(self, node):
        if node is None:
            return 0
        return 1 + max(self._height(node.left), self._height(node.right))

    def _serialize(self, node):
        if node is None:
            return None
        data = node.book.to_dict()
        data["left"] = self._serialize(node.left)
        data["right"] = self._serialize(node.right)
        return data


class BookRepository:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        if not os.path.exists(self.file_path):
            return [Book.from_dict(item) for item in SAMPLE_BOOKS]
        with open(self.file_path, "r", encoding="utf-8") as file:
            return [Book.from_dict(item) for item in json.load(file)]

    def save(self, books):
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump([book.to_dict() for book in books], file, indent=2, ensure_ascii=False)


class ValidationError(Exception):
    pass


class LibraryService:
    def __init__(self, repository):
        self.repository = repository
        self.tree = LibraryBST()
        for book in self.repository.load():
            self.tree.insert(book)
        self._persist()

    def list_books(self):
        return [book.to_dict() for book in self.tree.in_order()]

    def find_book(self, isbn):
        return self.tree.search(self.normalize_isbn(isbn))

    def add_book(self, payload):
        book = self._build_book(payload)
        if not self.tree.insert(book):
            return None
        self._persist()
        return book

    def remove_book(self, isbn):
        removed = self.tree.delete(self.normalize_isbn(isbn))
        if removed:
            self._persist()
        return removed

    def search_by_text(self, query):
        term = str(query or "").strip().lower()
        books = self.tree.in_order()
        if not term:
            return [book.to_dict() for book in books]
        return [
            book.to_dict()
            for book in books
            if term in book.title.lower() or term in book.author.lower()
        ]

    def tree_snapshot(self):
        return {
            "root": self.tree.serialize(),
            "size": self.tree.size,
            "height": self.tree.height(),
        }

    @staticmethod
    def normalize_isbn(value):
        return str(value or "").replace("-", "").replace(" ", "").strip().upper()

    def _build_book(self, payload):
        if not isinstance(payload, dict):
            raise ValidationError("Request body must be a JSON object.")
        isbn = self.normalize_isbn(payload.get("isbn"))
        title = str(payload.get("title") or "").strip()
        author = str(payload.get("author") or "").strip()
        missing = [name for name, value in (("isbn", isbn), ("title", title), ("author", author)) if not value]
        if missing:
            raise ValidationError("Missing required fields: " + ", ".join(missing) + ".")
        if not self._is_valid_isbn(isbn):
            raise ValidationError("ISBN must have 10 or 13 digits (ISBN-10 may end with X).")
        return Book(isbn, title, author)

    @staticmethod
    def _is_valid_isbn(isbn):
        if len(isbn) == 13:
            return isbn.isdigit()
        if len(isbn) == 10:
            return isbn[:9].isdigit() and (isbn[9].isdigit() or isbn[9] == "X")
        return False

    def _persist(self):
        self.repository.save(self.tree.pre_order())


ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")

app = Flask(__name__)
library = LibraryService(BookRepository(DATA_FILE))


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/books", methods=["GET"])
def get_books():
    return jsonify(library.list_books())


@app.route("/api/books/search", methods=["GET"])
def search_books():
    return jsonify(library.search_by_text(request.args.get("q", "")))


@app.route("/api/books/<isbn>", methods=["GET"])
def get_book(isbn):
    book, comparisons = library.find_book(isbn)
    if book is None:
        return jsonify({"error": "Book not found.", "comparisons": comparisons}), 404
    return jsonify({"book": book.to_dict(), "comparisons": comparisons})


@app.route("/api/books", methods=["POST"])
def create_book():
    try:
        book = library.add_book(request.get_json(silent=True))
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    if book is None:
        return jsonify({"error": "A book with this ISBN already exists."}), 409
    return jsonify(book.to_dict()), 201


@app.route("/api/books/<isbn>", methods=["DELETE"])
def delete_book(isbn):
    if not library.remove_book(isbn):
        return jsonify({"error": "Book not found."}), 404
    return jsonify({"deleted": library.normalize_isbn(isbn)})


@app.route("/api/tree", methods=["GET"])
def get_tree():
    return jsonify(library.tree_snapshot())


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5050)), debug=False)
