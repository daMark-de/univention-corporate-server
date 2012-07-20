#!/bin/bash
#
# Run test suite for ucslint
#
declare -i RETVAL=0

while [ $# -ge 1 ]
do
    case "$1" in
    --update) update=1 ;;
    --verbose) verbose=1 ;;
    --clean) clean=1 ;;
    --quiet) quiet=1 ;;
    --color) red=$(tput setaf 1) green=$(tput setaf 2) norm=$(tput op) ;;
    --) shift ; break ;;
    -*) exit 1 ;;
    esac
    shift
done

tmpdir=$(mktemp -d)
trap "rm -rf '$tmpdir'" EXIT
tmpresult="$tmpdir/result"
tmpdiff="$tmpdir/diff"

export PYTHONPATH="$PWD:$PYTHONPATH"
BINPATH="$PWD/bin/ucslint"
UCSLINTPATH="$PWD/ucslint"

for dir in testframework/*
do
    if [ -d "$dir" ]
    then
        [ -z "$quiet" ] && echo -n "Testing $dir "

        DIRNAME=$(basename "$dir")
        MODULE="${DIRNAME:0:4}"

        ( cd "$dir" && "$BINPATH" -p "$UCSLINTPATH" -m "$MODULE" >"$tmpresult" 2>/dev/null )
        ./ucslint-sort-output.py "$tmpresult" >"${dir}.test"

        if diff -u "${dir}.correct" "${dir}.test" >"$tmpdiff" 2>&1
        then
            [ -z "$quiet" ] && echo "${green}OK{$norm}"
            [ -n "$clean" ] && rm -f "${dir}.test"
        else
            [ -z "$quiet" ] && echo "${red}FAILED${norm}"
            RETVAL+=1
            [ -n "$verbose" ] && sed "s/^+/${red}&/;s/^-/${green}&/;s/$/${norm}/" "$tmpdiff"

            if [ -n "$update" ]
            then
                echo "USING TESTRESULT AS NEW TEST TEMPLATE"
                cp "${dir}.test" "${dir}.correct"
            fi
        fi
    fi
done

exit $RETVAL
