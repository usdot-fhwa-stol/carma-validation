# Scripts for core validation testing
## Setting up in the EC2 instance
### Connecting GitHub to Visual Studio Code
Steps:
1. Open Visual Studio Code from the Start menu.
2. Click "clone repository" and then "Clone from GitHub". Sign in to GitHub.
3. Type `usdot-fhwa-stol/carma-validation` and choose a location to store it in locally.
4. Open `generate_plots.py` and click yes when it asks you to install the Python extension.
### Python packages
We used a few extra packages beyond what was pre-installed. In particular, geopandas is tricky to install, so some of the dependencies were downloaded from https://www.lfd.uci.edu/~gohlke/pythonlibs/.

Run the following in the command line before running `generate_plots.py`:
```
pip install matplotlib
pip install "C:\Users\Public\Documents\packages\GDAL-3.2.2-cp38-cp38-win_amd64.whl"
pip install "C:\Users\Public\Documents\packages\Fiona-1.8.18-cp38-cp38-win_amd64.whl"
pip install geopandas
pip install mpld3
```

## running the script
To run the file scroll all the way to these lines -- (the final two lines, except for the commented-out bits at the end.)
```
generate_plots_for_run()
plt.show()
```
You will need to choose your parameters for `generate_plots_for_run`. 
- run. The name of the run you want to look at. For example, `run="LS_LS_SMPL_v3.5.1_r11"`. Note that the script currently assumes you're plotting data from the week of 3/15; once April data is available we'll need to adjust this.
- plots. By default, the script generates seven plots. Full documentation of the topics selected, axes used, etc. is on the Volpe HW40 Teams channel. You can generate a subset of these plots by specifying their numbers in a list, e.g., `plots=[4,5,6]`. If you want them all, you can just omit this parameter. 
	- Figure 0. state of CARMA system (always generated, even if not specified)
	- Figure 1. speed, commanded vs actual
	- Figure 2. linear accel, commanded limits vs actual
	- Figure 3. crosstrack distance from vehicle centroid to center dashed line
	- Figure 4. throttle pct actual vs commanded
	- Figure 5. steering angle actual vs commanded
	- Figure 6. brake pct actual vs commanded
- save_figs. Options are `png` or `html`, anything else (including omitting it) means that plots are not saved. The save locations are hardcoded in for now, in C:\Users\Public\Documents.

## after running the script
if you set `save_figs="png"`, you can 
upload those plots to the s3 bucket by opening a command line and running
```
cd C:\Users\public\documents\outplots`
aws s3 sync ./ s3://volpe-core-validation-results/output-plots/
```
