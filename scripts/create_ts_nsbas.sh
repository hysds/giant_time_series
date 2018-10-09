#!/bin/bash
BASE_PATH=$(dirname "${BASH_SOURCE}")
BASE_PATH=$(cd "${BASE_PATH}"; pwd)

# set PGE path
PGE_PATH=$(cd "${BASE_PATH}/.."; pwd)
BIN_PATH=$PGE_PATH/scripts

# source ISCE env
export GMT_HOME=/usr/local/gmt
source $BIN_PATH/isce.sh
source $BIN_PATH/giant.sh
export GIANT_HOME=/usr/local/giant/GIAnT
export PYTHONPATH=$ISCE_HOME/applications:$ISCE_HOME/components:$PGE_PATH:$GIANT_HOME:$PYTHONPATH
export PATH=$BIN_PATH:$GMT_HOME/bin:$PATH

# source environment
source $PGE_PATH/env/bin/activate

echo "##########################################" 1>&2
echo -n "Running NSBAS-inversion displacement time series generation: " 1>&2
date 1>&2
python $BIN_PATH/create_ts_nsbas.py _context.json > create_ts_nsbas.log 2>&1
STATUS=$?
echo -n "Finished running NSBAS-inversion displacement time series generation: " 1>&2
date 1>&2
if [ $STATUS -ne 0 ]; then
  echo "Failed to run NSBAS-inversion displacement time series generation." 1>&2
  cat create_ts_nsbas.log 1>&2
  echo "{}"
  exit $STATUS
fi
