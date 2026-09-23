import torch
import cv2

# initializing the model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

def process_frame(frame):
    """function to process each frames for detection in live feed"""

    # inference
    results = model(frame)

    # extracting class names and confidence values
    detected_info = [(model.names[int(i[-1])], i[-2]) for i in results.pred[0]]

    # rendering the results on the frame
    frame = results.render()[0]

    return frame, detected_info

def detect_live():
    """function to capture frames and make detections in live feed"""

    cap = cv2.VideoCapture(0)  # 0 for the default camera (web-cam)

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            break

        results = model(frame)

        # rendering the results on the frame
        frame = results.render()[0]

        cv2.imshow('Live Detection', frame)
        if cv2.waitKey(1) == ord('q'):  # press 'q' key to quit the live feed
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    detect_live()
