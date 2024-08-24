from typing import List
from tqdm import tqdm
import numpy as np
from scipy.spatial import cKDTree

def accumulate_strand_points(kdtree, visited_mask, points: np.ndarray, directions: np.ndarray, initial_point: np.ndarray, initial_direction: np.ndarray, step_size: float, 
                             dist_th: float, angle_th: float) -> List[np.ndarray]:
    def filter_by_angle_th(nn_indices, curr_direction):
        neighbor_directions = directions[nn_indices]
        cos_sim = (curr_direction @ neighbor_directions.T).squeeze()
        dir_mask = cos_sim > cos_sim_th
        return nn_indices[dir_mask]
    strand = []
    cos_sim_th = np.cos(np.deg2rad(angle_th))
    curr_point = initial_point + initial_direction * step_size
    curr_direction = initial_direction
    nn_indices = np.array(kdtree.query_ball_point(curr_point, r=dist_th, workers=-1))
    nn_indices = filter_by_angle_th(nn_indices, curr_direction) if len(nn_indices) > 0 else nn_indices
    nn_indices = nn_indices[visited_mask[nn_indices]] if len(nn_indices) > 0 else nn_indices
    while len(nn_indices) > 0:
        visited_mask[nn_indices] = False
        strand.append(curr_point)
        curr_point = np.mean(points[nn_indices], axis=0).squeeze()
        curr_direction = np.mean(directions[nn_indices], axis=0).squeeze()
        nn_indices = np.array(kdtree.query_ball_point(curr_point, r=dist_th, workers=-1))
        nn_indices = filter_by_angle_th(nn_indices, curr_direction)
        nn_indices = nn_indices[visited_mask[nn_indices]] if len(nn_indices) > 0 else nn_indices
    return strand

def generate_strands(points: np.ndarray, directions: np.ndarray, step_size: float = 0.1, dist_th: float = 0.1, angle_th: float = 30) -> List[np.ndarray]:
    directions = directions / np.linalg.norm(directions, axis=1)[:, None]
    total_points = points.shape[0]
    remaining_points_mask = np.ones(total_points, dtype=bool)
    strands = []
    kdtree = cKDTree(points)
    pbar = tqdm(total=total_points, desc="Generating strands", unit="iteration")
    while np.any(remaining_points_mask):
        strand = []
        # 1. Pick random seed from remaining points
        remaining_indices = np.where(remaining_points_mask)[0]
        seed_idx = np.random.choice(remaining_indices)
        seed_point = points[seed_idx]
        seed_direction = directions[seed_idx]
        strand.append(seed_point)
        # 2. Accumulate strand points from forward and backward directions
        visited_mask = remaining_points_mask.copy()
        visited_mask[seed_idx] = False
        forward_points = accumulate_strand_points(kdtree, visited_mask, points, directions, seed_point, seed_direction, step_size, dist_th, angle_th)
        backward_points = accumulate_strand_points(kdtree, visited_mask, points, directions, seed_point, -seed_direction, step_size, dist_th, angle_th)
        strand = forward_points + backward_points + strand
        strand = np.array(strand)
        strands.append(strand)        
        # 3. Remove points that are nearby current strand
        arr_list_indices = kdtree.query_ball_point(strand, r=dist_th, workers=-1)
        arr_indices = np.concatenate(arr_list_indices).astype(np.int64)
        remaining_points_mask[arr_indices] = False
        # updae progress bar
        processed_points = total_points - np.sum(remaining_points_mask)
        pbar.n = processed_points
        pbar.refresh()
    return strands