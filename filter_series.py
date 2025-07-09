import os
import shutil
import argparse
from pathlib import Path
import pydicom


def get_args():
    parser = argparse.ArgumentParser(prog="filter_series.py", description="filter series")
    parser.add_argument("in_directory", type=str, help="input directory containing dicom files")
    parser.add_argument("-od", "--out_directory", type=str, help="output directory of filtered studies", default="./outdir")
    parser.add_argument("--append_study_uid", action="store_true", help="append StudyInstanceUID to patientID in directory name", default=False)
    # parser.add_argument("--series_dir_name", type=str, help="use SeriesDescription or SeriesInstanceUID as names for directories", choices=("desc", "uid"))

    return parser.parse_args()


def filter_files(ds):
    series_desc = ["report", "dose", "protocol", "topogram", "scout", "coronal", "sagital"]
    if any(sub in ds.SeriesDescription.lower() for sub in series_desc):
        return True
    
    slice_thickness = getattr(ds, "SliceThickness", None)
    if slice_thickness is None or slice_thickness > 1.0:
        return True

    if not any("primary" in image_type.lower() for image_type in list(ds.ImageType)):
        return True


args = get_args()

in_directory = Path(args.in_directory)
study_dirs = os.listdir(in_directory)
out_directory = Path(args.out_directory)
os.makedirs(out_directory, exist_ok=True)

for root, _, files in os.walk(in_directory):
    if len(files) <= 0 or "DICOMDIR" in files:
        continue
    
    series_paths: dict[str, list[Path]] = {}    
    ds = pydicom.dcmread(Path(root, files[0]))
    patient_id = getattr(ds, "PatientID", None)
    study_uid = getattr(ds, "StudyInstanceUID", None)
    
    for file in files:
        old_path = Path(root, file)
        ds = pydicom.dcmread(old_path)
        
        if filter_files(ds):
            continue

        series_key = getattr(ds, "SeriesInstanceUID")
        
        if not series_key in series_paths:
            series_paths[series_key] = []
            
        series_paths[series_key].append(old_path)

    for series_uid, paths in series_paths.items():
        if args.append_study_uid:
            patient_id += "_" + study_uid
            
        series_dir = Path(out_directory, patient_id, series_uid)
        os.makedirs(series_dir, exist_ok=True)
        
        for src_path in paths:
            dest_path = Path(series_dir, src_path.stem)
            shutil.copy2(src_path, dest_path)
        total_files = sum([len(l) for l in series_paths.values()])
    print(f"moved ID {patient_id}, {total_files} files to {Path(out_directory, patient_id)}")
        

        