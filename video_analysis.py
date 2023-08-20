import cv2
import torch
import os

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
video_folder = 'CCTVFootage'
output_folder = 'ProcessedVideos'
os.makedirs(output_folder, exist_ok=True)


def detect_objects(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Define the codec and create VideoWriter object to save the video
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(os.path.join(output_folder, os.path.basename(video_path)), fourcc, fps,
                          (int(cap.get(3)), int(cap.get(4))))

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            break

        # Detect objects using YOLOv5
        results = model(frame)
        frame_with_detections = results.render()[0]

        out.write(frame_with_detections)  # Save the resulting frame to the output video
        cv2.imshow('Video Analysis', frame_with_detections)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    for video_file in os.listdir(video_folder):
        video_path = os.path.join(video_folder, video_file)
        detect_objects(video_path)
