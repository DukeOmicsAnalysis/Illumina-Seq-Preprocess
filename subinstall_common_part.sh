# This file should be sourced by any 'install_part' script in a pipeline-part directory.
#
# Expects variables:
#   pipeline_part_name -- name of pipiline-part (used in messages)
#   projdir -- command-line parameter
#   projscriptsdir -- $projdir/scripts


if [ $(id -ng) != "omicscore" -o $(umask) != "0007" ]; then
    echo "ERROR: This script should be executed with group=omicscore and umask=0007."
    exit 1
fi

if [ -z "$pipeline_part_name" ]; then
    echo "INTERNAL ERROR: variable 'pipeline_part_name' is not set."
    exit
fi
if [ -z "$projdir" ]; then
    echo "INTERNAL ERROR: variable 'projdir' is not set."
    exit
fi
if [ -z "$projscriptsdir" ]; then
    echo "INTERNAL ERROR: variable 'projscirptsdir' is not set."
    exit
fi

if [ ! -d "$projscriptsdir" ]; then
    echo "ERROR: directory does not exist: $projscriptsdir"
    exit
fi

echo "Installing $pipeline_part_name pipeline scripts:"
