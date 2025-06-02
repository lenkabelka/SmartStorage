import numpy as np
from PyQt6.QtGui import QPixmap, QImage, qAlpha, QPainterPath, QTransform
from PyQt6.QtCore import QRect, QBuffer, QPointF, Qt
import cv2
import math


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


def crop_transparent_edges_1(image: QImage) -> QImage:
    # Обрезает прозрачные края у картинки
    if image.format() != QImage.Format.Format_ARGB32:
        image = image.convertToFormat(QImage.Format.Format_ARGB32)

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
        return QImage()  # Пустая картинка

    rect = QRect(left, top, right - left + 1, bottom - top + 1)
    #TODO проверить copy
    return image.copy(rect)


def calculate_new_image_size(image, x_sm, y_sm):
    new_height = image.height()
    new_width = image.width()
    if image:
        ratio_px = image.width() / image.height() #!!!!!!!!!
        ratio_sm = x_sm / y_sm
        if math.isclose(ratio_px, ratio_sm, abs_tol=0.00001):
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

        print(f"old_width: {image.width()}")
        print(f"old_height: {image.height()}")

        print(f"new_width: {new_width}")
        print(f"new_height: {new_height}")

        return image.scaled(new_width, new_height)


def get_scaled_pixmap(image: QImage,
                        target_width,
                        target_height) -> QPixmap:

    if image.format() != QImage.Format.Format_ARGB32:
        image = image.convertToFormat(QImage.Format.Format_ARGB32)

    image_crop = crop_transparent_edges_1(image)

    #target_width = int(round(image.width() * x_scale_coef))
    print(f"target_width: {target_width}")
    #target_height = int(round(image.height() * y_scale_coef))
    print(f"target_height: {target_height}")

    scaled_image = image_crop.scaled(target_width,
                                target_height,
                                Qt.AspectRatioMode.IgnoreAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)

    pixmap_from_scaled_image = QPixmap.fromImage(scaled_image)
    #cropped_pixmap = crop_transparent_edges(pixmap_from_scaled_image)

    print(f"pixmap_from_scaled_image_W: {pixmap_from_scaled_image.width()}")
    print(f"pixmap_from_scaled_image_H: {pixmap_from_scaled_image.height()}")

    return pixmap_from_scaled_image

# def get_scaled_pixmap(image_filename: str, width_m: float, height_m: float) -> QPixmap:
#     target_width = int(width_m * SCALE)
#     target_height = int(height_m * SCALE)
#
#     pixmap = QPixmap(image_filename)
#     cropped = crop_transparent_edges(pixmap)
#     return cropped.scaled(target_width, target_height)


def pixmap_to_bytes(pixmap: QPixmap) -> bytes:
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.ReadWrite)
    # TODO сделать обработку других форматов
    pixmap.save(buffer, "PNG")
    return bytes(buffer.data())


def get_contours(pixmap: QPixmap):

    #print("Я в начале get_contours")

    rgba = pixmap_to_rgba(pixmap)
    #print("PUNKT_1")
    # create a binary mask based on the alpha channel
    alpha = rgba[:, :, 3]  # RGBA
    #print("PUNKT_2")
    _, binary = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)
    #print("PUNKT_3")
    # find contours and hierarchy
    contours, hierarchy = cv2.findContours(
        binary,
        cv2.RETR_CCOMP,   # outer and inner contours
        cv2.CHAIN_APPROX_SIMPLE
    )

    #print("Я в конце get_contours")

    return [contours, hierarchy]


def get_path(contours, hierarchy):
    #print("Я в начале get_path")

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

        #print("Я в конце get_path")

        return path


def allow_movement(path_1, path_2, new_x, new_y):
    transform = QTransform()
    transform.translate(new_x, new_y)
    transformed_path_2 = transform.map(path_2)

    if path_1.contains(transformed_path_2):
        #print("Background fully contains subspace. Movement is allowed!")
        return True
    else:
        #print("Movement is not allowed!")
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
