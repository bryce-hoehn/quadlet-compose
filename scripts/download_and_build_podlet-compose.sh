#!/bin/sh

# Delete repository dir
rm -rf podlet-compose-src

# Clone repository
git clone https://github.com/bryce-hoehn/podlet-compose podlet-compose-src

# Generate binary
sh podlet-compose-src/scripts/generate_binary_using_dockerfile.sh

# Move binary outside repo's dir
mv podlet-compose-src/podlet-compose .

# Delete repository dir
rm -rf podlet-compose-src