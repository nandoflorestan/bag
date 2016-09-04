#! /bin/sh

trash docs/docs.zip

cd docs/build/html/ && \
zip -r ../../docs.zip * && \
cd - > /dev/null && \
echo "To inspect the archive, type:  xdg-open docs/docs.zip"
