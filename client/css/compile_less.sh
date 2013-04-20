#!/bin/bash
echo "Compiling all LESS files to CSS"
for file in *.less
do
    FROM=$file
    TO=${file/.*/.css}
    echo "$FROM --> $TO"
    lessc $FROM $TO -x --yui-compress
done