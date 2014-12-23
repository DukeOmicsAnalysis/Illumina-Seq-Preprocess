#
# Common part of all other scripts:
# Do some checks and prepare environment
#
# Should be 'source'd by other scripts.
#
# Variable '$scriptdir' must be set by outer script
# (it is needed to source this file, anyway)

if [ $(id -ng) != "omicscore" -o $(umask) != "0007" ]; then
    echo "ERROR: This script should be executed with group=omicscore and umask=0007."
    exit 1
fi

projdir=$(dirname $(readlink -m $scriptdir))

export PROJDIR=$projdir

if [ "$1" = "-vvv" ]; then
    export VERBOSITY_LEVEL=3
    shift
elif [ "$1" = "-vv" ]; then
    export VERBOSITY_LEVEL=2
    shift
elif [ "$1" = "-v" ]; then
    export VERBOSITY_LEVEL=1
    shift
elif [ "$1" = "-" ]; then
    export VERBOSITY_LEVEL=0
    shift
else
    export VERBOSITY_LEVEL=0
fi

if [ $VERBOSITY_LEVEL != "0" ]; then
    echo "Versbosity: $VERBOSITY_LEVEL.  Project directory: $PROJDIR"
fi

