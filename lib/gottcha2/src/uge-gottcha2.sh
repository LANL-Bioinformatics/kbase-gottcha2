#!/bin/bash
#$ -l h_vmem=100G,mem_free=40G
#$ -j y
#$ -cwd

usage(){
cat << EOF
USAGE: $0 -i <FASTQ> -o <OUTDIR> -p <PREFIX> -l <LEVEL> [OPTIONS]

ARGUMENTS:
   -i      Input a FASTQ file or pair-ended FASTAQ files sperated by comma
   -o      Output directory
   -p      Output prefix
   -l      Level [genus|species|strain]
   -d      Database

OPTIONS:
   -t      Number of threads. [default is 4]
   -a      minimap2 options
   -c      Minimum linear coverage to be considered valid in abundance calculation [default: 0.005]
   -r      Minimum number of reads to be considered valid in abundance calculation [default: 3]
   -m      Minimum mean linear read length [default: 1] (*** disabled, don't use ***)
   -z      Maximum estimated zscore of depths of mapped region [default: 10] 
   -s      Minimum unique length to be considered valid in abundance calculation [default: 60]
   -h      help
EOF
}

rootdir=$( cd $(dirname $0) ; pwd -P )

###########################
#
# Default values
#
###########################

FASTQ=
PREFIX=
OUTPATH=
LVL="species"
THREADS=4
PRE_SPLITRIM=
MIN_COV=0.005
MIN_READS=3
MIN_LEN=60
MIN_AVG_LINEAR_RL=1
MAX_ZSCORE=10
DB=/data/gottcah2/RefSeq90/RefSeq-r90.cg.BacteriaArchaeaViruses.species.fna

while getopts "i:o:p:l:d:t:a:c:r:m:z:s:h" OPTION
do
     case $OPTION in
        i) FASTQ=$OPTARG
           ;;
        o) OUTPATH=$OPTARG
           ;;
        p) PREFIX=$OPTARG
           ;;
        l) LVL=$OPTARG
           ;;
        d) DB=$OPTARG
           ;;
        t) THREADS=$OPTARG
           ;;
        a) MINIMAP2OPTS=$OPTARG
           ;;
        c) MIN_COV=$OPTARG
           ;;
        r) MIN_READS=$OPTARG
           ;;
        m) MIN_AVG_LINEAR_RL=$OPTARG
           ;;
        z) MAX_ZSCORE=$OPTARG
           ;;
        s) MIN_LEN=$OPTARG
           ;;
        h) usage
           exit
           ;;
     esac
    
done

## path
RELABD_COL="ROLLUP_DOC"
export PATH=$rootdir:$PATH;

mkdir -p $OUTPATH

set -xe;

gottcha2.py -mc $MIN_COV -mr $MIN_READS -ml $MIN_LEN -mz $MAX_ZSCORE -r $RELABD_COL -i $FASTQ -t $THREADS --outdir $OUTPATH -p $PREFIX --database $DB

awk -F\\t '{if($NF=="" || $NF=="NOTE"){print $_}}' $OUTPATH/$PREFIX.full.tsv | cut -f -10 > $OUTPATH/$PREFIX.summary.tsv
awk -F\\t '{if(NR==1){out=$1"\t"$2"\tROLLUP\tASSIGNED"; { for(i=3;i<=NF;i++){out=out"\t"$i}}; print out;}}' $OUTPATH/$PREFIX.summary.tsv > $OUTPATH/$PREFIX.out.list
awk -F\\t '{if(NR>1){out=$1"\t"$2"\t"$4"\t"; { for(i=3;i<=NF;i++){out=out"\t"$i}}; print out;}}' $OUTPATH/$PREFIX.summary.tsv >> $OUTPATH/$PREFIX.out.list

touch $OUTPATH/$PREFIX.lineage.tsv
#gottcha2.py -r $RELABD_COL --database $DB -s $OUTPATH/$PREFIX.gottcha_*.sam -m lineage -c > $OUTPATH/$PREFIX.out.tab_tree
cp $OUTPATH/$PREFIX.lineage.tsv $OUTPATH/$PREFIX.out.tab_tree
#generate KRONA chart
ktImportText  $OUTPATH/$PREFIX.out.tab_tree -o $OUTPATH/$PREFIX.krona.html

#generate Tree Dendrogram
phylo_dot_plot.pl -i $OUTPATH/$PREFIX.out.tab_tree -p $OUTPATH/$PREFIX.tree -t 'GOTTCHA2'

set +xe;
echo "";
echo "[END] $OUTPATH $PREFIX";
