from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Protocol, overload

from ..models.ai import OCRItem
from ..models.component import Bounds


class AIProtocol(Protocol):
    @overload
    def corp_image(
        self, image: Path | bytes, box: Bounds, save: Literal[True]
    ) -> Path: ...

    @overload
    def corp_image(
        self, image: Path | bytes, box: Bounds, save: Literal[False]
    ) -> bytes: ...

    def corp_image(
        self, image: Path | bytes, box: Bounds, save: bool
    ) -> Path | bytes: ...

    def ocr(
        self, image: Path, target: str | None = None, threshold: float = 0.95
    ) -> Sequence[OCRItem]: ...

    def locator(
        self,
        target: Path,
        resource: Path | None = None,
        bounds: Bounds | None = None,
        threshold: float = 0.95,
    ) -> Bounds | None: ...

    def locators(
        self,
        target: Path,
        resource: Path | None = None,
        bounds: Bounds | None = None,
        threshold: float = 0.95,
    ) -> Sequence[Bounds]: ...
