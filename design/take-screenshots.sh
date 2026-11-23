#!/usr/bin/env bash
# Full-page screenshots of a mockup set (pages are taller than the
# monitor, so a normal screenshot tool won't work -- headless Firefox
# captures the entire page height instead).
#
# Usage: ./take-screenshots.sh <set> [width] [dest]
#   <set>   mockup set directory under design/ (typhoon, charon, ...)
#   width   viewport width, default 1440
#   dest    destination directory for the PNGs, default <set>/screenshots
#           (relative paths resolve against the working directory; the
#           directory is created if missing; existing files overwritten)
#
# Run ONLY when the product owner asks for screenshots (2026-11-20):
# regenerating PNGs per commit bloats the repository — they are not
# part of the normal set workflow and are never auto-captured. For
# on-demand captures that must never land in the repo, pass a
# gitignored destination such as .local/screenshots.

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <set> [width] [dest]" >&2
    exit 1
fi

target="$1"
width="${2:-1440}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
in_dir="$script_dir/$target"
out_dir="${3:-$in_dir/screenshots}"
# Firefox --screenshot silently writes nothing for relative paths —
# canonicalize the destination before handing it over.
mkdir -p "$out_dir"
out_dir="$(cd "$out_dir" && pwd)"
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

for html in "${htmls[@]}"; do
    name="$(basename "$html" .html)"
    echo "Capturing $target/$name.html -> $out_dir/$name.png (width $width)"
    firefox --headless --profile "$profile" \
        --screenshot "$out_dir/$name.png" \
        --window-size="$width" \
        "file://$html"
done

echo "Done. Screenshots in $out_dir"
