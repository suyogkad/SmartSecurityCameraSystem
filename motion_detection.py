import cv2


def detect_motion(frame1, frame2):
    # Resize both frames for consistent processing
    frame1_resized = cv2.resize(frame1, (640, 480))
    frame2_resized = cv2.resize(frame2, (640, 480))

    # Calculate the absolute difference between the two frames to detect changes (motion)
    frameDelta = cv2.absdiff(frame1_resized, frame2_resized)

    # Convert the difference frame to grayscale for further processing
    gray = cv2.cvtColor(frameDelta, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to the grayscale frame to remove noise and smoothen the image
    blurred = cv2.GaussianBlur(gray, (21, 21), 0)

    # Threshold the blurred frame to get a binary image where white represents motion
    thresh = cv2.threshold(blurred, 25, 255, cv2.THRESH_BINARY)[1]

    # Dilate the thresholded frame to fill in holes, making the motion area more continuous
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Find contours of the motion areas
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Iterate through the motion contours
    for contour in cnts:
        # If the contour is too small, ignore it (reduce false positives)
        if cv2.contourArea(contour) < 500:
            continue

        # Get bounding rectangle of the contour
        (x, y, w, h) = cv2.boundingRect(contour)

        # Draw a green rectangle around the motion area
        cv2.rectangle(frame1_resized, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Return the processed frame with motion areas highlighted
    return frame1_resized
