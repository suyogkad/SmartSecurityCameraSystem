
import cv2
import os


def detect_motion_and_save(video_path, save_path):
    cap = cv2.VideoCapture(video_path)
    ret, frame1 = cap.read()

    if not ret:
        print("Failed to read the frame.")
        return

    ret, frame2 = cap.read()

    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    motion_detected = False
    writer = None
    motion_start_time = None

    # creating a sub-directory based on the video filename
    video_name = os.path.basename(video_path).split(".")[0]
    segment_folder = os.path.join(save_path, f"{video_name}_segments")

    if not os.path.exists(segment_folder):
        os.makedirs(segment_folder)

    while ret:
        current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0  # in seconds

        frame1_resized = cv2.resize(frame1, (640, 480))
        frame2_resized = cv2.resize(frame2, (640, 480))

        frameDelta = cv2.absdiff(frame1_resized, frame2_resized)
        gray = cv2.cvtColor(frameDelta, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in cnts:
            if cv2.contourArea(contour) < 500:
                continue
            motion_detected = True
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame1_resized, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Display the processed frame
        cv2.imshow("Motion Detection", frame1_resized)

        if motion_detected:
            if writer is None:
                filename = os.path.join(segment_folder, "motion_start_{}.avi".format(str(motion_start_time)))
                writer = cv2.VideoWriter(filename, fourcc, 20.0, (frame1_resized.shape[1], frame1_resized.shape[0]))
                motion_start_time = current_time
            writer.write(frame1_resized)
        else:
            if writer is not None:
                writer.release()
                writer = None
                motion_start_time = None

        motion_detected = False
        frame1 = frame2
        ret, frame2 = cap.read()

        #  press 'q' to quit the video window
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    if writer is not None:
        writer.release()

    cap.release()
    cv2.destroyAllWindows()
