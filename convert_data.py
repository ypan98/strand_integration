"""
Convert COLMAP fomrat data to format that LPMVS codebase can read
"""

import argparse
from pathlib import Path
import shutil
import os
import cv2
import numpy as np

from utils.colmap_loader import read_extrinsics_binary, read_intrinsics_binary, colmap_camera_extrinsic_to_Rt, colmap_camera_intrinsic_to_K

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Convert custom data to LPMVS format")
    parser.add_argument("--input", default="../Datasets/hair/00002", type=str)
    parser.add_argument("--skip_orientation", action="store_true")
    parser.add_argument("--scale", default=100, type=float, help="Scale factor to convert from meter to cm")
    args = parser.parse_args()

    # check if input folder exists
    original_data_folder = Path(args.input)
    if not original_data_folder.exists():
        raise FileNotFoundError(f"Folder {original_data_folder} does not exist")
    id = original_data_folder.parts[-1]
    # create output folder
    output_folder = Path(f"data") / id
    if output_folder.exists():
        shutil.rmtree(output_folder)
    output_folder.mkdir(exist_ok=True, parents=True)
    # get image, orientation, mask, sparse folder
    image_folder = original_data_folder / "images"
    orientation_folder = original_data_folder / "orientations"
    mask_folder = original_data_folder / "masks"
    sparse_folder = original_data_folder / "sparse" / "0"
    # check if images and masks folder exists
    if not image_folder.exists():
        raise FileNotFoundError(f"Folder {image_folder} does not exist")
    if not orientation_folder.exists():
        raise FileNotFoundError(f"Folder {orientation_folder} does not exist")
    if not mask_folder.exists():
        raise FileNotFoundError(f"Folder {mask_folder} does not exist")
    if not sparse_folder.exists():
        raise FileNotFoundError(f"Folder {sparse_folder} does not exist")
    
    # load camera intrinsic and extrinsic
    cameras_extrinsic_file = os.path.join(sparse_folder, "images.bin")
    cameras_intrinsic_file = os.path.join(sparse_folder, "cameras.bin")
    cam_extrinsics = read_extrinsics_binary(cameras_extrinsic_file)
    cam_intrinsics = read_intrinsics_binary(cameras_intrinsic_file)
    
    images_path = os.listdir(image_folder)
    # iterate over all views
    for i, image_path in enumerate(images_path):
        view_output_folder = output_folder / str(i).zfill(2)
        view_output_folder.mkdir(exist_ok=True, parents=True)
        # image
        view_id = int((image_path.split("image_")[1]).split(".")[0])
        image_file = image_folder / image_path
        image_rbg = cv2.imread(image_file, cv2.IMREAD_COLOR)
        image_gray = cv2.cvtColor(image_rbg, cv2.COLOR_BGR2GRAY)
        image_gray = image_gray.astype("float32") / 255.0
        cv2.imwrite(str(view_output_folder / "intensity.exr"), image_gray)
        # mask
        mask_file = mask_folder / image_path
        mask = cv2.imread(mask_file)
        cv2.imwrite(str(view_output_folder / "mask.png"), mask)
        # orientation and confidence
        if not args.skip_orientation:
            orientation_file = orientation_folder / f"image_{view_id}_orientation.png"
            confidence_file = orientation_folder / f"image_{view_id}_confidence.png"
            orientation = cv2.imread(orientation_file, cv2.IMREAD_GRAYSCALE)
            confidence = cv2.imread(confidence_file, cv2.IMREAD_GRAYSCALE)
            orientation = (orientation.astype("float32") / 255.0) * np.pi
            confidence = (confidence.astype("float32") / 255.0) * 1000
            cv2.imwrite(str(view_output_folder / "orientation2d.exr"), orientation)
            cv2.imwrite(str(view_output_folder / "confidence.exr"), confidence)
        # K, R, t
        R, t = colmap_camera_extrinsic_to_Rt(cam_extrinsics[view_id], scale=args.scale)
        K = colmap_camera_intrinsic_to_K(cam_intrinsics[view_id])
        np.savetxt(view_output_folder / "R.txt", R)
        np.savetxt(view_output_folder / "t.txt", t)
        np.savetxt(view_output_folder / "K.txt", K)
        