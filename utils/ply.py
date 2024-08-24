from pathlib import Path
from typing import Tuple, Optional, List

import numpy as np
from tqdm import trange
from plyfile import PlyData, PlyElement


def write_ply(
    filename: Path,
    points: np.ndarray,
    colors: Optional[np.ndarray] = None,
    normals: Optional[np.ndarray] = None,
    comment: Optional[str] = None,
    *,
    verbose: bool = False,
):
    """Write a point cloud to a .ply file.

    Parameters
    ----------
    filename : Path
        Path to the .ply file.
    points : np.ndarray
        Point cloud of shape (N, 3), dtype=np.float32.
    colors : np.ndarray, optional
        Colors of shape (N, 3), dtype=np.uint8, by default None
    normals : np.ndarray, optional
        Normals of shape (N, 3), dtype=np.float32, by default None
    comment : str, optional
        comment to be written in the header, by default None
    verbose : bool, optional
        Whether to show a progress bar, by default False
    """
    filename = Path(filename)
    if filename.suffix != ".ply":
        raise ValueError("File extension must be .ply")

    has_colors = colors is not None
    has_normals = normals is not None

    points = points.astype(np.float32)

    if has_colors:
        colors = colors.astype(np.uint8)
        if colors.shape != points.shape:
            raise ValueError("Colors must have the same shape as points")

    if has_normals:
        normals = normals.astype(np.float32)
        if normals.shape != points.shape:
            raise ValueError("Normals must have the same shape as points")
        
    filename.parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "wb") as f:
        f.write(b"ply\n")
        f.write(b"format binary_little_endian 1.0\n")
        f.write(b"element vertex %d\n" % len(points))

        if comment is not None:
            for com in comment.split("\n"):
                f.write(b"comment %s\n" % com.encode("utf-8"))

        f.write(b"property float x\n")
        f.write(b"property float y\n")
        f.write(b"property float z\n")

        if has_colors:
            f.write(b"property uchar red\n")
            f.write(b"property uchar green\n")
            f.write(b"property uchar blue\n")

        if has_normals:
            f.write(b"property float nx\n")
            f.write(b"property float ny\n")
            f.write(b"property float nz\n")

        f.write(b"end_header\n")

        progress = trange(len(points), desc=f"Writing {filename}", leave=False, disable=not verbose)
        for i in progress:
            f.write(points[i])
            if has_colors:
                f.write(colors[i])
            if has_normals:
                f.write(normals[i])

        f.write(b"\n")


def read_ply(filename: Path, *, verbose: bool = False) -> Tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """Read a point cloud from a .ply file.

    Parameters
    ----------
    filename : Path
        Path to the .ply file.
    verbose : bool, optional
        Whether to show a progress bar, by default False

    Returns
    -------
    points : np.ndarray
        Point cloud of shape (N, 3), dtype=np.float32.
    colors : np.ndarray
        Colors of shape (N, 3), dtype=np.uint8. None if there are no colors.
    normals : np.ndarray
        Normals of shape (N, 3), dtype=np.float32. None if there are no normals.
    comment : str
        comment in the header. None if there are no comment.
    """
    filename = Path(filename)
    if filename.exists() is False:
        raise FileNotFoundError(f"{filename} does not exist")

    with open(filename, "rb") as f:
        # Read header
        header = []
        while True:
            line = f.readline().decode("utf-8")
            header.append(line)
            if line == "end_header\n":
                break

        # Element vertex
        num = int([line.split(" ")[-1] for line in header if "element vertex" in line][0])

        # comment
        has_comment = any("comment" in line for line in header)
        if has_comment:
            comment = [line.split(" ", 1)[-1] for line in header if "comment" in line]
            comment = "".join(comment)[:-1]  # [:-1] to remove "\n" at the end
        else:
            comment = None

        # Properties
        properties = [line.split(" ")[-1].replace("\n", "") for line in header if "property" in line]

        # Check if there are colors and normals
        has_colors = "red" in properties and "green" in properties and "blue" in properties
        has_normals = "nx" in properties and "ny" in properties and "nz" in properties

        # Read points and colors
        points = np.empty((num, 3), dtype=np.float32)
        colors = np.empty((num, 3), dtype=np.uint8) if has_colors else None
        normals = np.empty((num, 3), dtype=np.float32) if has_normals else None

        progress = trange(num, leave=False, desc=f"Reading {filename}", disable=not verbose)
        for i in progress:
            points[i] = np.frombuffer(f.read(12), dtype=np.float32)
            if has_colors:
                colors[i] = np.frombuffer(f.read(3), dtype=np.uint8)
            if has_normals:
                normals[i] = np.frombuffer(f.read(12), dtype=np.float32)

    return points, colors, normals, comment

def write_ply_strands(filename, strands: List[np.ndarray]):
    filename = Path(filename)
    if filename.suffix != ".ply":
        raise ValueError("File extension must be .ply")
    filename.parent.mkdir(parents=True, exist_ok=True)
    # get data from strands
    points = []
    directions = []
    strand_roots = []
    points_id_to_strand_id = []
    edges = []
    points_count = 0
    strand_count = 0
    for strand in strands:
        if len(strand) < 2:
            continue
        strand_arr = np.array(strand)
        subarray_1 = strand_arr[0:-1]
        subarray_2 = strand_arr[1:]
        strand_direction = subarray_2 - subarray_1
        strand_num_points = subarray_1.shape[0]
        strand_ids = (np.ones(strand_num_points) * strand_count).astype(np.int64)
        points.append(subarray_1)
        directions.append(strand_direction)
        strand_roots.append(strand[0])
        points_id_to_strand_id.append(strand_ids)
        if strand_num_points > 1:
            edges_vertex_1 = np.arange(strand_num_points) + points_count
            edges_vertex_2 = np.arange(strand_num_points) + points_count + 1
            edges_ = np.stack((edges_vertex_1, edges_vertex_2), axis=1)
            edges.append(edges_)
        strand_count += 1
        points_count += strand_num_points
    points = np.concatenate(points)
    directions = np.concatenate(directions)
    strand_roots = np.array(strand_roots)
    points_id_to_strand_id = np.concatenate(points_id_to_strand_id)
    edges = np.concatenate(edges)
    # saving to ply
    # create vertex
    dtype = [(attribute, 'float32') for attribute in ['x', 'y', 'z', 'nx', 'ny', 'nz']]
    attributes =  np.concatenate((points, directions), axis=1)
    elements = np.empty(points.shape[0], dtype=dtype)
    elements[:] = list(map(tuple, attributes))
    vertex_elem = PlyElement.describe(elements, 'vertex')
    # create strand root
    dtype = [(attribute, 'float32') for attribute in ['x', 'y', 'z']]
    elements = np.empty(strand_roots.shape[0], dtype=dtype)
    elements[:] = list(map(tuple, strand_roots))
    root_elem = PlyElement.describe(elements, 'strand_root')
    # create strand id
    dtype = [('points_id_to_strand_id', 'i4')]
    elements = np.empty(points_id_to_strand_id.shape[0], dtype=dtype)
    elements[:] = points_id_to_strand_id.tolist()
    strand_id_elem = PlyElement.describe(elements, 'points_id_to_strand_id')
    # create edge
    dtype = [('vertex1', 'i4'), ('vertex2', 'i4')]
    elements = np.empty(edges.shape[0], dtype=dtype)
    elements[:] = list(map(tuple, edges))
    edge_elem = PlyElement.describe(elements, 'edge')
    # save to ply
    PlyData([vertex_elem, root_elem, strand_id_elem, edge_elem]).write(filename)