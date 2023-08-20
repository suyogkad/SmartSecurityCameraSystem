import torch
import cv2

# Initialize the model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # you can use 'yolov5m' or 'yolov5l' for better accuracy but slower speed

def process_frame(frame):
    # Inference
    results = model(frame)

    # Extracting class names and confidence values
    detected_info = [(model.names[int(i[-1])], i[-2]) for i in results.pred[0]]

    # Rendering the results on the frame
    frame = results.render()[0]

    return frame, detected_info

def detect_live():
    cap = cv2.VideoCapture(0)  # Use 0 for the default camera, change if you have multiple cameras

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            break

        # Inference
        results = model(frame)

        # Rendering the results on the frame
        frame = results.render()[0]

        cv2.imshow('Live Detection', frame)
        if cv2.waitKey(1) == ord('q'):  # Press 'q' to exit the live feed
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    detect_live()
