usage <- function() {
cat ( "
# Usage:
# 
# Windows:
# R.exe --slave --args working_dir=. input_file=input.csv outputfilehc=afilename.csv outputfilelab=afilename.js username=username < HeatmapData.R
#
# unix:
# R --slave --args working_dir=. input_file=input.csv outputfilehc=afilename.csv outputfilelab=afilename.js username=username < HeatmapData.R
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
  if ( is.na( options["input_file"] ) ) {
     cat("\nMissing required option 'input_file'\n");
     usage();
  }
  if ( is.na( options["working_dir"] ) ) {
     cat("\nMissing required option 'working_dir'\n");
     usage();
  }
  if ( is.na( options["outputfilehc"] ) ) {
     cat("\nMissing required option 'outputfilehc'\n");
     usage();
  }
if ( is.na( options["outputfilelab"] ) ) {
     cat("\nMissing required option 'outputfilelab'\n");
     usage();
  }
    return( options );
}

  # Fetch command-line options
options <- getOptions();

# Check options
options <- checkOptions(options);

setwd(options["working_dir"])


library(RJSONIO)
library(pvclust)
hcdata <- read.delim(options["input_file"],sep=",", header=T, row.names=1)

#  Cluster conditions
hcdatanona <- hcdata[,colSums(!is.na(hcdata))>=2 ]
hc <- pvclust(hcdatanona, method.hclust="ward", method.dist="euclidean", r=seq(0.8,1.4,by=.2)) # pvclust is NA resistant clustering method
hcrows <- toJSON(hc$hclust$order)

# Cluster genes
hcdataT <- t(hcdata) # Genes are cols Conditions are rows
hcdataTnona <- hcdataT[,colSums(!is.na(hcdataT))>=2 ]
hcT <- pvclust(hcdataTnona, method.hclust="ward", method.dist="euclidean", r=seq(0.8,1.4,by=.2))
hccols <- toJSON(hcT$hclust$order)

#  Order data according to clustering of genes (columns)
#orderedDataMatrix <- hcdataTnona[,hcT$hclust$order]

rowstrs <- c()	
row <- 1
for (i in 1:dim(hcdataTnona)[[1]]) {
	col <- 1
	rowdata <- hcdataTnona[i,] # a set of gene values for a condition
	for (j in 1:length(rowdata)) {
		coldata <- rowdata[j]
		rowstrs <- c(rowstrs, paste(i,',',j,',',coldata, sep=""))
	}
}

header <- c("row_idx,col_idx,log2ratio")
write.table(file=options["outputfilehc"], header, row.names=F, col.names=F, quote=F)
write.table(file=options["outputfilehc"], rowstrs, row.names=F, col.names=F, quote=F, append=T)

str1 <- paste("var hcrow = ",hcrows,sep="")
str2 <- paste("var hccol = ", hccols, sep="")
str3 <- paste("var colLabel = ", toJSON(hcT$hclust$labels)) #[hcT$hclust$order])) # Genes
str4 <- paste("var rowLabel = ", toJSON(hc$hclust$labels )) #[hc$hclust$order])) # Conditions

rowstrs <- c(str1,str2,str3,str4)
write.table(file=options["outputfilelab"], rowstrs, row.names=F, col.names=F, quote=F)

#pngfilename1 <- paste("hccols_",options["username"],".png",sep="") # Genes
#pngfilename2 <- paste("hrows_",options["username"],".png",sep="") # Conditions
#png(pngfilename1, height=480, width=(48*length(hcT$hclust$labels)), units="px", res=200 )
#png(pngfilename1)
#plot(hcT, hang=-1)
#dev.off()
#png(pngfilename2, height=480, width=(48*length(hc$hclust$labels)), units="px", res=200 )
#png(pngfilename2)
#plot(hc, hang=-1)
#dev.off()
