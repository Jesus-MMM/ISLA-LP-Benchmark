from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from ..core.types import DocumentModel, RenderContext


@dataclass
class RenderResult:
    """Result from a rendering operation."""
    success: bool
    output_path: Optional[str] = None
    content: Optional[str] = None
    pages: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseRenderer(ABC):
    """Abstract base class for all report renderers."""

    def __init__(self, context: Optional[RenderContext] = None):
        self.context = context or RenderContext()

    @abstractmethod
    def render(self, model: DocumentModel, output_path: str) -> RenderResult:
        """Render a document model to the target format.

        Args:
            model: Document model to render.
            output_path: Path for the output file.

        Returns:
            RenderResult with render outcome.
        """
        ...

    def pre_render(self, model: DocumentModel) -> DocumentModel:
        """Hook called before rendering begins.

        Subclasses can override to add preprocessing.

        Args:
            model: Document model.

        Returns:
            Processed document model.
        """
        return model

    def post_render(self, model: DocumentModel, result: RenderResult) -> RenderResult:
        """Hook called after rendering completes.

        Args:
            model: Document model that was rendered.
            result: Current render result.

        Returns:
            Modified render result.
        """
        return result

    def render_to_string(self, model: DocumentModel) -> str:
        """Render model to string (for formats that support it).

        Args:
            model: Document model.

        Returns:
            Rendered string content.
        """
        raise NotImplementedError("render_to_string not supported by this renderer")
