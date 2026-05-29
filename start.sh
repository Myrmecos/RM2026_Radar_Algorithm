cd /home/etmphile/桌面/RM2025-Radar-Algorithm

source ros_setup.bash

sudo chmod 766 /dev/ttyACM0

python main.py --config config/params.yaml --device_config config/device.yaml