#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/DIST"

if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub. Run 'gh auth login'"
    exit 1
fi

cd "$PROJECT_ROOT"

if [ ! -d "$DIST_DIR" ]; then
    echo "Error: DIST directory not found at $DIST_DIR"
    exit 1
fi

VERSION_PATTERN='[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?'
DIST_FILES=($(ls "$DIST_DIR" | grep -E "^[^.]+[-_]$VERSION_PATTERN\." | head -1))

if [ ${#DIST_FILES[@]} -eq 0 ]; then
    echo "Error: No distribution files found in DIST"
    exit 1
fi

extractVersionFromFilename() {
    local filename="$1"
    local version_with_suffix=$(echo "$filename" | grep -oE "$VERSION_PATTERN(-[a-zA-Z]+)?" | head -1)
    echo "$version_with_suffix" | sed 's/-apple$//' | sed 's/-intel$//'
}

VERSION=$(extractVersionFromFilename "${DIST_FILES[0]}")

if [ -z "$VERSION" ]; then
    echo "Error: Could not extract version from distribution files"
    exit 1
fi

echo "Found version: $VERSION"

TAG="release-$VERSION"
echo "Looking for tag: $TAG"

if ! git tag | grep -q "^${TAG}$"; then
    echo "Error: Tag $TAG not found"
    exit 1
fi

RELEASE_EXISTS=false
if gh release view "$TAG" &> /dev/null; then
    echo "Release $TAG already exists"
    RELEASE_EXISTS=true
fi

collectReleaseAssets() {
    local assets=()

    for pattern in \
        "Freeplane-Setup-$VERSION.exe" \
        "Freeplane-$VERSION-apple.dmg" \
        "Freeplane-$VERSION-intel.dmg" \
        "Freeplane-Setup-touchscreen-$VERSION.exe" \
        "FreeplanePortable-$VERSION.paf.exe" \
        "freeplane_${VERSION}~upstream-1_all.deb" \
        "freeplane_bin-$VERSION.zip"; do

        local file="$DIST_DIR/$pattern"
        if [ -f "$file" ]; then
            assets+=("$file")
        fi
    done

    echo "${assets[@]}"
}

ASSETS=($(collectReleaseAssets))

if [ ${#ASSETS[@]} -eq 0 ]; then
    echo "Error: No release assets found for version $VERSION"
    exit 1
fi

echo "Found ${#ASSETS[@]} release assets:"
for asset in "${ASSETS[@]}"; do
    echo "  - $(basename "$asset")"
done

findReleaseNotes() {
    local versioned_notes="$DIST_DIR/history_en-$VERSION.txt"
    local generic_notes="$DIST_DIR/history_en.txt"

    if [ -f "$versioned_notes" ]; then
        echo "$versioned_notes"
    elif [ -f "$generic_notes" ]; then
        echo "$generic_notes"
    else
        echo ""
    fi
}

RELEASE_NOTES=$(findReleaseNotes)
if [ -z "$RELEASE_NOTES" ]; then
    echo "Warning: No release notes found (tried history_en-$VERSION.txt and history_en.txt)"
else
    echo "Using release notes: $(basename "$RELEASE_NOTES")"
fi

extractVersionSection() {
    local history_file="$1"
    local version="$2"
    local temp_file="$DIST_DIR/release_notes_${version}.txt"

    awk -v ver="$version" '
        BEGIN { found=0; next_section=0 }
        /^=+$/ && found && next_section { exit }
        /^=+$/ {
            getline
            if ($0 == ver) {
                found=1
                next_section=0
                getline
                next
            } else if (found) {
                next_section=1
            }
        }
        found && !next_section { print }
    ' "$history_file" > "$temp_file"

    if [ -s "$temp_file" ]; then
        echo "$temp_file"
    else
        rm -f "$temp_file"
        echo ""
    fi
}

checkAssetAlreadyUploaded() {
    local asset_name="$1"
    gh release view "$TAG" --json assets -q ".assets[].name" 2>/dev/null | grep -q "^${asset_name}$"
}

uploadAsset() {
    local asset="$1"
    local asset_name=$(basename "$asset")
    local asset_size=$(du -h "$asset" | cut -f1)
    local current_time=$(date '+%Y-%m-%d %H:%M:%S')

    if checkAssetAlreadyUploaded "$asset_name"; then
        echo ""
        echo "[$current_time] Asset already uploaded: $asset_name"
        echo "  ✓ Skipping: $asset_name"
        return 0
    fi

    echo ""
    echo "[$current_time] Uploading asset: $asset_name (Size: $asset_size)"
    echo "----------------------------------------"

    if gh release upload "$TAG" "$asset" --clobber 2>&1 | tee /tmp/upload_log.txt; then
        echo "  ✓ Successfully uploaded: $asset_name"
        return 0
    else
        echo "  ✗ Failed to upload $asset_name"
        echo "  Error details:"
        cat /tmp/upload_log.txt | sed 's/^/    /'
        echo ""
        echo "Exiting on failure. You can resume by running the script again."
        echo "Already uploaded assets will be skipped."
        exit 1
    fi
}

isPreRelease() {
    local version="$1"
    if [[ "$version" =~ -pre[0-9]+ ]] || [[ "$version" =~ -(alpha|beta|rc)[0-9]* ]]; then
        return 0
    fi
    return 1
}

createGitHubRelease() {
    if [ "$RELEASE_EXISTS" = true ]; then
        echo "Using existing release $TAG"
        echo ""
        return 0
    fi

    local cmd="gh release create \"$TAG\" --title \"Freeplane $VERSION\" --draft"

    if isPreRelease "$VERSION"; then
        cmd+=" --prerelease"
    fi

    if [ -n "$RELEASE_NOTES" ]; then
        local version_notes=$(extractVersionSection "$RELEASE_NOTES" "$VERSION")
        if [ -n "$version_notes" ]; then
            cmd+=" --notes-file \"$version_notes\""
        else
            cmd+=" --notes \"Release $VERSION\""
        fi
    else
        cmd+=" --notes \"Release $VERSION\""
    fi

    cmd+=" --target 1.12.x"

    echo "Creating GitHub release $TAG..."
    echo "================================"

    eval $cmd

    if [ $? -ne 0 ]; then
        echo "Error: Failed to create release"
        exit 1
    fi

    echo "✓ Draft release created successfully"
    echo ""

    if [ -n "$version_notes" ]; then
        rm -f "$version_notes"
    fi
}

uploadReleaseAssets() {
    echo "Uploading release assets (2 in parallel)..."
    echo "========================================"
    echo "Total assets to check: ${#ASSETS[@]}"

    local next_asset_index=0
    local active_pids=()
    local pid_to_asset=()
    local failed_uploads=()
    local successful_uploads=0
    local max_parallel=2

    startNextUpload() {
        if [ $next_asset_index -lt ${#ASSETS[@]} ]; then
            local asset="${ASSETS[$next_asset_index]}"
            local asset_name=$(basename "$asset")
            local index=$next_asset_index

            echo ""
            echo "[$((index + 1))/${#ASSETS[@]}] Starting upload: $asset_name"

            (
                uploadAsset "$asset"
                echo $? > "/tmp/upload_status_$$_$index.txt"
            ) &

            local pid=$!
            active_pids+=($pid)
            pid_to_asset[$pid]="$asset_name"
            next_asset_index=$((next_asset_index + 1))
        fi
    }

    # Start initial uploads up to max_parallel
    while [ ${#active_pids[@]} -lt $max_parallel ] && [ $next_asset_index -lt ${#ASSETS[@]} ]; do
        startNextUpload
    done

    # Process uploads as they complete
    while [ ${#active_pids[@]} -gt 0 ] || [ $next_asset_index -lt ${#ASSETS[@]} ]; do
        # Wait for any background job to finish
        if [ ${#active_pids[@]} -gt 0 ]; then
            local finished_pid
            wait -n ${active_pids[@]} 2>/dev/null
            local wait_result=$?

            # Find which PID finished
            local new_active_pids=()
            for pid in "${active_pids[@]}"; do
                if kill -0 $pid 2>/dev/null; then
                    new_active_pids+=($pid)
                else
                    finished_pid=$pid

                    # Check the actual exit status from the status file
                    local status_file="/tmp/upload_status_$$_*.txt"
                    for f in $status_file; do
                        if [ -f "$f" ]; then
                            local status=$(cat "$f")
                            rm -f "$f"
                            if [ "$status" -eq 0 ]; then
                                successful_uploads=$((successful_uploads + 1))
                            else
                                failed_uploads+=("${pid_to_asset[$pid]}")
                            fi
                            break
                        fi
                    done
                fi
            done
            active_pids=("${new_active_pids[@]}")

            # Start next upload if available
            if [ $next_asset_index -lt ${#ASSETS[@]} ]; then
                startNextUpload
            fi
        fi
    done

    # Clean up any remaining status files
    rm -f /tmp/upload_status_$$_*.txt

    # Check if any uploads failed
    if [ ${#failed_uploads[@]} -gt 0 ]; then
        echo ""
        echo "========================================"
        echo "Upload failed for the following assets:"
        for asset in "${failed_uploads[@]}"; do
            echo "  ✗ $asset"
        done
        echo ""
        echo "Exiting on failure. You can resume by running the script again."
        echo "Already uploaded assets will be skipped."
        exit 1
    fi

    echo ""
    echo "========================================"
    echo "Upload Summary:"
    echo "  All assets uploaded successfully: $successful_uploads/${#ASSETS[@]}"

    echo ""
    echo "All assets uploaded successfully. Publishing release..."
    echo "========================================"

    local publish_cmd="gh release edit \"$TAG\" --draft=false"
    if isPreRelease "$VERSION"; then
        publish_cmd+=" --prerelease"
    fi

    if eval $publish_cmd; then
        echo "✓ Release $TAG published successfully!"
    else
        echo "✗ Failed to publish release. You can manually publish with:"
        echo "  $publish_cmd"
        exit 1
    fi
}

processRelease() {
    echo "Pushing tags to remote repository..."
    git push --tags
    echo "✓ Tags pushed successfully"
    echo ""

    createGitHubRelease
    uploadReleaseAssets
}

processRelease

echo ""
echo "✓ Successfully processed GitHub release $TAG with all assets"
