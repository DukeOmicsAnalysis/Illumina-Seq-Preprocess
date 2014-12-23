# This file should be sourced by any 'install' script in a pipeline directory.
#
# Expects variables:
#   pipeline_name -- name of pipiline (used in messages)
# Sets variables:
#   projdir -- command-line parameter
#   projscriptsdir -- $projdir/scripts


if [ $(id -ng) != "omicscore" -o $(umask) != "0007" ]; then
    echo "ERROR: This script should be executed with group=omicscore and umask=0007."
    exit 1
fi


echo "=== Installing $pipeline pipeline scripts"

printUsage () {
    echo "Usage:"
    echo "      install  destination/projects/directory"
    echo "(destdir should not include 'scripts')"
}

# Check parameters and destination directory

if [ -z "$1" ]; then
    printUsage
    exit
fi

export projdir=$(readlink -m $1)
export projscriptsdir=$projdir/scripts
echo "Destination project directory: $projdir"

if [ ! -d "$projdir" ]; then
    echo "ERROR: Project directory does not exist"
    exit
fi
if [ -d "$projscriptsdir" ]; then
    if [ -n "$(ls -A  $projscriptsdir)" ]; then
        if [ "$2" == "force" ]; then
            echo "Overwriting existing scripts directory"
        else
            echo "ERROR: scripts directory is not empty."
            echo "Use second argument 'force' if you want to overwrite scripts."
            exit
        fi
    else
        echo "Using existing scripts directory"
    fi
else
    echo "Creating new scripts directory"
    mkdir "$projdir/scripts"
fi
