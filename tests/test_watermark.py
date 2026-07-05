from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_info_pages() -> None:
    for path in ["/privacy", "/terms", "/security"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


def test_rejects_non_pdf_upload() -> None:
    response = client.post(
        "/api/remove",
        files=[("files", ("note.txt", b"hello", "text/plain"))],
    )
    assert response.status_code == 400
