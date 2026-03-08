import time
import httpx

from typing import overload, Literal
from loguru import logger

from ..models.component import Point


class PortalContent:
    AUTH_TOKEN = "content://com.hermes.portal.provider/auth-token"
    ENABLE_SERVICE = "content://com.hermes.portal.provider/start-service"
    DISABLE_SERVICE = "content://com.hermes.portal.provider/stop-service"


class PortalHTTP:
    PING = "/health"
    STATE_ID = "/stateId"
    DISPLAYS = "/displays/{}"
    HIERARCHY = DISPLAYS + "/hierarchy"
    CAPTURE = DISPLAYS + "/capture"
    ACTION = DISPLAYS + "/actions"
    TAP = ACTION + "/tap"
    LONG_PRESS = ACTION + "/longPress"
    SWIPE = ACTION + "/swipe"
    ZOOM = ACTION + "/zoom"
    CUSTOM_ZOOM = ACTION + "/customZoom"
    INPUT = DISPLAYS + "/input"
    INPUT_TEXT = INPUT + "/text"
    CLEAR_INPUT = INPUT + "/clear"
    SEARCH = DISPLAYS + "/search"
    NOTIFICATIONS = "/notification"
    TRIGGER_NOTIFICATION = NOTIFICATIONS + "/trigger"

    def __init__(self):
        self.base_url = "http://127.0.0.1:8200/v1"
        self._client = httpx.Client(timeout=3, base_url=self.base_url)

    def set_port(self, port: int):
        """
        设置Portal服务器端口

        :param port: Portal服务器端口号
        """
        self.base_url = f"http://127.0.0.1:{port}/v1"
        self._client.close()
        self._client = httpx.Client(timeout=3, base_url=self.base_url)

    def _check_response(self, response: httpx.Response):
        response.raise_for_status()
        return response.json()

    def ping(self) -> bool:
        """
        检查Portal服务器是否响应

        :return: 如果服务器响应则返回True，否则返回False
        """
        for i in range(5):
            try:
                response = self._client.get(self.PING)
            except Exception as e:
                logger.warning(f"Ping portal server failed: {e}, retry {i}")
                time.sleep(1)
                continue
            if response.status_code == 200:
                return True
            time.sleep(1)
        return False

    def get_state_id(self) -> int:
        """
        获取当前状态ID

        :return: 当前状态ID整数
        """
        response = self._client.get(self.STATE_ID)
        response_json = self._check_response(response)
        return response_json["result"]

    def get_disaplys(self, display_id: int):
        """
        获取指定display_id的信息

        :param display_id: 显示ID
        :return: {
            "displayId": 0,
            "stateId": 0,
            "hasChanged": True,
        }
        """
        response = self._client.get(self.DISPLAYS.format(display_id))
        response_json = self._check_response(response)
        return response_json["result"]

    @overload
    def get_hierarchy(self, display_id: int, format: Literal["xml"]) -> str: ...

    @overload
    def get_hierarchy(self, display_id: int, format: Literal["json"]) -> dict: ...

    def get_hierarchy(self, display_id: int, format: Literal["xml", "json"] = "xml"):
        """
        获取指定display_id的层级结构

        :param display_id: 显示ID
        :param format: 层级结构格式，默认xml, 可选json
        :return: 层级结构JSON字符串或XML字符串
        """
        params = {"format": format}
        response = self._client.get(self.HIERARCHY.format(display_id), params=params)
        if format == "xml":
            return response.content.decode("utf-8")
        else:
            response_json = self._check_response(response)
            if response_json["success"]:
                return response_json["result"]
            else:
                raise ValueError(response_json["message"])

    def get_capture(self, display_id: int) -> bytes:
        """
        获取指定display_id的截图

        :param display_id: 显示ID
        :return: 截图字节流
        """
        response = self._client.get(self.CAPTURE.format(display_id))
        return response.content

    def action_tap(self, display_id: int, point: Point, duration: int = 100):
        """
        在指定display_id的坐标(x, y)点击

        :param display_id: 显示ID
        :param point: 点击坐标
        :param duration: 点击时间，默认100ms
        """
        params = {"x": point.x, "y": point.y, "duration": duration}
        response = self._client.get(self.TAP.format(display_id), params=params)
        response.raise_for_status()

    def action_long_press(self, display_id: int, point: Point, duration: int = 1000):
        """
        在指定display_id的坐标(x, y)长按

        :param display_id: 显示ID
        :param point: 长按坐标
        :param duration: 长按时间，默认1000ms
        """
        params = {"x": point.x, "y": point.y, "duration": duration}
        response = self._client.get(self.LONG_PRESS.format(display_id), params=params)
        response.raise_for_status()

    def action_swipe(
        self,
        display_id: int,
        start: Point,
        end: Point,
        duration: int = 500,
    ):
        """
        在指定display_id的坐标(x1, y1)滑动到(x2, y2)

        :param display_id: 显示ID
        :param start: 滑动起始坐标
        :param end: 滑动结束坐标
        :param duration: 滑动时间，默认500ms
        """
        params = {
            "startX": start.x,
            "startY": start.y,
            "endX": end.x,
            "endY": end.y,
            "duration": duration,
        }
        response = self._client.get(self.SWIPE.format(display_id), params=params)
        response.raise_for_status()

    def action_zoom(self, display_id: int, action_type: str = "in"):
        """
        在指定display_id的坐标(x1, y1)缩放到(x2, y2)

        :param display_id: 显示ID
        :param action_type: 缩放类型，默认in，可选out
        :param duration: 缩放时间，默认1000ms
        """
        params = {"type": action_type}
        response = self._client.get(self.ZOOM.format(display_id), params=params)
        response.raise_for_status()

    def action_custom_zoom(
        self,
        display_id: int,
        start1: Point,
        end1: Point,
        start2: Point,
        end2: Point,
        duration: int = 500,
    ):
        """
        在指定display_id的坐标(x1, y1)缩放到(x2, y2)

        :param display_id: 显示ID
        :param start1: 缩放起始坐标1
        :param end1: 缩放结束坐标1
        :param start2: 缩放起始坐标2
        :param end2: 缩放结束坐标2
        :param duration: 缩放时间，默认500ms
        """
        data = {
            "displayId": display_id,
            "finger1": {
                "start": {"x": start1.x, "y": start1.y},
                "end": {"x": end1.x, "y": end1.y},
            },
            "finger2": {
                "start": {"x": start2.x, "y": start2.y},
                "end": {"x": end2.x, "y": end2.y},
            },
            "duration": duration,
        }
        response = self._client.post(self.ZOOM.format(display_id), json=data)
        response.raise_for_status()

    def action_input_text(self, display_id: int, content: str):
        """
        在指定display_id输入文本

        :param display_id: 显示ID
        :param content: 输入文本
        """
        data = {"text": content}
        check = False
        for _ in range(3):
            response = self._client.post(self.INPUT_TEXT.format(display_id), json=data)
            if response.status_code == 200:
                response_json = response.json()
                if response_json["success"]:
                    check = True
                    break
                logger.warning(f"Input text failed: {response_json}, retry {_}")
            time.sleep(0.5)
        assert check, "Input text failed"

    def action_clear_text(self, display_id: int):
        """
        在指定display_id清除文本

        :param display_id: 显示ID
        """
        check = False
        for _ in range(3):
            response = self._client.get(self.CLEAR_INPUT.format(display_id))
            if response.status_code == 200:
                response_json = response.json()
                if response_json["success"]:
                    check = True
                    break
                logger.warning(f"Clear text failed: {response_json}, retry {_}")
            time.sleep(0.5)
        assert check, "Clear text failed"

    def action_search(
        self,
        display_id: int,
        resource_id: str | None = None,
        class_name: str | None = None,
        text: str | None = None,
        description: str | None = None,
        container_id: int | None = None,
        direction: str = "down",
        max_retries: int = 5,
    ):
        """
        在指定display_id搜索文本

        :param display_id: 显示ID
        :param resource_id: 资源ID
        :param class_name: 类名
        :param text: 文本
        :param description: 描述
        :param container_id: 容器ID
        :param direction: 搜索方向，默认down，可选up
        :param max_retries: 最大重试次数，默认5次
        """
        data = {
            "displayId": display_id,
            "resourceId": resource_id,
            "className": class_name,
            "text": text,
            "description": description,
            "containerResourceId": container_id,
            "direction": direction,
            "maxRetries": max_retries,
        }
        response = self._client.post(self.SEARCH.format(display_id), json=data)
        response.raise_for_status()

    def get_notifications(self, display_id: int):
        """
        获取指定display_id的通知

        :param display_id: 显示ID
        """
        response = self._client.get(self.NOTIFICATIONS.format(display_id))
        response.raise_for_status()
        return response.json()["result"]

    def trigger_notification(
        self, display_id: int, title: str, content: str, duration: int = 5000
    ):
        """
        触发指定display_id的通知

        :param display_id: 显示ID
        :param title: 通知标题
        :param content: 通知内容
        :param duration: 通知显示时间，默认5000ms
        """
        params = {"title": title, "content": content, "duration": duration}
        response = self._client.get(
            self.TRIGGER_NOTIFICATION.format(display_id), params=params
        )
        response.raise_for_status()
        return response.json()["result"]
