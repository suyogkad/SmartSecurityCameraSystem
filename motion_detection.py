import cv2
import numpy as np


def detect_motion(video_path):
    # Initialize the video capture object
    cap = cv2.VideoCapture(video_path)

    # Initialize two frames for motion comparison
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()

    while cap.isOpened():
        # Update frames for the next iteration
        frame1 = frame2
        ret, frame2 = cap.read()

        # If we can't fetch the next frame, break out of the loop
        if not ret:
            break
        # Calculate absolute difference between two consecutive frames
        diff = cv2.absdiff(frame1, frame2)

        # Convert the difference to grayscale
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to grayscale frame
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Detect edges in the blurred frame
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)

        # Dilate the thresholded frame to fill holes and improve motion detection
        dilated = cv2.dilate(thresh, None, iterations=3)

        # Find contours in the dilated frame
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Draw rectangles around detected motions
        for contour in contours:
            (x, y, w, h) = cv2.boundingRect(contour)

            # Draw rectangles for significant motions only
            if cv2.contourArea(contour) < 500:
                continue
            cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Display the motion-detected frame
        cv2.imshow("Feed with Motion Detection", frame1)

        # Update frames for the next iteration
        frame1 = frame2
        ret, frame2 = cap.read()

        if cv2.waitKey(40) == 27:  # Press 'ESC' key to exit
            break

    cap.release()
    cv2.destroyAllWindows()
