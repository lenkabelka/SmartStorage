from dataclasses import dataclass
from PyQt6.QtGui import QPixmap, QImage
from typing import Optional
import draggable_pixmap_item
import space
import object_state


@dataclass
class Projection:
    projection_name: str
    projection_image: QImage
    projection_width: float | None
    projection_height: float | None
    reference_to_parent_space: Optional["space.Space"]
    scaled_projection_pixmap: draggable_pixmap_item.DraggablePixmapItem | QPixmap | None = None
    reference_to_parent_projection: Optional["Projection"] | None = None
    projection_description: str | None = None
    x_pos: float | None = None
    y_pos: float | None = None
    id_projection: int | None = None
    id_parent_projection: int | None = None
    id_parent_space: int | None = None

    projection_object_state: object_state.State = object_state.State.NEW