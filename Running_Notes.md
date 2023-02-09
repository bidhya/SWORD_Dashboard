# Running notes on changes made after forking 
Reverse Chronological Order  

## Feb 03, 2023
Merged v0_4_sample_ts branch to main
- plot reach level sample timeseries SWOT data
- nodes not yet plotted

## Jan 29, 2023
Merged v0_3_connect_reach_to_gage branch to main
- Map out USGS gage from SWORD Reaches using a csv files created from the nc file shared by Steve
- uses this file: reach_gage_mapping.csv
- basin 73 hard-coded for prototpying
- download and save field_measurements data from USGS
- No downloading if csv file is already saved previously

## Dec 30, 2022
Forked repo  
copy paste "data" folder to this repo  
edit .gitignore to remove "/data" and add ".DS_Store"  
Create a .gitignore inside the "data" folder to ignore nc files and html files. This keep an almost empty data folder  
Add .flake8 to ignore some python PEP warnings on vscode  
 


