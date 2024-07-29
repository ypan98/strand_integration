import numpy as np
import os
from pathlib import Path
import pyvista as pv
from dreifus.pyvista import add_floor, add_coordinate_axes
import matplotlib.pyplot as plt

def plot_cameras(p, K, R, t, i):
    from dreifus.pyvista import add_camera_frustum, Pose, PoseType, Intrinsics, CameraCoordinateConvention
    cmap = plt.get_cmap("viridis")
    pose = np.eye(4)
    pose[:3, :3] = R
    pose[:3, 3] = t
    E = Pose(pose, pose_type=PoseType.WORLD_2_CAM, camera_coordinate_convention=CameraCoordinateConvention.OPEN_CV)
    K_ = Intrinsics(K)
    color = cmap(i)
    add_camera_frustum(p, E, K_, color=color)

p = pv.Plotter(notebook=False)
add_coordinate_axes(p, scale=0.1, draw_labels=False)
data_folder = Path(f"data") / "straight_s"
scale = 1/100 # cm to m
# data_folder = Path(f"data") / "00002"
N = len(os.listdir(data_folder))

for i in range(N):
    view_id = str(i).zfill(2)
    view_folder = data_folder / view_id
    K = np.loadtxt(view_folder / "K.txt")
    R = np.loadtxt(view_folder / "R.txt")
    t = np.loadtxt(view_folder / "t.txt")
    t *= scale
    plot_cameras(p, K, R, t, i/N)

axes_actor = p.add_axes()
axes_actor.SetXAxisLabelText("X")
axes_actor.SetYAxisLabelText("Y")
axes_actor.SetZAxisLabelText("Z")
p.show()

