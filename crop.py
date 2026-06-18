import cv2
import numpy as np

def crop_polygon(image, points, return_mask_data=False):
    """
    Crops an image using a polygon.
    If return_mask_data=True, returns (roi, local_mask, x, y, w, h) for optimized looping.
    Otherwise, returns just the cropped ROI image.
    """
    if len(points) < 3:
        blank = np.zeros_like(image)
        return (blank, None, 0, 0, 0, 0) if return_mask_data else blank
    
    pts = np.array([points], dtype=np.int32)
    x, y, w, h = cv2.boundingRect(pts)
    
    if w <= 0 or h <= 0:
        blank = np.zeros_like(image)
        return (blank, None, 0, 0, 0, 0) if return_mask_data else blank

    local_mask = np.zeros((h, w), dtype=np.uint8)
    # Shift polygon points to match the new cropped coordinate space
    shifted_pts = pts - [x, y]
    cv2.fillPoly(local_mask, shifted_pts, 255)

    roi = image[y:y+h, x:x+w]
    
    if len(roi.shape) == 3: # Color
        mask_3ch = cv2.merge([local_mask] * 3)
        cropped_roi = cv2.bitwise_and(roi, mask_3ch)
    else: # Grayscale
        cropped_roi = cv2.bitwise_and(roi, roi, mask=local_mask)

    if return_mask_data:
        return cropped_roi, local_mask, x, y, w, h
    
    return cropped_roi

def select_points(image):
    print("""Selecione os pontos.
          Botão direito para adicionar
          Botão esquerdo para remover o último
          ESC para finalizar""")
    WINDOW_NAME =  "Select Points"
    image = image.copy()
    image_display = image.copy()
    points = []

    def click_event(event, x, y, flags, param):
        nonlocal points, image_display

        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
            image_display = image.copy()
            for pt in points:
                cv2.circle(image_display, pt, 5, (0, 255, 0), -1)
            update_preview()
        elif event == cv2.EVENT_RBUTTONDOWN:
            if points:
                points.pop()
                image_display = image.copy()
                for pt in points:
                    cv2.circle(image_display, pt, 5, (0, 255, 0), -1)
                update_preview()

    def update_preview():
        if len(points) >= 3:
            preview = crop_polygon(image, points)
        else:
            preview = np.ones((100, 100, 3), dtype=np.uint8) * 50
        cv2.imshow("Preview", preview)
        cv2.imshow(WINDOW_NAME, image_display)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.namedWindow("Preview", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW_NAME, click_event)

    update_preview()

    while True:
        cv2.imshow(WINDOW_NAME, image_display)
        key = cv2.waitKey() & 0xFF
        if key == 27:  # ESC to finish
            break

    cv2.destroyAllWindows()

    return points