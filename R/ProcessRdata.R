#  Script to read in the mtu Rdata file and output the expression ratios

usage <- function() {
cat ( "
# Usage:
# 
# Windows:
# R.exe --slave --args working_dir=. rdata_file=mtu_inf_111813.RData outputfile=outputfilename < ProcessRdata.R
#
# unix:
# R --slave --args working_dir=. rdata_file=mtu_inf_111813.RData outputfile=outputfilename < ProcessRdata.R
#
#
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
  if ( is.na( options["rdata_file"] ) ) {
     cat("\nMissing required option 'rdata_file'\n");
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

setwd(options["working_dir"])
load(options["rdata_file"])
nrows <- dim(e$ratios[[1]])[[1]]
genenms <- row.names(e$ratios[[1]])
indices <- c(1:nrows)
df <- cbind(indices, genenms, e$ratios[[1]])
print(dim(df))
#setwd("/Users/mharris/Documents/work/bin/flask_stuff/mtbflask/app/static/datafiles/")
#gz1 <- gzfile("cMonkey_Mtu_ratios.csv.gz", "w")
#write.csv(df, gz1, row.names=F, quote=F)
#close(gz1)
write.table(df, options["outputfile"], sep=",", row.names=F, quote=F)

#  Write for each gene cluster to which it belongs
#df <- data.frame()
#for (i in 1:length(genenms)) { 
#    g <- genenms[i]; 
#    d <- env$clusters.w.genes(g);
#    d <- na.omit(d);
#    df <- rbind(df, c(d));
#}
#df <- cbind(genenms,df)
#nrows <- dim(df)[[1]]
#indices <- c(1:nrows)
#df <- cbind(indices,df)
#write.table(df, paste(options["outputfile"],"cluster_assign.csv", sep=""),sep=",", row.names=F, quote=F)

#  Write out biclusters to files (json format)
#wd <- paste(options["working_dir"], '/biclusters',sep="")
#setwd(wd)

library(RJSONIO)

str = "{"
for ( i in 1:(env$k.clust+1)) {

  fname <- paste("biclusters/bc_", i, ".json", sep="")
  write.table(file=fname, str, row.names=F, col.names=F, quote=F)
  genestr <- paste("\"genes\": ", toJSON(env$clusterStack[[i]]$rows), ",\n", sep="")
  write.table(file=fname, genestr, row.names=F, col.names=F, quote=F, append=T)
  #jsongenes <- toJSON(env$clusterStack[[i]]$rows)
  #write.table(file=fname, jsongenes, row.names=F, col.names=F, quote=F, append=T)
  #write.table(file=fname, ",\n'conditions': ", row.names=F, col.names=F, quote=F, append=T)
  #jsonconds <- toJSON(env$clusterStack[[i]]$cols)
  condstr <- paste("\"conditions\": ", toJSON(env$clusterStack[[i]]$cols), sep="")
  write.table(file=fname, condstr, row.names=F, col.names=F, quote=F, append=T)
  write.table(file=fname, "}", row.names=F, col.names=F, quote=F, append=T)
}


