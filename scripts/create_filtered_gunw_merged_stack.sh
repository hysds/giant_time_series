#!/bin/bash
BASE_PATH=$(dirname "${BASH_SOURCE}")
BASE_PATH=$(cd "${BASE_PATH}"; pwd)

# set PGE path
PGE_PATH=$(cd "${BASE_PATH}/.."; pwd)
BIN_PATH=$PGE_PATH/scripts

# move symlinked products
INPUT_DIR=orig_symlinked_inputs
if [ ! -d "$INPUT_DIR" ]; then
   mkdir $INPUT_DIR
   mv S1-GUNW-MERGED* $INPUT_DIR/
   cd $INPUT_DIR
   cp -aL S1-GUNW-MERGED* ..
   cd ..
fi

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
echo -n "Running filtered interferogram stack generation: " 1>&2
date 1>&2
python $BIN_PATH/create_filtered_gunw_merged_stack.py _context.json > create_filtered_gunw_merged_stack.log 2>&1
STATUS=$?
echo -n "Finished running filtered interferogram stack generation: " 1>&2
date 1>&2
if [ $STATUS -ne 0 ]; then
  echo "Failed to run filtered interferogram stack generation." 1>&2
  cat create_filtered_gunw_merged_stack.log 1>&2
  echo "{}"
  exit $STATUS
fi

# copy log to dataset
cp create_filtered_gunw_merged_stack.log filtered-gunw-merged-stack*/

