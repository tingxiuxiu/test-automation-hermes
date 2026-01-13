from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Protocol, overload

from ..models.ai import OCRItem
from ..models.component import Box


class AIProtocol(Protocol):
    @overload
    def corp_image(
        self, image: Path | bytes, box: Box, save: Literal[True]
    ) -> Path: ...

    @overload
    def corp_image(
        self, image: Path | bytes, box: Box, save: Literal[False]
    ) -> bytes: ...

    def corp_image(self, image: Path | bytes, box: Box, save: bool) -> Path | bytes: ...

    def ocr(
        self, image: Path, target: str | None = None, threshold: float = 0.95
    ) -> Sequence[OCRItem]: ...

    def locator(
        self,
        target: Path,
        resource: Path | None = None,
        box: Box | None = None,
        threshold: float = 0.95,
    ) -> Box | None: ...

    def locators(
        self,
        target: Path,
        resource: Path | None = None,
        box: Box | None = None,
        threshold: float = 0.95,
    ) -> Sequence[Box]: ...
