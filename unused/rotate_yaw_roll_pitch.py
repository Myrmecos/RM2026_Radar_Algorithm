import numpy as np

def rotate(R, t, yaw, roll, pitch):
    """
    Rotate camera by yaw (Z), roll (X), pitch (Y) in degrees
    Returns new R and t
    """
    # Convert to radians
    y, r, p = np.radians([yaw, roll, pitch])
    
    # Rotation matrices
    R_yaw = np.array([[np.cos(y), -np.sin(y), 0],
                      [np.sin(y),  np.cos(y), 0],
                      [0, 0, 1]])
    
    R_roll = np.array([[1, 0, 0],
                       [0, np.cos(r), np.sin(r)],
                       [0, -np.sin(r), np.cos(r)]])
    
    R_pitch = np.array([[np.cos(p), 0, -np.sin(p)],
                        [0, 1, 0],
                        [np.sin(p), 0, np.cos(p)]])
    
    # Combined rotation (Z*Y*X order)
    R_delta = R_yaw @ R_pitch @ R_roll
    
    # Apply rotation
    R_new = R @ R_delta
    t_new = R @ (R_delta @ t)
    
    return R_new, t_new

def print_Rt(R, t):
    # print in format:
    # R: [[0.99530147, -0.03039188, -0.09193101],
    #     [-0.01339114, -0.98354371, 0.18017339],
    #     [-0.09589397, -0.17809578, -0.97932948],]
    # t: [[-0.68605672], [1.13893625], [15.32698638]]
        # Print R
    print("R: [", end="")
    for i, row in enumerate(R):
        row_str = ", ".join([f"{x:.8f}" for x in row])
        if i < len(R) - 1:
            print(f"    [{row_str}],")
        else:
            print(f"    [{row_str}]]")
    # print("]")
    
    # Print t
    t_flat = t.flatten()
    t_str = ", ".join([f"[{x:.8f}]" for x in t_flat])
    print(f"  t: [[{t_str}]]")

R = [[0.99530147, -0.03039188, -0.09193101],
    [-0.01339114, -0.98354371, 0.18017339],
    [-0.09589397, -0.17809578, -0.97932948],]
t = np.array([[-0.68605672], [1.13893625], [15.32698638]])

# Example: rotate down 15 degrees (roll around X-axis)
R_new, t_new = rotate(R, t, yaw=0, roll=1, pitch=0) # pos yaw: image rotate counter-clockwise
# pos roll: rot camera up while move whole thing down

print_Rt(R_new, t)