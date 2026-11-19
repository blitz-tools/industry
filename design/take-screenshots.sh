#!/usr/bin/env bash
# Full-page screenshots of a mockup set (pages are taller than the
# monitor, so a normal screenshot tool won't work -- headless Firefox
# captures the entire page height instead).
#
# Usage: ./take-screenshots.sh <set> [width]
#   <set>   mockup set directory under design/ (typhoon, charon, ...)
#   width   viewport width, default 1440
# Output: design/<set>/screenshots/<name>.png (existing files
#         overwritten)

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <set> [width]" >&2
    exit 1
fi

target="$1"
width="${2:-1440}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
in_dir="$script_dir/$target"
out_dir="$in_dir/screenshots"
profile="$(mktemp -d /tmp/ff-headless.XXXXXX)"

trap 'rm -rf "$profile"' EXIT

if [[ ! -d "$in_dir" ]]; then
    echo "No mockup set directory: $in_dir" >&2
    exit 1
fi

shopt -s nullglob
htmls=("$in_dir"/*.html)
if [[ ${#htmls[@]} -eq 0 ]]; then
    echo "No .html files in $in_dir" >&2
    exit 1
fi

mkdir -p "$out_dir"

for html in "${htmls[@]}"; do
    name="$(basename "$html" .html)"
    echo "Capturing $target/$name.html -> $target/screenshots/$name.png (width $width)"
    firefox --headless --profile "$profile" \
        --screenshot "$out_dir/$name.png" \
        --window-size="$width" \
        "file://$html"
done

echo "Done. Screenshots in $out_dir"
