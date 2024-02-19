Jonathan’s run_deconvolution.py deconvolution file has been modified slightly (mainly to address warnings and issues with some Python library imports). This modified file is named run_deconvolution_m.py.

In order to run  run_deconvolution_m.py, a shell script run_deconvolution_m_dialog.sh has been provided. Additionally, you will require a .csv file containing bead information and all the .ome.tif files to be deconvolved. All these files are to be contained within the same folder.

run_deconvolution_m.py
run_deconvolution_m_dialog.sh
All .ome.tif files
.csv beed file

Steps (MacOS/Linux)
1. Ensure python, flowdec, bio-formats, Anaconda/miniconda have been fully installed and working on your machine (and GPU too)
2. Open terminal
3. Change directory to folder containing above files
4. Execute chmod +x run_deconvolution_m_dialog.sh (running this command allows you to simply execute the below command each time to run deconvolution)
5. To run the bash script, execute ./run_deconvolution_m_dialog.sh
6. A dialog window will allow you select the directory containing the .ome.tif files
7. A second dialog will prompt you for the .csv bead file
8. Once you click OK, the deconvolution process begins on all your .ome.tif files present. The deconvolved files are saved in the same directory once complete.