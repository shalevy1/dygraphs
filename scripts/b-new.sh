#!/bin/mksh
set -e
header=$1

rm -rf disttmp2
mkdir disttmp2
pax -rw -l node_modules src disttmp2/

babel \
  --compact false \
  --source-maps inline \
  -d disttmp2 \
  LICENCE.js

cd disttmp2
PATH=$PWD/node_modules/.bin:$PATH

babel \
  --compact false \
  --source-maps inline \
  -d es5 \
  src
rm -rf src

# we could, in theory, remove the last line //# sourceMappingURL=…
# from these files to make into src-es5/ now, would be identical
# otherwise to whatever b-old.sh generated… but then, why not keep
# these maps for users who need to debug especially the extras?

cp -r es5 src
browserify \
  -v \
  -t [ envify --NODE_ENV development ] \
  --debug \
  --standalone Dygraph \
  LICENCE.js \
  src/dygraph.js \
  >dygraph.tmp.js
../scripts/smap-out.py dygraph.tmp.js dygraph.js dygraph.js.map

#cp -r es5 src
browserify \
  -v \
  -t [ envify --NODE_ENV production ] \
  --debug \
  --standalone Dygraph \
  src/dygraph.js \
  >dygraph.min.tmp.js
../scripts/smap-out.py dygraph.min.tmp.js /dev/null dygraph.min.tmp.js.map

uglifyjs --compress --mangle \
  --preamble "$header" \
  --in-source-map dygraph.min.tmp.js.map \
  --source-map-include-sources \
  --source-map dygraph.min.js.map \
  -o dygraph.min.js \
  dygraph.min.tmp.js

cd ..
