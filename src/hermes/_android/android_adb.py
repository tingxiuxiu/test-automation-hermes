import re
import threading
import time
from collections import deque
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen
from typing import Literal

from loguru import logger

from .._core import config
from .._protocol.debug_bridge_protocol import DebugBridgeProtocol
from ..models.common import PopenOutput
from ..models.component import Box, Point, Size
from ..models.logcat import LogcatItem


class AndroidADB(DebugBridgeProtocol):
    def __init__(self, serial: str, capture_logcat: bool = False):
        self._serial = serial
        self._capture_logcat = capture_logcat
        self._adb = f"adb -s {self._serial} "
        self._stop_event = threading.Event()
        self._logcat_queue = deque(maxlen=1000)
        self._screen_size: Size | None = None
        if capture_logcat:
            threading.Thread(target=self._logcat_thread, daemon=True).start()

    def _adb_popen(
        self,
        command: str,
        timeout: int,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> PopenOutput:
        _time = int(timeout / 1000)
        _command = self._adb + command
        logger.info(f"Run command: {_command}")
        _cmd_args = _command.split(" ")
        process = Popen(_cmd_args, stdout=PIPE, stderr=PIPE, cwd=cwd, env=env)
        out, err = process.communicate(timeout=_time)
        return PopenOutput(stdout=out, stderr=err)

    def cmd(
        self,
        command: str,
        timeout: int = 30000,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> PopenOutput:
        _command = self._adb + command
        return self._adb_popen(_command, timeout, cwd, env)

    def shell(
        self,
        command: str,
        timeout: int = 30000,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> PopenOutput:
        _command = self._adb + "shell " + command
        return self._adb_popen(_command, timeout, cwd, env)

    def clear_logcat(self):
        self.cmd("logcat -b all -c")

    def stop_logcat(self):
        self._stop_event.set()

    def _logcat_thread(self):
        cmd = self._adb + "logcat -v year -D"
        logger.info(f"Start logcat thread: {cmd}")
        while not self._stop_event.is_set():
            process = Popen(cmd.split(), stdout=PIPE, stderr=STDOUT)
            while not self._stop_event.is_set():
                if process.stdout:
                    output = process.stdout.readline()
                    if output == b"" and process.poll() is not None:
                        break
                    if output:
                        line = output.strip().decode("utf-8", errors="replace")
                        try:
                            timestamp = line[:23]
                            # Python's strptime %f requires microseconds (6 digits), logcat has milliseconds (3 digits)
                            dt = datetime.strptime(
                                timestamp + "000", "%Y-%m-%d %H:%M:%S.%f"
                            )
                            self._logcat_queue.append(
                                LogcatItem(timestamp=dt, message=line)
                            )
                        except ValueError:
                            logger.error(f"Invalid logcat line: {line}")
                else:
                    time.sleep(0.1)
                if process.poll() is not None:
                    break
            try:
                process.kill()
            except Exception as e:
                logger.error(f"Failed to kill logcat process: {e}")

    def reboot(self, wait_for_boot_completed: bool = True, timeout: int = 60000):
        self.cmd("reboot")
        if wait_for_boot_completed:
            self.wait_for_boot_completed(timeout)

    def wait_for_boot_completed(self, timeout: int = 60000) -> bool:
        _time = int(timeout / 1000)
        started_at = time.time()
        deadline = started_at + _time
        n = 1
        while time.time() < deadline:
            try:
                output = self.shell("getprop sys.boot_completed")
                if "1" in output.get_stdout():
                    return True
            except Exception as e:
                logger.debug(f"Failed to get boot completed: {e}")
            logger.debug(f"Waiting for boot completed...{n}")
            time.sleep(0.5)
            n += 1
        return False

    def get_devices(self) -> list[str]:
        output = self.cmd("devices -l")
        return output.get_stdout_list()

    def screenshot(self, path: Path | None, display_id: str | None = None) -> Path:
        if path:
            _path = path
        else:
            _path = (
                config.CACHE_DIR
                / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}-screenshot.png"
            )
        if display_id:
            self.cmd(f"exec-out screencap -d {display_id} -p {_path}")
        else:
            self.cmd(f"exec-out screencap -p {_path}")
        return _path

    def click_back(self):
        self.cmd("input keyevent 4")

    def click_enter(self):
        self.cmd("input keyevent 66")

    def click_home(self):
        self.cmd("input keyevent 3")

    def click_recent_task(self):
        self.cmd("input keyevent 187")

    def get_screen_size(self, refresh: bool = False) -> Size:
        if not refresh and self._screen_size:
            return self._screen_size
        else:
            output = self.shell("wm size")
            search = re.search(r"\d+x(\d+)", output.get_stdout())
            if search:
                _s = [int(x) for x in search.group().split("x")]
                self._screen_size = Size(width=_s[0], height=_s[1])
                return self._screen_size
            raise ValueError("Failed to get screen size")

    def tap(self, x: int, y: int, offset_x: int = 0, offset_y: int = 0):
        self.shell(f"input tap {x + offset_x} {y + offset_y}")

    def long_press(
        self, x: int, y: int, offset_x: int = 0, offset_y: int = 0, duration: int = 2000
    ):
        self.shell(
            f"input swipe {x + offset_x} {y + offset_y} {x + offset_x} {y + offset_y} {duration}"
        )

    def drag_and_drop(self, start: Point, end: Point, duration: int = 1000):
        self.shell(f"input draganddrop {start.x} {start.y} {end.x} {end.y} {duration}")

    def swipe(
        self,
        start: Point,
        end: Point,
        duration: int = 500,
        repeat: int = 1,
        wait_render: int = 200,
    ):
        for _ in range(repeat):
            self.shell(f"input swipe {start.x} {start.y} {end.x} {end.y} {duration}")
            time.sleep(wait_render / 1000)

    def swipe_ext(
        self,
        direction: Literal["up", "down", "right", "left"],
        *,
        scale: float = 0.9,
        box: Box | None = None,
        duration: int = 500,
        repeat: int = 1,
        wait_render: int = 200,
    ):
        if box is None:
            box = Box(
                left=0,
                top=0,
                right=self.get_screen_size().width,
                bottom=self.get_screen_size().height,
                width=self.get_screen_size().width,
                height=self.get_screen_size().height,
            )
        center_x = int(box.left + box.width / 2)
        center_y = int(box.top + box.height / 2)
        offset_x = int(center_x * scale)
        offset_y = int(center_y * scale)
        if direction == "up":
            start = Point(x=center_x, y=offset_y)
            end = Point(x=center_x, y=int(box.height * 0.1))
        elif direction == "down":
            start = Point(x=center_x, y=int(box.height * 0.1))
            end = Point(x=center_x, y=offset_y)
        elif direction == "right":
            start = Point(x=int(box.width * 0.1), y=center_y)
            end = Point(x=offset_x, y=center_y)
        elif direction == "left":
            start = Point(x=offset_x, y=center_y)
            end = Point(x=int(box.width * 0.1), y=center_y)
        self.swipe(start, end, duration, repeat, wait_render)

    def get_datetime(self) -> str:
        output = self.shell("date '+%Y-%m-%d\\ %H:%M:%S.%s'")
        return output.get_stdout().strip()

    def pull(self, remote_path: str, local_path: Path):
        self.cmd(f"pull {remote_path} {local_path}")

    def push(self, remote_path: str, local_path: Path):
        self.cmd(f"push {local_path} {remote_path}")

    def install(self, apk_path: Path):
        self.cmd(f"install {apk_path}")

    def uninstall(self, package_name: str):
        self.cmd(f"uninstall {package_name}")

    def start_app(self, package_name: str, activity_name: str | None = None):
        if activity_name:
            self.shell(f"am start -n {package_name}/{activity_name}")
        else:
            self.shell(f"am start -n {package_name}")

    def stop_app(self, package_name: str):
        self.shell(f"am force-stop {package_name}")

    def get_app_info(self, package_name: str) -> str:
        output = self.shell(f"dumpsys package {package_name}")
        return output.get_stdout()

    def get_app_version(self, package_name: str):
        output = self.shell(f"dumpsys package {package_name}")
        search = re.search(r"versionName=([\d\.]+)", output.get_stdout())
        if search:
            return search.group(1)
        return None
