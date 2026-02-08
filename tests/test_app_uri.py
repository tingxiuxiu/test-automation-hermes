import subprocess
from _operator import sub
import httpx
import subprocess


class TestAppUri:
    headers = {
        "Authorization": "Bearer cd25430e-fe25-4e29-93a1-4afd15ebe37d",
    }

    def test_app_uri(self):
        token = subprocess.run("adb shell uri ")