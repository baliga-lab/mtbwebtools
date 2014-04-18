#  Script to read in the mtu Rdata file and output the expression ratios

usage <- function() {
cat ( "
# Usage:
# 
# Windows:
# R.exe --slave --args working_dir=. csb_file=mtu_inf_111813.csv outputfile=outputfilename < ProcessingRatiosCSV2JSON.R
#
# unix:
# R --slave --args working_dir=. csv_file=mtu_inf_111813.csv outputfile=outputfilename < ProcessingRatiosCSV2JSON.R
#
# General options:
#  csv_file   (req) - the csv file made by ProcessRdata
#  working_dir      (req) - directory containing input and where output will go

" );
quit();
}

getOptions <- function( cmd_args ) {

  anames <- c();
  avalues <- c();
  argidx <- 1;

  # Read command line arguments
  skip = TRUE;
  for( i in commandArgs() ) {
    if ( i == "--args" ){
      skip = FALSE;
      next;
    }

    # Command args also has R-specific args, we don't want them
    if ( skip ) next;

    ta = strsplit(i,"=",fixed=TRUE)
    if(! is.na(ta[[1]][2])) {
      avalues[argidx] = ta[[1]][2];
      anames[argidx] = tolower(ta[[1]][1]);
    }
    else {
      print( "Arguments must be of the form name=value, quitting" );
      quit();
    }
    argidx = argidx + 1;
  }

  # Problem if no args defined
  if ( argidx == 1 ) {
    avalues[1] = "help";
    anames[1] = "help";
  }

  names(avalues) <- anames;
  return( avalues );

} # End getOptions() 

checkOptions <- function( options ) {

  # Check for required parameters
  if ( is.na( options["csv_file"] ) ) {
     cat("\nMissing required option 'csv_file'\n");
     usage();
  }
  if ( is.na( options["working_dir"] ) ) {
     cat("\nMissing required option 'working_dir'\n");
     usage();
  }
  if ( is.na( options["outputfile"] ) ) {
     cat("\nMissing required option 'outputfile'\n");
     usage();
  }

    return( options );
}

  # Fetch command-line options
options <- getOptions();

# Check options
options <- checkOptions(options);

library(RJSONIO)

setwd(options["working_dir"])

cat0 <- function(file, ...) cat(..., sep="", file=file)
cat0a <- function(file, ...) cat(..., sep="", file=file, append=TRUE)

data <- read.delim(options["csv_file"], sep=',')
labels <- data[,2] # Gene names
print(labels)
data <- data[,3:length(colnames(data))] # The ratio values
times <- c(1:dim(data)[2])
file <- options["outputfile"]
cat0(file, "{\n")
cat0a(file, "\"labels\" : \n", toJSON(labels), ",\n\n")
cat0a(file, "\"times\" : \n", toJSON(times), ",\n\n")
str <- ""
for ( i in 1:dim(data)[1]) {
  row <- as.numeric(data[i,])
  row[which(is.na(row))] <- 0
  if (i != dim(data)[1]) {
    row <- paste(toJSON(row),",\n",sep="")
    str <- paste(str, row, sep="")
  } else {
    row <- paste(toJSON(row),"\n",sep="")
    str <- paste(str, row, sep="")
  }
}
cat0a(file, "\"curves\" : \n[", str, "]\n\n")
cat0a(file, "}\n")


