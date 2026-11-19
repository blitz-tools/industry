#!/usr/bin/env bash
# Full-page screenshots of the mockups (page is taller than the monitor,
# so a normal screenshot tool won't work -- headless Firefox captures the
# entire page height instead).
#
# Usage: ./take-screenshots.sh [width]
# Output: design/typhoon/screenshots/<name>.png

set -euo pipefail

width="${1:-1440}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
out_dir="$script_dir/screenshots"
profile="$(mktemp -d /tmp/ff-headless.XXXXXX)"

trap 'rm -rf "$profile"' EXIT

mkdir -p "$out_dir"

for html in "$script_dir"/*.html; do
    name="$(basename "$html" .html)"
    echo "Capturing $name.html -> screenshots/$name.png (width $width)"
    firefox --headless --profile "$profile" \
        --screenshot "$out_dir/$name.png" \
        --window-size="$width" \
        "file://$html"
done

echo "Done. Screenshots in $out_dir"
