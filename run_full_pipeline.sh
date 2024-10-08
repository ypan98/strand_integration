#!/bin/bash

original_data_folder=$1
# depth range in cm for filtering
min_depth=$2    
max_depth=$3
folder_name=$(basename "$original_data_folder")

echo "######################## Converting data "########################
python convert_data.py --input $original_data_folder --skip_orientation

echo "######################## Running LPMVS pipeline "########################
python run_lpmvs.py data/$folder_name -o result/lpmvs/$folder_name  --min_depth $min_depth --max_depth $max_depth
python run_line_filtering.py result/lpmvs/$folder_name result/merged_ply/lpmvs/$folder_name.ply

echo "######################## Running Strand Integration pipeline ########################"
python run_consistency_map.py result/lpmvs/$folder_name -o result/consistency/$folder_name
python run_strand_integration.py result/lpmvs/$folder_name --consistency result/consistency/$folder_name -o result/si/$folder_name
python run_line_filtering.py result/si/$folder_name result/merged_ply/si/$folder_name.ply

echo "######################## Running LPMVS V2 pipeline "########################
python run_line_filtering.py result/lpmvs/$folder_name result/merged_ply/lpmvs_v2/$folder_name.ply -s

echo "######################## Running Strand Integration V2 pipeline ########################"
python run_line_filtering.py result/si/$folder_name result/merged_ply/si_v2/$folder_name.ply -s