#!/bin/sh

# Delete repository dir
rm -rf quadlet-compose-src

# Clone repository
git clone https://github.com/bryce-hoehn/quadlet-compose quadlet-compose-src

# Generate binary
sh quadlet-compose-src/scripts/generate_binary_using_dockerfile.sh

# Move binary outside repo's dir
mv quadlet-compose-src/quadlet-compose .

# Delete repository dir
rm -rf quadlet-compose-src