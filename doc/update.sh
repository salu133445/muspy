#!/bin/bash
#
# Build and update the documentation.
# Usage: ./update.sh

set -ex

# Find the working directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null && pwd )"

# Build documentation
rm -rf "$DIR/build"
cd "$DIR"
make html
cd -

# Remove outdated documentation
rm -rf "$DIR/../docs/"*
rm -rf "$DIR/../docs/".[!.]*

# Copy updated documentation
cp -r "$DIR/build/html/"* "$DIR/../docs"
cp -r "$DIR/build/html/".[!.]* "$DIR/../docs"
cp -r "$DIR/source/pdf/" "$DIR/../docs/"
cp -r "$DIR/source/examples/" "$DIR/../docs/"
