#!/bin/bash

# shellcheck disable=shellcheck-x
set -o errexit   # abort on nonzero exitstatus
set -o nounset   # abort on unbound variable
set -o pipefail  # don't hide errors within pipes
shopt -q -s checkwinsize

# CONFIGURATION ###########################################
# paths -- experiment host
PATH_GIT_REPOS_ROOT="/$HOME/git"
PATH_EXP_CODE_DIR="scope-systematic-bit-flipping"
PATH_XMLDIG2CSV="${PATH_GIT_REPOS_ROOT}/xmldig2csv-converter/xmldig2csv"
PATH_DATA_MOUNT="/data/projects/ddr5-scope-data-shared"
PATH_EXP_EXEC_DIR="${HOME}/ddr5-exp"
# this path is passed to the experiment code to start the scope acquisition script
export PATH_TELEDYNE_REPO="/$HOME/git/teledyne-scope/"
# paths -- decoding host
PATH_DECODER_SCRIPTS_DIR="/$HOME/git/teledyne-scope/scripts/"

# executables and command line options
PY="/usr/bin/python3.8"
EXP_EXEC="experiment"
SSH_OPTIONS="-q -o PreferredAuthentications=publickey"

# other settings
# if the RAMDISK is 90% full, then we copy stuff to the server
MAX_RAMDISK_RATIO="90"

# input
DIMM_ID=511
# the scope setup file must be created with the scope GUI; it contains the digitizer thresholds and the labels for the digital lines that are captured
SCOPE_SETUP_FILE="F:\\\scope\\\setups\\\setup_correct_refreshes_finegrain--00021-all-795mv.lss"

# output
EXP_OUTPUT_FILE="exp_cfg.csv"

# this required that pubkey auth to this server has been set up
SCOPE_IP_ADDR="172.31.200.250"
SCOPE_SSH_USER="root"
SCOPE_SSH="${SCOPE_SSH_USER}@${SCOPE_IP_ADDR}"

ETHZ_LDAP_USERNAME="${USER}"

# storage server: fetches data from scope
# this required that pubkey auth to this server has been set up
RESEARCH_HEADNODE_IP_ADDR="172.31.200.194"
RESEARCH_HEADNODE_SSH="${ETHZ_LDAP_USERNAME}@${RESEARCH_HEADNODE_IP_ADDR}"

# powerful server: decodes and plots data
DECODER_HOST_IP_ADDR="ee-tik-cn107.ethz.ch"
DECODER_HOST_SSH="${ETHZ_LDAP_USERNAME}@${DECODER_HOST_IP_ADDR}"

Q_WORKLOAD2TRIGGER="/tmp/workload2trigger"
Q_TRIGGER2WORKLOAD="/tmp/trigger2workload"
Q_WORKLOAD2RUNNER="/tmp/workload2runner"
###########################################################

# make pushd, popd silent
pushd () { command pushd "$@" > /dev/null ; }
popd () { command popd > /dev/null ; }

# print message with custom prefix
echof_n () {
  C_FG='\033[0;32m'
  C_NC='\033[0m'
  date=$(date "+%H:%M:%S:%m.%N")
  printf "${C_FG}[$(basename ${0})|${date%???}]${C_NC} $*"
  # printf "[$(basename ${0})|${date%???}] $*"
}

echof () {
  echof_n $@ "\n"
}

check_prepare_host () {
  set +u
  if [ -n "${HOST_ACQ_READY}" ] && [ "${HOST_ACQ_READY}" == "1" ]; then
    return;
  fi
  set -u

  # make sure xmldig2csv is present
  #if [ ! -f "${PATH_XMLDIG2CSV}" ]; then
  #    echof "xmldig2csv not found! Please build xmldig2csv and rerun this script."
  #    exit 1
  #else
  #    echof "xmldig2csv found: ${PATH_XMLDIG2CSV}"
  #fi

  # make sure the default ftdi module is not loaded as it conflicts with our ftdi module
  set +e
  lsmod | grep ftdi_sio
  if [ "$?" == "0" ]; then
      echof "ftdi_sio found and unloaded"
      rmmod ftdi_sio &>/dev/null
  fi
  set -e

  # make sure that we can connect to the scope via SSH
  set +e  # otherwise things will fail due to "set -e -o pipefail" above
  pkill --signal SIGKILL ssh-agent
  ssh ${SSH_OPTIONS} ${SCOPE_SSH} hostname &>/dev/null; ssh_key_available="$?"
  if [ "${ssh_key_available}" -ne "0" ]; then
      echof "ERROR: could not connect to oscilloscope: ssh key missing?"
      exit 1
  else
      echof "connection to oscilloscope (${SCOPE_SSH}) successful!"
  fi
  set -e

  export HOST_ACQ_READY=1
}

get_available_ramdisk_space () {
   ssh -q ${SCOPE_SSH} << 'EOF'
      usage=$(df /mnt/r | tail -n1 | tr -s ' ')
      total=$(echo $usage | cut -d' ' -f4)
      used=$(echo $usage | cut -d' ' -f3)
      python3 -c "print(int(($used/$total)*100))"
EOF
}

cleanup_ramdisk () {
  # clean up RAMDisk (empty folders) on scope
  ssh ${SSH_OPTIONS} ${SCOPE_SSH} "find /mnt/r/ -empty -not -path '*/System Volume Information*' 2>/dev/null | xargs rm -rf ; exit 0"
}

copy_nfs_cleanup () {
  # Pull data from scope to NFS share.
  # This is currently done via the experiment host, but it would be faster do
  # pull directly from the research cluster headnode, to avoid the NFS overhead.
  # The commented-out ssh command below could be used to acheive this.

  echof "copying data to server"
  rsync -W --no-compress --exclude 'System Volume Information' \
      --remove-source-files \
      -aq /mnt/scope-ramdisk/* "$PATH_DATA_MOUNT/${TARGET_DIR}/" &>/dev/null

  # ssh ${SSH_OPTIONS} ${RESEARCH_HEADNODE_SSH} \
	# 	"rsync -W --no-compress --exclude 'System Volume Information' -aq /mnt/scope-ramdisk/* /srv/nfs4/clusterdata/projects/ddr5-scope-data/${TARGET_DIR}/" \
	# 	&>/dev/null
  cleanup_ramdisk
}

# ----------------------------------------------------------------

# stop any instances of blacksmith that might still be running
echof "stopping any instances of trigger/workload that might still be running"
set +e
pgrep -u "$USER",root "$EXP_EXEC" | xargs -I@ sudo kill --signal SIGKILL @
set -e

check_prepare_host

# manual abort of this script kills the experiment executable and cleans the ramdisk on the scope
trap "echof '[!] received request to terminate, please hold on...'; tput init; sudo pkill -f ${EXP_EXEC}; ssh ${SSH_OPTIONS} ${SCOPE_SSH} 'rm -rf /mnt/r/*.XMLdig' &>/dev/null; exit 1" SIGINT SIGTERM

# Take the experiment comment from the command line, if it exists, or prompt otherwise.
if [ -n "${1-}" ]; then
  EXP_COMMENT="$1"
else
  read -e -p "[>] experiment name: " EXP_COMMENT
fi

# create experiment dir
mkdir -p "${PATH_EXP_EXEC_DIR}"

# copy test programs and setup scripts to remote machine
echof "copying $PATH_EXP_CODE_DIR INCLUDING targets.txt to ${PATH_EXP_EXEC_DIR}/"
rsync --no-compress --exclude CMakeCache.txt --exclude CMakeFiles -avq ${PATH_GIT_REPOS_ROOT}/${PATH_EXP_CODE_DIR}/* "${PATH_EXP_EXEC_DIR}/"
echof "copying teledyne-scope/decoder to ${PATH_EXP_EXEC_DIR}/"
rsync -avq --no-compress --exclude venv "${PATH_GIT_REPOS_ROOT}/teledyne-scope/decoder" ${PATH_EXP_EXEC_DIR}/

# cleanup decoder logs
#echof "cleaning up $(pwd)/decoder/logs/*"
#rm -rf decoder/logs/*

# we need to setup the venv twice: once for us (e.g., for calling configure.py) [NOT AUTOMATED] and once for Blacksmith (e.g., so it can call acquire.sh to start/stop acquisition)
# setup venv required to run python scripts; this requires
#   - pip to be installed (python -m ensurepip --upgrade),
#   - python >= 3.9,
#   - pip packages installed: python3-vxi11, wheel
if [ ! -d "${PATH_EXP_EXEC_DIR}/decoder/venv" ]; then
    echof "installing Python venv in /decoder directory and installing required packages"
    pushd "${PATH_EXP_EXEC_DIR}/decoder"
    python -m venv venv
    source venv/bin/activate; 
    python -m pip install -r requirements.txt
    deactivate
    popd
fi

## build 
pushd "${PATH_EXP_EXEC_DIR}"
cmake -S . -B build && cmake --build build
mv build/experiment .
popd

# main dir for this experiment run's results
ts=$(date +"%Y%m%d_%H%M%S")
TARGET_DIR="${ts}_${HOSTNAME}_DIMM=${DIMM_ID}_${EXP_COMMENT}"
TARGET_PATH="${PATH_DATA_MOUNT}/${TARGET_DIR}"
mkdir -p "${TARGET_PATH}"
echof "created experiment's target dir: $TARGET_PATH"

# exports for the decoder
export XMLDIG2CSV_PATH="${PATH_XMLDIG2CSV}"
export XMLDIG_DIR="${PATH_DATA_MOUNT}/${TARGET_DIR}"
export DATA_DIR="${XMLDIG_DIR}/data"

# load the setup file on the scope only one time
# then delete the first trace file trace-00000.XMLdig as this has been created during setup while
# the workload was not running yet
pushd "${PATH_TELEDYNE_REPO}"
source "${PATH_EXP_EXEC_DIR}/decoder/venv/bin/activate" && python ./decoder/configure.py --setup-file "${SCOPE_SETUP_FILE}"
popd

# make sure ramdisk is empty before beginning to start acquiring data
ssh ${SSH_OPTIONS} ${SCOPE_SSH} "rm -rf /mnt/r/*.XMLdig 2>/dev/null; exit 0" &>/dev/null

# set up queues
echof "setting up FIFO queues for IPC"
set +e
sudo rm -f ${Q_WORKLOAD2TRIGGER}
sudo rm -f ${Q_TRIGGER2WORKLOAD}
sudo rm -f ${Q_WORKLOAD2RUNNER}
set -e
mkfifo ${Q_WORKLOAD2TRIGGER}
mkfifo ${Q_TRIGGER2WORKLOAD}
mkfifo ${Q_WORKLOAD2RUNNER}
chmod 0777 ${Q_WORKLOAD2TRIGGER}
chmod 0777 ${Q_TRIGGER2WORKLOAD}
chmod 0777 ${Q_WORKLOAD2RUNNER}

# start the WORKLOAD process
pushd "${PATH_EXP_EXEC_DIR}"
source ./decoder/venv/bin/activate

sudo ./experiment --superpages 8 --offset 2048 --uncached-mem --num 16 --keep-fixed "0x3fffc0040=0" &
BS_WORKLOAD_PID=$!
echof "started workload process (PID ${BS_WORKLOAD_PID})"
popd

# wait for the workload process to build (or load) the conflict clusters
while IFS= read -r -n1 c; do
  if [ "$c" == "\x01" ]; then
     echof "workload is ready for experiment!"
     break
  fi
  sleep 1
done < ${Q_WORKLOAD2RUNNER}

cleanup_ramdisk

all_subdirs=()
it=0
# workload is still running => there are untested addresses left
while ps -p ${BS_WORKLOAD_PID} >/dev/null
do
    it_ext=$(printf %05d $it)
    SUBDIR="it=${it_ext}"
    echof "===== running experiment iteration ${it} ======"

    # start the TRIGGER process
    (
    pushd "${PATH_EXP_EXEC_DIR}"
      # This can probably go away.
      source ./decoder/venv/bin/activate;
      # Time out the trigger process after 3 minutes.
      sudo timeout -v 3m ./experiment --trigger
      if [ "$?" -eq 124 ]; then
        echof "TIMEOUT for trigger process: Exiting script..."
        kill -9 ${BS_WORKLOAD_PID}
        exit 124
      fi
      deactivate
    popd
    ) 

    NUM_XMLDIG_FILES=$(ssh ${SCOPE_SSH} "ls -la /mnt/r/*.XMLdig | wc -l")
    if [ "${NUM_XMLDIG_FILES}" == "0" ]; then
        echof "acquisition failed. retrying.. "
        continue
    fi

    # copy experiment configuration (exp_cfg.csv) to the network drive
    echof "copying experiment configuration to experiment dir"
    rsync "${PATH_EXP_EXEC_DIR}/${EXP_OUTPUT_FILE}" "${PATH_DATA_MOUNT}/${TARGET_DIR}/${SUBDIR}/"

    # move acquired data into subdirectory on RAMDisk
    ssh ${SSH_OPTIONS} ${SCOPE_SSH} "mkdir -p /mnt/r/${SUBDIR} && mv /mnt/r/*.XMLdig /mnt/r/${SUBDIR}"

    USED_RATIO=$(get_available_ramdisk_space)
    if (( "${USED_RATIO}" > "90" )); then
      echof "used RAMDisk space: ${USED_RATIO}%%, copying data to NFS share"
      copy_nfs_cleanup
    else
      echof "enough free RAMDisk space available, used: ${USED_RATIO}%%"
    fi

    # remember subdirectories
    all_subdirs+=( "${SUBDIR}" )

    # update iteration counter
    it=$((it+1))
done

# COPYING REMAINDER
echof "copying remaining files to NFS server"
copy_nfs_cleanup

# DECODING
echof "decoding data on ${DECODER_HOST_IP_ADDR}...";
ssh ${SSH_OPTIONS} ${DECODER_HOST_SSH} "cd ${PATH_DECODER_SCRIPTS_DIR}; ./decode_parallel.sh ${TARGET_PATH}; exit 0"
