#!/bin/bash

original_data_folder=$1
folder_name=$(basename "$original_data_folder")

echo "Converting: $original_data_folder..."
python convert_data.py --input $original_data_folder --skip_orientation
echo "Data conversion complete."

echo "**************** Running LPMVS pipeline ****************"
echo "Estimating depth maps and 3d orientations..."
python run_lpmvs.py data/$folder_name -o result/lpmvs/$folder_name 
echo "Filtering output..."
python run_line_filtering.py result/lpmvs/$folder_name result/merged_ply/lpmvs/$folder_name.ply
echo "**************** LPMVS pipeline complete ****************"

echo "**************** Running Strand Integration pipeline ****************"
echo "Estimating depth maps and 3d orientations..."
python run_consistency_map.py result/lpmvs/straight_s -o result/consistency/straight_s
echo "Filtering output..."
python run_strand_integration.py result/lpmvs/$folder_name --consistency result/consistency/$folder_name -o result/si/$folder_name
echo "Filtering output..."
python run_line_filtering.py result/si/$folder_name result/merged_ply/si/$folder_name.ply
echo "**************** Strand Integration pipeline complete ****************"