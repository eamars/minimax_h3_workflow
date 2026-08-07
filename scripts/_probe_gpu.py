import os
import torch

with open(r"D:\minimax_h3_workflow\logs\probe3.txt", "w") as f:
    f.write("CVD=" + os.environ.get("CUDA_VISIBLE_DEVICES", "NONE") + "\n")
    f.write("count=" + str(torch.cuda.device_count()) + "\n")
    for i in range(torch.cuda.device_count()):
        f.write(f"dev{i}={torch.cuda.get_device_name(i)}\n")
