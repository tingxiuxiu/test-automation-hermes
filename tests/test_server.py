import httpx


headers = {
    "Authorization": "Bearer cd25430e-fe25-4e29-93a1-4afd15ebe37d",
}


class TestServer:
    def test_enable_accessibility(self):
        with httpx.Client() as client:
            response = client.post(
                "http://localhost:8080/enable_accessibility", headers=headers
            )
            assert response.status_code == 200
            assert response.json() == {"result": True}

    def test_get_token(self):
        with httpx.Client() as client:
            response = client.get("http://localhost:8080/token", headers=headers)
            assert response.status_code == 200
            assert response.json() == {"result": True}

    def test_server(self):
        with httpx.Client() as client:
            response = client.get("http://localhost:8080/ping", headers=headers)
            assert response.status_code == 200
            assert response.json() == {"message": "Hello, World!"}

    def test_get_xml(self):
        with httpx.Client() as client:
            response = client.get(
                "http://localhost:8080/a11y_tree_xml", headers=headers
            )
            print(response.text)
            assert response.status_code == 200
            assert response.json()["result"].startswith(
                '<?xml version="1.0" encoding="UTF-8"?>'
            )

    def test_get_window_status(self):
        with httpx.Client() as client:
            response = client.get(
                "http://localhost:8080/window_changed", headers=headers
            )
            assert response.status_code == 200
            assert response.json()["result"] == False

    def test_get_screenshot_bytes(self):
        with httpx.Client() as client:
            response = client.get(
                "http://localhost:8080/screenshot_bytes", headers=headers
            )
            assert response.status_code == 200
            with open("screenshot.png", "wb") as f:
                f.write(response.content)
