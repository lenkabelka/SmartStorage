from dataclasses import dataclass
from PyQt6.QtGui import QPixmap, QImage
from typing import Optional
import draggable_pixmap_item
import space


@dataclass
class Projection:
    projection_name: str
    projection_image: QImage
    x_scale: float
    y_scale: float
    reference_to_parent_space: Optional["space.Space"]
    scaled_projection_pixmap: draggable_pixmap_item.DraggablePixmapItem | QPixmap | None = None
    reference_to_parent_projection: Optional["Projection"] | None = None
    projection_description: str | None = None
    x_pos: float | None = None
    y_pos: float | None = None