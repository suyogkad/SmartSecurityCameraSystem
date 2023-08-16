import cv2

def detect_motion(frame1, frame2):
    frame1_resized = cv2.resize(frame1, (640, 480))
    frame2_resized = cv2.resize(frame2, (640, 480))

    frameDelta = cv2.absdiff(frame1_resized, frame2_resized)

    gray = cv2.cvtColor(frameDelta, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (21, 21), 0)
    thresh = cv2.threshold(blurred, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in cnts:
        if cv2.contourArea(contour) < 500:
            continue
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame1_resized, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return frame1_resized
