import os
import argparse
import pandas
from pathlib import Path
import numpy as np
import glob
from collections import defaultdict

vertebra_levels = ("T12", "L1", "L2", "L3", "L4", "L5")
images = (
    "T12", "L1", "L2", "L3", "L4", "L5", 
    "spine", 
    "spine_muscle", 
    "spine_report", 
    "spine_sagittal"
    )
metrics = (
    "level", 
    "slice_index",
    "muscle_hu", 
    "muscle_csa_cm2",
    "sat_hu", 
    "sat_csa_cm2",
    "vat_hu",
    "vat_csa_cm2",
    "imat_hu",
    "imat_csa_cm2"
    )

def get_args():
    parser = argparse.ArgumentParser(prog="extract_metrics.py", description="extraction and merge of comp2comp's result metrics")
    parser.add_argument("in_directory", type=str)
    parser.add_argument("-od", "--out_directory", type=str, default=os.getcwd(), help="set output directory")
    parser.add_argument("-ve", "--vertebrae", nargs="+", help="vertebrae to extract", choices=vertebra_levels, required=True)
    parser.add_argument("-me", "--metrics", nargs="+", help="metric to extract", choices=metrics, required=True)
    parser.add_argument("-im", "--images", nargs="+", help="segmentation images (PNG) to copy", choices=images)
    
    return parser.parse_args()


def get_metrics(df, metrics, vertebrae, case_name: str = ""):
    cols = [col for col in df.columns if col in metrics]

    matched_df: pandas.DataFrame = df[cols]
    out_df = matched_df[matched_df['level'].isin(vertebrae)]
    return out_df
    

args = get_args()

in_directory = Path(args.in_directory)
csv_files = list(in_directory.rglob("muscle*.csv"))
args.metrics = ["level"] + [m.lower() for m in args.metrics if m != "level"]

dataframes = []

for path in csv_files:    
    data_df = pandas.read_csv(path)
    path_parts = path.parts
    case_name = path_parts[path_parts.index("metrics") - 1]
    
    result_df = get_metrics(data_df, args.metrics, args.vertebrae, case_name=case_name)
    dataframes.append(result_df)
        
    
output_df = pandas.concat(dataframes, ignore_index=True)
output_csv = Path(args.out_directory, "comp2comp_concat_muscle_metrics.csv")
print(output_df)
output_df.to_csv(output_csv, sep=",", na_rep=np.nan, index=True)
print(f"written concatenated metrics to {output_csv}")


