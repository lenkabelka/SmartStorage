from dataclasses import dataclass

from PyQt6.QtGui import QPixmap

import projection
from typing import Optional


@dataclass
class Space:
    name: str
    description: str
    projections: list[projection.Projection] | None = None
    current_projection: projection.Projection | None = None
    sub_projections: list[projection.Projection] | None = None
    subspaces: list[Optional["Space"]] | None = None
    space_images: list[QPixmap] | None = None