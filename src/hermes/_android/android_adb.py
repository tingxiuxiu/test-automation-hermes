import subprocess
import re
import threading
import time
import subprocess
from subprocess import CompletedProcess

from collections import deque
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen
from typing import Literal

from loguru import logger

from .._core import config
from ..protocol.debug_bridge_protocol import DebugBridgeProtocol
from ..models.component import Bounds, Point, Size
from ..models.logcat import LogcatItem


class AndroidADB(DebugBridgeProtocol):
    """
    AndroidADB class for interacting with Android devices via ADB (Android Debug Bridge).

    This class provides methods to communicate with Android devices using ADB commands,
    including device control, app management, input simulation, and logcat monitoring.

    Attributes:
        _serial: str - The serial number of the Android device
        _adb: str - The ADB command prefix with serial number
        _capture_logcat: bool - Whether to capture logcat output
        _stop_event: threading.Event - Event to stop logcat thread
        _logcat_queue: deque - Queue to store logcat items
        _window_size: Size | None - Cached window size of the device
    """

    def __init__(
        self, serial: str, android_home: str | None = None, capture_logcat: bool = False
    ):
        """
        Initialize AndroidADB instance.

        Args:
            serial: str - The serial number of the Android device
            android_home: str | None - Path to Android SDK home directory
            capture_logcat: bool - Whether to start capturing logcat output
        """
        self._serial = serial
        self._capture_logcat = capture_logcat
        if not android_home:
            self._adb = f"adb -s {self._serial} "
        else:
            if android_home.endswith("/"):
                android_home = android_home[:-1]
            self._adb = f"{android_home}/platform-tools/adb -s {self._serial} "
        self._stop_event = threading.Event()
        self._logcat_queue = deque(maxlen=1000)
        self._window_size: Size | None = None
        if capture_logcat:
            threading.Thread(target=self._logcat_thread, daemon=True).start()

    def _adb_popen(
        self,
        command: str,
        timeout: int,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> CompletedProcess:
        """
        Execute an ADB command and return the result.

        Args:
            command: str - The command to execute
            timeout: int - Timeout in milliseconds
            cwd: Path | None - Working directory for the command
            env: Mapping[str, str] | None - Environment variables for the command

        Returns:
            CompletedProcess - The result of the command execution
        """
        _time = int(timeout / 1000)
        logger.info(f"Run command: {command}")
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True,
            timeout=_time,
            cwd=cwd,
            env=env,
        )

    def cmd(
        self,
        command: str,
        timeout: int = 30000,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> CompletedProcess:
        """
        Execute an ADB command.

        Args:
            command: str - The ADB command to execute
            timeout: int - Timeout in milliseconds (default: 30000)
            cwd: Path | None - Working directory for the command
            env: Mapping[str, str] | None - Environment variables for the command

        Returns:
            CompletedProcess - The result of the command execution
        """
        _command = self._adb + command
        return self._adb_popen(_command, timeout, cwd, env)

    def shell(
        self,
        command: str,
        timeout: int = 30000,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> CompletedProcess:
        """
        Execute a shell command on the device.

        Args:
            command: str - The shell command to execute
            timeout: int - Timeout in milliseconds (default: 30000)
            cwd: Path | None - Working directory for the command
            env: Mapping[str, str] | None - Environment variables for the command

        Returns:
            CompletedProcess - The result of the command execution
        """
        _command = self._adb + "shell " + command
        return self._adb_popen(_command, timeout, cwd, env)

    def clear_logcat(self):
        """
        Clear all logcat buffers.
        """
        self.cmd("logcat -b all -c")

    def stop_logcat(self):
        """
        Stop the logcat capture thread.
        """
        self._stop_event.set()

    def get_pid(self, package_name: str) -> int:
        """
        Get the process ID of a package.

        Args:
            package_name: str - The package name to get the PID for

        Returns:
            int - The PID of the package, or -1 if not found
        """
        completed_process = self.shell(f"pidof {package_name}")
        if completed_process.returncode != 0:
            return -1
        return int(completed_process.stdout.strip())

    def _logcat_thread(self):
        """
        Thread function to capture logcat output.

        This method runs in a separate thread and captures logcat output,
        parsing it into LogcatItem objects and storing them in a queue.
        """
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
        """
        Reboot the device and optionally wait for boot completion.

        Args:
            wait_for_boot_completed: bool - Whether to wait for boot completion
            timeout: int - Timeout in milliseconds for boot completion
        """
        self.cmd("reboot")
        if wait_for_boot_completed:
            self.wait_for_boot_completed(timeout)

    def wait_for_boot_completed(self, timeout: int = 60000) -> bool:
        """
        Wait for the device to complete booting.

        Args:
            timeout: int - Timeout in milliseconds (default: 60000)

        Returns:
            bool - True if boot completed within timeout, False otherwise
        """
        _time = int(timeout / 1000)
        started_at = time.time()
        deadline = started_at + _time
        n = 1
        while time.time() < deadline:
            try:
                output = self.shell("getprop sys.boot_completed")
                if "1" in output.stdout:
                    return True
            except Exception as e:
                logger.debug(f"Failed to get boot completed: {e}")
            logger.debug(f"Waiting for boot completed...{n}")
            time.sleep(0.5)
            n += 1
        return False

    def get_devices(self) -> list[str]:
        """
        Get list of connected devices.

        Returns:
            list[str] - List of connected devices with details
        """
        output = self.cmd("devices -l")
        return output.stdout.splitlines()[1:]

    def screenshot(self, path: Path | None, display_id: str | None = None) -> Path:
        """
        Take a screenshot of the device.

        Args:
            path: Path | None - Path to save the screenshot, or None for default path
            display_id: str | None - Display ID to capture, or None for default display

        Returns:
            Path - Path where the screenshot was saved
        """
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
        """
        Simulate back button press.
        """
        self.shell("input keyevent 4")

    def click_enter(self):
        """
        Simulate enter key press.
        """
        self.shell("input keyevent 66")

    def click_home(self):
        """
        Simulate home button press.
        """
        self.shell("input keyevent 3")

    def click_recent_task(self):
        """
        Simulate recent tasks button press.
        """
        self.shell("input keyevent 187")

    def click_menu(self):
        """
        Simulate menu button press.
        """
        self.shell("input keyevent 82")

    def click_power(self):
        """
        Simulate power button press.
        """
        self.shell("input keyevent 26")

    def get_window_size(self, refresh: bool = False) -> Size:
        """
        Get the window size of the device.

        Args:
            refresh: bool - Whether to refresh the cached window size

        Returns:
            Size - The window size of the device

        Raises:
            ValueError - If failed to get window size
        """
        if not refresh and self._window_size:
            return self._window_size
        else:
            output = self.shell("wm size")
            search = re.search(r"\d+x(\d+)", output.stdout)
            if search:
                _s = [int(x) for x in search.group().split("x")]
                self._window_size = Size(width=_s[0], height=_s[1])
                return self._window_size
            raise ValueError("Failed to get window size")

    def tap(self, x: int, y: int, offset_x: int = 0, offset_y: int = 0):
        """
        Simulate a tap at the specified coordinates.

        Args:
            x: int - X coordinate
            y: int - Y coordinate
            offset_x: int - Offset for X coordinate (default: 0)
            offset_y: int - Offset for Y coordinate (default: 0)
        """
        self.shell(f"input tap {x + offset_x} {y + offset_y}")

    def long_press(
        self, x: int, y: int, offset_x: int = 0, offset_y: int = 0, duration: int = 2000
    ):
        """
        Simulate a long press at the specified coordinates.

        Args:
            x: int - X coordinate
            y: int - Y coordinate
            offset_x: int - Offset for X coordinate (default: 0)
            offset_y: int - Offset for Y coordinate (default: 0)
            duration: int - Duration of the long press in milliseconds (default: 2000)
        """
        self.shell(
            f"input swipe {x + offset_x} {y + offset_y} {x + offset_x} {y + offset_y} {duration}"
        )

    def drag_and_drop(self, start: Point, end: Point, duration: int = 1000):
        """
        Simulate a drag and drop operation.

        Args:
            start: Point - Starting coordinates
            end: Point - Ending coordinates
            duration: int - Duration of the drag operation in milliseconds (default: 1000)
        """
        self.shell(f"input draganddrop {start.x} {start.y} {end.x} {end.y} {duration}")

    def swipe(
        self,
        start: Point,
        end: Point,
        duration: int = 500,
        repeat: int = 1,
        wait_render: int = 200,
    ):
        """
        Simulate a swipe gesture.

        Args:
            start: Point - Starting coordinates
            end: Point - Ending coordinates
            duration: int - Duration of the swipe in milliseconds (default: 500)
            repeat: int - Number of times to repeat the swipe (default: 1)
            wait_render: int - Wait time between swipes in milliseconds (default: 200)
        """
        for _ in range(repeat):
            self.shell(f"input swipe {start.x} {start.y} {end.x} {end.y} {duration}")
            time.sleep(wait_render / 1000)

    def swipe_ext(
        self,
        direction: Literal["up", "down", "right", "left"],
        *,
        scale: float = 0.9,
        bounds: Bounds | None = None,
        duration: int = 500,
        repeat: int = 1,
        wait_render: int = 200,
    ):
        """
        Simulate a swipe in a specified direction.

        Args:
            direction: Literal["up", "down", "right", "left"] - Direction of the swipe
            scale: float - Scale factor for swipe distance (default: 0.9)
            bounds: Bounds | None - Bounds within which to perform the swipe
            duration: int - Duration of the swipe in milliseconds (default: 500)
            repeat: int - Number of times to repeat the swipe (default: 1)
            wait_render: int - Wait time between swipes in milliseconds (default: 200)
        """
        if bounds is None:
            bounds = Bounds(
                left=0,
                top=0,
                right=self.get_window_size().width,
                bottom=self.get_window_size().height,
            )
        center_x = int(bounds.left + (bounds.right - bounds.left) / 2)
        center_y = int(bounds.top + (bounds.bottom - bounds.top) / 2)
        offset_x = int(center_x * scale)
        offset_y = int(center_y * scale)
        if direction == "up":
            start = Point(x=center_x, y=offset_y)
            end = Point(
                x=center_x, y=int(bounds.top + (bounds.bottom - bounds.top) * 0.1)
            )
        elif direction == "down":
            start = Point(
                x=center_x, y=int(bounds.top + (bounds.bottom - bounds.top) * 0.1)
            )
            end = Point(x=center_x, y=offset_y)
        elif direction == "right":
            start = Point(
                x=int(bounds.left + (bounds.right - bounds.left) * 0.1), y=center_y
            )
            end = Point(x=offset_x, y=center_y)
        elif direction == "left":
            start = Point(x=offset_x, y=center_y)
            end = Point(
                x=int(bounds.left + (bounds.right - bounds.left) * 0.1), y=center_y
            )
        self.swipe(start, end, duration, repeat, wait_render)

    def get_datetime(self) -> str:
        """
        Get the current date and time from the device.

        Returns:
            str - Current date and time in the format 'YYYY-MM-DD HH:MM:SS.ssssss'
        """
        output = self.shell("date '+%Y-%m-%d\\ %H:%M:%S.%s'")
        return output.stdout.strip()

    def pull(self, remote_path: str, local_path: Path):
        """
        Pull a file from the device to the local system.

        Args:
            remote_path: str - Path on the device
            local_path: Path - Path on the local system
        """
        self.cmd(f"pull {remote_path} {local_path}")

    def push(self, remote_path: str, local_path: Path):
        """
        Push a file from the local system to the device.

        Args:
            remote_path: str - Path on the device
            local_path: Path - Path on the local system
        """
        self.cmd(f"push {local_path} {remote_path}")

    def install(self, apk_path: Path):
        """
        Install an APK on the device.

        Args:
            apk_path: Path - Path to the APK file
        """
        self.cmd(f"install {apk_path}")

    def uninstall(self, package_name: str):
        """
        Uninstall a package from the device.

        Args:
            package_name: str - Name of the package to uninstall
        """
        self.cmd(f"uninstall {package_name}")

    def start_app(self, package_name: str, activity_name: str | None = None):
        """
        Start an app on the device.

        Args:
            package_name: str - Name of the package to start
            activity_name: str | None - Name of the activity to start (optional)
        """
        if activity_name:
            self.shell(f"am start -n {package_name}/{activity_name}")
        else:
            self.shell(f"am start -n {package_name}")
        time.sleep(1)

    def stop_app(self, package_name: str):
        """
        Stop an app on the device.

        Args:
            package_name: str - Name of the package to stop
        """
        self.shell(f"am force-stop {package_name}")

    def get_app_info(self, package_name: str) -> str:
        """
        Get information about an app.

        Args:
            package_name: str - Name of the package

        Returns:
            str - App information
        """
        output = self.shell(f"dumpsys package {package_name}")
        return output.stdout

    def get_app_version(self, package_name: str):
        """
        Get the version of an app.

        Args:
            package_name: str - Name of the package

        Returns:
            str | None - Version name if found, None otherwise
        """
        output = self.shell(f"dumpsys package {package_name}")
        search = re.search(r"versionName=([\d\.]+)", output.stdout)
        if search:
            return search.group(1)
        return None

    def forward_port(self, local_port: int, remote_port: int):
        """
        Forward a local port to a remote port on the device.

        Args:
            local_port: int - Local port to forward
            remote_port: int - Remote port on the device

        Raises:
            ValueError - If port forwarding fails
        """
        output = self.cmd(f"forward tcp:{local_port} tcp:{remote_port}")
        if output.returncode != 0:
            raise ValueError(f"Failed to forward port {local_port} to {remote_port}")

    def reverse_port(self, local_port: int, remote_port: int):
        """
        Reverse forward a remote port on the device to a local port.

        Args:
            local_port: int - Local port
            remote_port: int - Remote port on the device to reverse forward

        Raises:
            ValueError - If port reverse forwarding fails
        """
        output = self.cmd(f"reverse tcp:{local_port} tcp:{remote_port}")
        if output.returncode != 0:
            raise ValueError(f"Failed to reverse port {local_port} to {remote_port}")

    def remove_forward_port(self, local_port: int):
        """
        Remove a port forward.

        Args:
            local_port: int - Local port to remove forwarding for

        Raises:
            ValueError - If removing port forward fails
        """
        output = self.cmd(f"forward --remove tcp:{local_port}")
        if output.returncode != 0:
            raise ValueError(f"Failed to remove forward port {local_port}")

    def remove_all_forward_ports(self):
        """
        Remove all port forwards.

        Raises:
            ValueError - If removing all port forwards fails
        """
        output = self.cmd("forward --remove-all")
        if output.returncode != 0:
            raise ValueError("Failed to remove all forward ports")

    def get_forwarded_ports(self) -> list[int]:
        """
        Get list of forwarded ports.

        Returns:
            list[int] - List of forwarded local ports

        Raises:
            ValueError - If getting forwarded ports fails
        """
        output = self.cmd("forward --list")
        if output.returncode != 0:
            raise ValueError("Failed to get forwarded ports")
        lines = output.stdout.splitlines()
        ports = []
        for line in lines:
            search = re.search(r"tcp:(\d+)", line)
            if search:
                ports.append(int(search.group(1)))
        return ports

    def get_all_display_id(self) -> list[int]:
        """
        Get all display IDs on the device.

        Returns:
            list[int] - List of display IDs

        Raises:
            ValueError - If getting display IDs fails
        """
        output = self.shell("dumpsys display | grep mDisplayId")
        search = re.findall(r"mDisplayId=(\d+)", output.stdout)
        if search:
            return [int(id) for id in search]
        raise ValueError("Failed to get display id")

    def set_accessibility_service(self, service_name: str):
        """
        Set an accessibility service.

        Args:
            service_name: str - Name of the accessibility service
        """
        self.shell(f"settings put secure enabled_accessibility_services {service_name}")

    def check_accessibility_service(self, service_name: str) -> bool:
        """
        Check if an accessibility service is enabled.

        Args:
            service_name: str - Name of the accessibility service

        Returns:
            bool - True if the service is enabled, False otherwise
        """
        output = self.shell(f"settings get secure enabled_accessibility_services")
        return service_name in output.stdout

    def query_content(self, uri: str) -> str:
        """
        Query content provider.

        Args:
            uri: str - URI of the content provider

        Returns:
            str - Query result
        """
        output = self.shell(f"content query --uri {uri}")
        return output.stdout

    def insert_content(self, uri: str, values: dict[str, str] | None = None):
        """
        Insert content into content provider.

        Args:
            uri: str - URI of the content provider
            values: dict[str, str] | None - Values to insert

        Raises:
            ValueError - If insertion fails
        """
        cmd = f"content insert --uri {uri}"
        if values:
            for key, value in values.items():
                cmd += f" --bind {key}:{value}"
        output = self.shell(cmd)
        if output.returncode != 0:
            raise ValueError(f"Failed to insert content to {uri}")
