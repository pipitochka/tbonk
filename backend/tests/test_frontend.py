"""The backend must keep serving the browser UI after source moves."""
import pytest

from backend.app import app


@pytest.mark.parametrize(
    "url, content_type, marker",
    [
        ("/", "text/html", b"<title>Tbonk Tasks</title>"),
        ("/styles.css", "text/css", b".container"),
        ("/app.js", "javascript", b"/api/tasks"),
    ],
)
def test_frontend_assets_are_served(url, content_type, marker):
    response = app.test_client().get(url)
    assert response.status_code == 200
    assert content_type in response.content_type
    assert marker in response.data
