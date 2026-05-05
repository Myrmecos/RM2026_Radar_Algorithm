import cv2

cap = cv2.VideoCapture('/home/etmphile/桌面/RM2025-Radar-Algorithm/videos/HarbinU.mp4')

# Set the frame position directly instead of reading 5000 frames
cap.set(cv2.CAP_PROP_POS_FRAMES, 1)
ret, frame = cap.read()

if ret:
    print(f'Shape: {frame.shape}')
    cv2.imwrite('/home/etmphile/桌面/RM2025-Radar-Algorithm/videos/first_frame.png', frame)
    print('Saved to first_frame.png')
else:
    print(f'Failed to read frame at position 5000 (total frames: {int(cap.get(cv2.CAP_PROP_FRAME_COUNT))})')

cap.release()