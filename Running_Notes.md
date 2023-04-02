# Running notes on changes made after forking 
Reverse Chronological Order  
## Apr 02, 2023  --> 
- plot the reach matching gages for SWORD part on initial loda  

## Mar 25, 2023  --> merged to main multiple times
- modified sword_maps.py to match my python environment, path, and updates  
- mapping and symbology still not working on my machine  
- added gages on basin74 (by E. Altaneu)
- updated figures and legend  
- updated python packages on server
- addes statsmodels for fitting line  

## Mar 17, 2023  --> merged to Main round1 and 2
- code cleanup
- start redesign of interface overlaying USGS stage over SWOT WSE
- overlay USGS stage over SWOT WSE. 
- Added Datum as difference between minimum of SWOT and USGS_Stage
- Pulling datums from USGS using pandas and converted to meters  
- Display reachid and gage in a html div so it is selectable 

## Mar 15, 2023
- Display the gage Id correspondig to Reach.  
- convert all units to meters [as part of data download and processing]  

## Mar 14, 2023
Cloning only main on new replacement laptop

## Mar 11, 2023
ohio2 branch --> merged to main
- Selecting subset of gages with both stage and discharge IDA data  
    - some gages has only stage other had two stages with backwater. These gages are currently removed   
    - out of 33 reach-gage combination we now have only 14 remaining for visualization  
- Comment out this code after first initialization run  
- Plot SWOT, IDA, and Field Measure together
- App is very slow because scatter >15k points is known to slow down  
- Subset based on dates for reach to reduce data volume  

## Mar 03, 2023
ohio1 branch --> merged to main
- replace "time_str" field with "time" because Merrit used this field  
- Load, parse and plot Ohio River data  
- sort index (time) before plotting  
- moved download and plotting to util script  

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
 


