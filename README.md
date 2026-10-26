# Library Backend

REST API for a university library catalog. Books are stored in a Binary Search Tree keyed by ISBN and persisted to `data.json`.

## Run

```
pip install -r requirements.txt
python app.py
```

The API runs at `http://127.0.0.1:5050`.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/books` | Full catalog sorted by ISBN |
| GET | `/api/books/search?q=<text>` | Books whose title or author contains the text |
| GET | `/api/books/<isbn>` | One book or 404 |
| POST | `/api/books` | Create a book (`isbn`, `title`, `author`) |
| DELETE | `/api/books/<isbn>` | Delete a book or 404 |
| GET | `/api/tree` | Serialized tree structure |
| GET | `/api/health` | Health check |
