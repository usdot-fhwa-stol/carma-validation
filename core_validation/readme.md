# Scripts for core validation testing
## Setting up in the EC2 instance
### Connecting GitHub to Visual Studio Code
Steps:
1. Open Visual Studio Code from the Start menu.
2. Click "clone repository" and then "Clone from GitHub". Sign in to GitHub.
3. Type `usdot-fhwa-stol/carma-validation` and choose a location to store it in locally.
4. Open `lexus_plots.py` and click yes when it asks you to install the Python extension.
### Python packages
We used a few extra packages beyond what was pre-installed. In particular, geopandas is tricky to install, so some of the dependencies were downloaded from https://www.lfd.uci.edu/~gohlke/pythonlibs/.

Run the following in the command line before running `lexus_plots.py`
- `pip install matplotlib`
- `pip install "C:\Users\Public\Documents\packages\GDAL-3.2.2-cp38-cp38-win_amd64.whl"`
- `pip install "C:\Users\Public\Documents\packages\Fiona-1.8.18-cp38-cp38-win_amd64.whl"`
- `pip install geopandas`
- `pip install mpld3`


## after running the scripts
upload plots to the s3 bucket by opening a command line and running
- `cd C:\Users\public\documents\outplots`
- `aws s3 sync ./ s3://volpe-core-validation-results/output-plots/`
