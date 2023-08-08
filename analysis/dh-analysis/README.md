
This R project is composed of four files:

.Rprofile
111_Functions.Rmd
111_Report_A_prep.Rmd
111A_Report_Offense.Rmd

These files should be located in the same folder, which is presumed to be the R project folder.

The .Rprofile contains 'require' statements naming all the required packages. It also contains several constants used by the Rmd programs. These are:

csvPath - path to the csv files described below.
RDataPath - the folder to which the Rmd programs write output that may be subsequently used as input.
FILE_DATE - such as, "2023-07-30", that specify the csv files to be used as input.
CURRENT_DATE - reserved for future use.

The style of programming is based on that used in biostatistics, where there are an alternating series of "data" and "program" steps. Each program step produces a data file that is subsequently written to the RDataPath folder as an RData file. With a few exceptions, the program steps use functions that are defined in 111_Functions.Rmd and located in the functions.RData file. Generally, complex program steps are avoided and broken into a series of simpler steps. While this results in multi-step processes, it allows for verification of intermediate results and supports confidence in the results of analyses as new data is added.

The necessary data csv data files are:

charge_definitions-2023-07-09.csv
daily_charges-2023-07-09.csv
2023-07-30-all-stays-summarized.csv
daily_inmates-2023-07-09.csv
stays-2023-07-09.csv

The format of the file names are those provided by the project owner and the date part may move from head to tail or vice versa. If only the 111_Report_A_prep.Rmd and 111A_Report_Offense.Rmd programs are used, the only csv data files required are charge_definitions-2023-07-09.csv and 2023-07-30-all-stays-summarized.csv, and the others my be not there at all.

RUNNING THE REPORT

The 111_Functions.Rmd program needs to be run at least once, and if changes are made changes to the plot functions.

The 111_Report_A_prep.Rmd program needs to be run each time a change is made to a function (in 111_Functions.Rmd) or if a csv data file is changed.

The 111A_Report_Offense.Rmd program uses files produced in 111_Report_A_prep.Rmd. If only the report appearance is altered, 111A_Report_Offense.Rmd may be run without rerunning 111_Report_A_prep.Rmd.

