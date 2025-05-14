import numpy as np
from PyQt6.QtGui import QPixmap, QImage, qAlpha, QPainterPath, QTransform
from PyQt6.QtCore import QRect, QBuffer, QPointF, Qt
import cv2

SCALE = 100

def crop_transparent_edges(pixmap: QPixmap) -> QPixmap:
    # Обрезает прозрачные края у картинки
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)

    left, top = image.width(), image.height()
    right, bottom = 0, 0

    for y in range(image.height()):
        for x in range(image.width()):
            if qAlpha(image.pixel(x, y)) > 0:
                left = min(left, x)
                right = max(right, x)
                top = min(top, y)
                bottom = max(bottom, y)

    if left > right or top > bottom:
        return QPixmap()  # Пустая картинка

    rect = QRect(left, top, right - left + 1, bottom - top + 1)
    return pixmap.copy(rect)


def get_scaled_pixmap(image_filename: str, width_m: float, height_m: float) -> QPixmap:
    target_width = int(width_m * SCALE)
    target_height = int(height_m * SCALE)

    pixmap = QPixmap(image_filename)
    cropped = crop_transparent_edges(pixmap)
    return cropped.scaled(target_width, target_height)


def pixmap_to_bytes(pixmap: QPixmap) -> bytes:
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.ReadWrite)
    pixmap.save(buffer, "PNG")
    return bytes(buffer.data())


def get_contours(pixmap: QPixmap):
    rgba = pixmap_to_rgba(pixmap)

    # create a binary mask based on the alpha channel
    alpha = rgba[:, :, 3]  # RGBA
    _, binary = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)

    # find contours and hierarchy
    contours, hierarchy = cv2.findContours(
        binary,
        cv2.RETR_CCOMP,   # outer and inner contours
        cv2.CHAIN_APPROX_SIMPLE
    )

    return [contours, hierarchy]


def get_path(contours, hierarchy):
    path = QPainterPath()
    path.setFillRule(Qt.FillRule.OddEvenFill)

    if hierarchy is not None:
        for i, contour in enumerate(contours):
            # start a new subpath
            sub_path = QPainterPath()

            if len(contour) == 0:
                continue

            first_point = contour[0][0]
            sub_path.moveTo(QPointF(first_point[0], first_point[1]))

            for point in contour[1:]:
                x, y = point[0]
                sub_path.lineTo(QPointF(x, y))

            sub_path.closeSubpath()
            path.addPath(sub_path)

        return path


def allow_movement(path_1, path_2, new_x, new_y):
    transform = QTransform()
    transform.translate(new_x, new_y)
    transformed_path_2 = transform.map(path_2)

    if path_1.contains(transformed_path_2):
        print("Background fully contains subspace. Movement is allowed!")
        return True
    else:
        print("Movement is not allowed!")
        return False


def pixmap_to_rgba(pixmap: QPixmap):
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
    width = image.width()
    height = image.height()
    ptr = image.bits()
    ptr.setsize(image.sizeInBytes())  # PyQt6
    arr = np.array(ptr, dtype=np.uint8).reshape((height, width, 4))

    return arr
