import os
import argparse
import pandas
from pathlib import Path
import numpy as np
import glob
from collections import defaultdict

allowed_vertebrae = ("T12", "L1", "L2", "L3", "L4", "L5")
# allowed_metrics = ("muscle_csa", "slice_index")
allowed_pngs = ("T12", "L1", "L2", "L3", "L4", "L5", "spine", "spine_muscle", "spine_report", "spine_sagittal")
metrics_map = {
    'level': "Level",
    'slice_index': "Index",
    'muscle_hu': "Muscle HU",
    'muscle_csa': "Muscle CSA (cm^2)",
    'sat_hu': "SAT HU",
    'sat_csa': "SAT CSA (cm^2)",
    'vat_hu': "VAT HU",
    'vat_csa': "VAT CSA (cm^2)",
    'imat_hu': "IMAT HU",
    'imat_csa': "IMAT CSA (cm^2)"
}

def get_args():
    parser = argparse.ArgumentParser(prog="extract_metrics.py", description="extraction and merge of comp2comp's result metrics")
    parser.add_argument("in_directory", type=str)
    parser.add_argument("-od", "--out_directory", type=str, default=os.getcwd(), help="set output directory")
    parser.add_argument("-ve", "--vertebrae", nargs="+", help="vertebrae to extract", choices=allowed_vertebrae, required=True)
    parser.add_argument("-me", "--metrics", nargs="+", help="metric to extract", choices=metrics_map.keys(), required=True)
    # parser.add_argument("-im", "--images", nargs="+", help="segmentation images (PNG) to copy", choices=allowed_pngs)
    
    return parser.parse_args()


def get_metrics(df, metrics, vertebrae, case_name: str = ""):
    # rows = []
    # for vert in vertebrae:
    #     matches = df[df['level'] == vert]
    #     print(matches)
        
    
    matches = [col for col in df.columns if col in metrics]
    
    matched_df: pandas.DataFrame = df[matches]
    rows = []
    for vert in vertebrae:
        matched_vert: pandas.DataFrame = matched_df[matched_df['level'] == vert]
        if matched_vert.empty:
            row_dict = {met: (vert if met == 'level' else np.nan) for met in metrics}
            row = pandas.DataFrame([row_dict])
        else:
            row = matched_vert[metrics]
            
        row = row.copy()
        row.insert(0, 'case', case_name)
        rows.append(row)
    return pandas.concat(rows, ignore_index=True)
    

args = get_args()

in_directory = Path(args.in_directory)
csv_files = list(in_directory.rglob("muscle*.csv"))
case_names = [p.stem for p in in_directory.glob("*") if p.is_dir()]
args.metrics = ["level"] + [m for m in args.metric if m != "level"]

case_csv_paths = defaultdict(list[Path])
for path in csv_files:
    for name in case_names:
        if name in str(path):
            case_csv_paths[name].append(path)
            break

case_csv_paths = dict(case_csv_paths)
dataframes = []

for name, paths in case_csv_paths.items():
    for file in paths:
        muscle_metrics_df = pandas.read_csv(file)
        reversed_metrics_map = {v: k for k, v in metrics_map.items()}
        muscle_metrics_df.rename(columns=reversed_metrics_map, inplace=True)
        
        print(file.parts)
        
        result_df = get_metrics(muscle_metrics_df, args.metric, args.vertebrae, case_name=name)
        dataframes.append(result_df)
        
    
output_df = pandas.concat(dataframes, ignore_index=True)
output_csv = Path(args.out_directory, "comp2comp_concat_muscle_metrics.csv")
# output_df.to_csv(output_csv, sep=",", na_rep="NaN")
print(f"written concatenated metrics to {output_csv}")


