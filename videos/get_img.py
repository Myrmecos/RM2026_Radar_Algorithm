
import cv2
cap = cv2.VideoCapture('/home/etmphile/桌面/RM2025-Radar-Algorithm/videos/H_edited.mp4')
ret, frame = cap.read()
if ret:
    print(f'Shape: {frame.shape}')
    cv2.imwrite('/home/etmphile/桌面/RM2025-Radar-Algorithm/videos/first_frame.png', frame)
    print('Saved to first_frame.png')
cap.release()
