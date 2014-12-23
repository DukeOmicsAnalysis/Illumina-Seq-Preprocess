# This file should be sourced by any 'install' script in a pipeline directory.
#
# It copies '*.temlate' files to original files if not exist. 
#
# Expects variables:
#   projdir -- command-line parameter
#   projscriptsdir -- $projdir/scripts

echo "Handling '*.template' files..."

for f in $(find $projscriptsdir -type f -name '*.template'); do
    f0=${f%.template}
    if [ ! -f "$f0" ]; then
        cp $f $f0
    fi
done
