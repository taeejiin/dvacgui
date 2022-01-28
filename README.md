# DVaCGUI

## Introduction

This was my first ever coding project built the summer (2020) before my senior year of high school. Through this endeavor, I learned Python as well as its powerful libraries, iteration over data structures with pandas, data processing, debugging techniques, and much more. The code is definitely very scrappy and could be infinitely improved on, but as a first software project I am proud of it nonetheless. For the project, I developed, iterated, and tested DVaCGUI independently as a research intern for the Greer Group at Caltech. To understand materials theory, I was mentored by Rebecca Gallivan through our discussions of scientific papers, textboook passages, lectures and selected exercises.

## Short Description of DVaCGUI

The repo consists of the core self-containing code used in the earliest model of DVaCGUI, a proprietary graphical user interface that cleans raw nanoindentation CSV data, allows highly versatile calculations including burst behavior, energy dissipation, stress/strain/Sneddon’s correction, stiffness, and is armed with simultaneous graphing capabilities supported in windows 10 OS+ and macOS X.

## General Launching & Setup Guidelines

# For MacOS X+

1. Download from dropbox
2. Open DVaCGUI.zip
3. Open DVaCGUI.app to launch the software
      * May need to allow authorization for opening software off open web

# For Windows 10 OS+

1. Download from dropbox
2. Download** PyCharm professional:
      * https://www.jetbrains.com/pycharm/download/#section=windows
      * Activate free educational license through academic institution for unlimited usage
3. Click File, then New Project
4. Select Pure Python
5. Name the file DataVisualizationAndCalculationGUI and specify a directory
6. Select the following information for Project Interpreter:
      * New environment using: Virtualenv
      * Base interpreter: Python 3.8.3
7. Click Create
8. Right click the folder that has the name of the file
9. Hover New
10. Click Python File
11. Name it main, hit enter/return on keyboard (creates main.py file)
12. Open DVaCGUI.py to open script that contains code
13. Copy code from DVACGUI.py and paste to main.py
14. Open PyCharm Preferences
15. Select Project: DataVisualizationAndCalculationGUI
16. Select Project Interpreter
17. Click the + (install) button
18. For each of the following below: search*, select, click Install Package
      * matplotlib: 3.3.1
      * pandas: 1.1.0
      * numpy: 1.19.1
      * scipy: 1.5.2
19. Once all packages added to Project Interpreter, click OK.
20. Right click the file main.py and select Run to launch the software.

## General Usage Guidelines

1. After launching software, the DVaC GUI window appears
2. Upload .csv files to GUI through Choose Select File
      * Maximum of 26 .csv files (including files parsed into multiple .csv files)
3. If the .csv file is cycle data, parse one of four ways:
      * Displacement controlled
      * Arbitrary displacement peaks
      * Load controlled
      * Arbitrary load peaks
4. For each .csv file, can click CSV File + .csv file # to open Data Calculations window
5. The windows are:
      * Main window: CSV Interface (where steps 1-4 occur)
      * Secondary window: Data Calculation
      * Tertiary window: Statistics Interface
      * Quaternary window: Weibull Distributions Interface
      * 
In Data Calculation window:
1. Choose raw data to plot with Select Abscissa and Select Ordinate drop-downs
2. For all calculations, in numeric input areas, hit enter/return on keyboard after you
input a value for the program to register the value
3. After a calculation is completed, click Refresh Options to update drop-down
menus for graphing as well as display output values and information
4. If a calculation cannot be done, a pop-up window appears that outlines what may
be missing such that the calculation cannot be done.
5. Available calculations:
      * Engineering stress-strain
      * True stress-strain
      * Young’s modulus (slope method)
      * Young’s modulus (CSM method)
      * Sneddon’s correction to Young’s modulus (CSM method)
      * Ultimate failure stress-strain
      * Energy dissipated
      * Burst events: # of bursts, lower & upper bound stress-strain of bursts, size of bursts (strain range)
6. Change domain and range of plot, then click Refresh Options to update graph
7. Export graph as .svg file
a. Name of .svg file is y-axis + units vs. x-axis + units
8. Do not dismiss Data Calculation window for update main DVaC GUI window
functionality

In CSV Interface window:

1. Choose same data for each Select Abscissa and Select Ordinate of each .csv file
2. Click Plot All to display all plots onto the same graph
3. If Data Calculation windows are open and calculations have been done using them for the .csv files, click Refresh Plot-able Options to update Select Abscissa and Select Ordinate drop-downs with calculated data
4. Change domain and range of plot, then click Refresh Plot-able Options to update graph
5. Export graph as a .svg file
      * Name of .svg file is y-axis + units vs. x-axis + units

Output of Statistics Interface window:

1. For all 8 data calculation algorithms, statistics interface stores each calculation for every uploaded data file.
2. The statistics interface calculates and displays the mean, median, standard deviation, variance, interquartile range, and outliers for the distribution of calculated data.
3. The statistics interface also displays boxplots for visualization of each mode of statistics calculated.
   
Output of Weibull Distribution window:

1. Graphical plot with 4 axes
      a. 1st X-axis: ln Stress
      b. 1st Y-axis: ln ln (1 / (1 - Probability of Fracture))
      c. 2nd X-axis: Fracture Stress (typically MPa)
      d. 2nd Y-axis: Probability of Fracture (%)
2. Displays both the weibull modulus and characteristic strength calculated from a
linear regression analysis of the graphical plot.
3. Note that the weibull distribution does not account for minimum stressed below
which the test specimen will not break. This can be included in the algorithm in
the future but would require statistical confidence analysis.
