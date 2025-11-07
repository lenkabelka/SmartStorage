import numpy as np
from PyQt6.QtGui import QPixmap, QImage, qAlpha, QTransform
from PyQt6.QtCore import QRect, QBuffer, QPointF, Qt
import cv2
import math
import os
import sys
from PyQt6.QtGui import QPainterPath


def crop_transparent_edges(image: QImage) -> QImage:
    # Обрезает прозрачные края у картинки
    if image.format() != QImage.Format.Format_ARGB32:
        image = image.convertToFormat(QImage.Format.Format_ARGB32)

    left, top = image.width(), image.height()
    right, bottom = 0, 0

    #for y in range(image.height()):
    #    for x in range(image.width()):
    #        if qAlpha(image.pixel(x, y)) > 0:
    #            left = min(left, x)
    #            right = max(right, x)
    #            top = min(top, y)
    #            bottom = max(bottom, y)

    found = False
    for x in range(image.width()):
        for y in range(image.height()):
            if qAlpha(image.pixel(x, y)) > 0:
                left = x
                found = True
                break
        if found: break

    found = False
    for y in range(image.height()):
        for x in range(image.width()):
            if qAlpha(image.pixel(x, y)) > 0:
                top = y
                found = True
                break
        if found: break

    found = False
    for x in range(image.width() - 1, 0, -1):
        for y in range(image.height()):
            if qAlpha(image.pixel(x, y)) > 0:
                right = x
                found = True
                break
        if found: break

    for y in range(image.height() - 1, 0, -1):
        for x in range(image.width()):
            if qAlpha(image.pixel(x, y)) > 0:
                bottom = y
                found = True
                break
        if found: break

    if left > right or top > bottom:
        return QImage()  # Пустая картинка

    rect = QRect(left, top, right - left + 1, bottom - top + 1)
    #TODO проверить copy
    return image.copy(rect)


def calculate_new_image_size(image, x_width, y_height):
    new_height = image.height()
    new_width = image.width()
    if image:
        ratio_px = image.width() / image.height()
        ratio_sm = x_width / y_height
        if math.isclose(ratio_px, ratio_sm, abs_tol=0.0005):
            print("равны")
            new_height = image.height()
            new_width = image.width()
        elif ratio_px < ratio_sm:
            print("слишком высокая")
            k = ratio_px / ratio_sm
            new_height = int(round(k * image.height()))
            new_width = image.width()
        elif ratio_px > ratio_sm:
            print("слишком широкая")
            k = ratio_sm / ratio_px
            new_width = int(round(k * image.width()))
            new_height = image.height()

        return image.scaled(new_width, new_height)
    return None


def get_scaled_pixmap(image: QImage,
                        target_width,
                        target_height) -> QPixmap:
    if image.format() != QImage.Format.Format_ARGB32:
        image = image.convertToFormat(QImage.Format.Format_ARGB32)
    image_crop = crop_transparent_edges(image)

    scaled_image = image_crop.scaled(target_width,
                                target_height,
                                Qt.AspectRatioMode.IgnoreAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
    pixmap_from_scaled_image = QPixmap.fromImage(scaled_image)

    return pixmap_from_scaled_image


def get_scaled_cropped_pixmap(image, real_projection_width, real_projection_height):
    scaled_image = calculate_new_image_size(
        image,
        real_projection_width,
        real_projection_height
    )

    scaled_cropped_pixmap = get_scaled_pixmap(
        image,
        scaled_image.width(),
        scaled_image.height()
    )

    return scaled_cropped_pixmap


def pixmap_to_bytes(pixmap: QPixmap) -> bytes:
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.ReadWrite)
    # TODO сделать обработку других форматов
    pixmap.save(buffer, "PNG")
    return bytes(buffer.data())

def qimage_to_bytes(image: QImage) -> bytes:
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.ReadWrite)
    # TODO: поддержка других форматов по необходимости
    image.save(buffer, "PNG")
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


def allow_movement(path_parent, path_child, new_x, new_y):
    transform = QTransform()
    transform.translate(new_x, new_y)
    transformed_path_child = transform.map(path_child)

    if path_parent.contains(transformed_path_child):
        return True
    else:
        return False


def pixmap_to_rgba(pixmap: QPixmap):
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
    width = image.width()
    height = image.height()
    ptr = image.bits()
    ptr.setsize(image.sizeInBytes())  # PyQt6
    arr = np.array(ptr, dtype=np.uint8).reshape((height, width, 4))

    return arr


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
        elif item.layout() is not None:
            clear_layout(item.layout())


def iterate_pixels_in_path(path: QPainterPath, step: int = 1):
    """
    Генерирует *все пиксели внутри path*

    :param path: QPainterPath любой формы
    :param step: шаг перебора (1 = каждый пиксель, 2 = каждый второй и т.д.)
    :yield: QPointF - координаты пикселя внутри path
    """
    bounds = path.boundingRect()
    left = int(bounds.left())
    right = int(bounds.right())
    top = int(bounds.top())
    bottom = int(bounds.bottom())

    for y in range(top, bottom + 1, step):
        for x in range(left, right + 1, step):
            point = QPointF(x, y)
            if path.contains(point):
                yield point


def resource_path(relative_path):
    """Возвращает корректный путь к ресурсу при запуске и из IDE, и из .exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)