"""LAB 1 — add your five tests here. Do not delete the smoke tests.

A. GET /books, empty database -> HTTP 200 and []
B. GET /books/9999 -> HTTP 404, JSON code == NOT_FOUND
C. POST /books with only author -> HTTP 400, errors contains title
D. POST valid book, DELETE it, GET same id -> HTTP 404
BONUS. Validate a Book response using JSON Schema; add an unknown
       field to a *copy* of the response and assert ValidationError.

Useful imports:
    from jsonschema import validate, ValidationError
    import pytest
    from tools import get_book_schema

Do not depend on test execution order. Fixtures: client, app, sample_book.
"""
import copy

import pytest
from jsonschema import ValidationError, validate

from tools import get_book_schema


# ---------- Bước 1: 4 test bắt buộc ----------

def test_list_books_empty_db_returns_empty_array(client):
    """A. GET /books khi CSDL rỗng -> 200 và [] (không phải null)."""
    response = client.get("/books")

    assert response.status_code == 200
    body = response.get_json()
    assert body is not None
    assert body == []


def test_get_unknown_book_returns_404_not_found(client):
    """B. GET /books/9999 -> 404 + code == NOT_FOUND."""
    response = client.get("/books/9999")

    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"


def test_create_book_missing_title_returns_400(client):
    """C. POST /books thiếu title -> 400, errors có field "title"."""
    response = client.post("/books", json={"author": "J.J. Geewax"})

    assert response.status_code == 400
    body = response.get_json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "title" in [err["field"] for err in body["errors"]]


def test_deleted_book_is_gone(client):
    """D. Tạo sách, xoá, GET cùng id -> 404."""
    created = client.post(
        "/books", json={"title": "Clean Code", "author": "Robert C. Martin"}
    )
    assert created.status_code == 201
    book_id = created.get_json()["id"]

    assert client.delete(f"/books/{book_id}").status_code == 204
    assert client.get(f"/books/{book_id}").status_code == 404


# ---------- Bước 2: Bonus ----------

def test_book_response_schema_rejects_unknown_field(client):
    """BONUS. Validate response theo Book JSON Schema; field lạ phải bị chặn.

    Lưu ý: openapi.yaml cố ý khai báo year: type: string (lỗi dành cho Lab 2,
    xem README). Để không phụ thuộc vào việc sửa lỗi đó, test này dùng một bản
    sao schema đã sửa field year thành integer, phản ánh đúng hành vi thật của
    app.py/models.py hiện tại.
    """
    created = client.post(
        "/books",
        json={
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "year": 2008,
            "isbn": "9780132350884",
        },
    )
    assert created.status_code == 201
    book = created.get_json()

    schema = copy.deepcopy(get_book_schema())
    schema["properties"]["year"] = {"type": "integer", "nullable": True}

    # Response hợp lệ phải khớp schema.
    validate(book, schema)

    # Thêm field lạ vào một *bản sao* -> additionalProperties: false phải chặn.
    leaked = copy.deepcopy(book)
    leaked["password_hash"] = "should-not-be-here"
    with pytest.raises(ValidationError):
        validate(leaked, schema)