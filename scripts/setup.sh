#!/bin/bash
# Automotive Copilot Agents - Linux/Mac Setup Script
# Installs automotive copilot agents to .github/copilot/ directory
# Append-safe: never modifies existing content

set -e

# ============================================================================
# Configuration
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
COPILOT_PATH="$PROJECT_ROOT/.github/copilot"
SOURCE_PATH="$PROJECT_ROOT/.github/copilot"
MANIFEST_FILE="$PROJECT_ROOT/.github/copilot/.install.manifest.json"

# Colors for output
COLOR_INFO='\033[0;36m'    # Cyan
COLOR_SUCCESS='\033[0;32m' # Green
COLOR_WARNING='\033[0;33m' # Yellow
COLOR_ERROR='\033[0;31m'   # Red
COLOR_RESET='\033[0m'

# Log file
LOG_FILE="$SCRIPT_DIR/setup.log"

# ============================================================================
# Helper Functions
# ============================================================================

write_info() {
    echo -e "${COLOR_INFO}[INFO] $1${COLOR_RESET}"
}

write_success() {
    echo -e "${COLOR_SUCCESS}[OK] $1${COLOR_RESET}"
}

write_warning() {
    echo -e "${COLOR_WARNING}[WARN] $1${COLOR_RESET}"
}

write_error() {
    echo -e "${COLOR_ERROR}[ERROR] $1${COLOR_RESET}"
}

get_directory_size() {
    local path="$1"
    if [ -d "$path" ]; then
        du -sb "$path" 2>/dev/null | cut -f1
    else
        echo "0"
    fi
}

get_file_count() {
    local path="$1"
    local filter="${2:-*}"
    if [ -d "$path" ]; then
        find "$path" -type f -name "$filter" 2>/dev/null | wc -l
    else
        echo "0"
    fi
}

format_file_size() {
    local size="$1"
    if [ "$size" -gt 1073741824 ]; then
        printf "%.2f GB" "$(echo "$size / 1073741824" | bc -l)"
    elif [ "$size" -gt 1048576 ]; then
        printf "%.2f MB" "$(echo "$size / 1048576" | bc -l)"
    elif [ "$size" -gt 1024 ]; then
        printf "%.2f KB" "$(echo "$size / 1024" | bc -l)"
    else
        printf "%d B" "$size"
    fi
}

is_admin() {
    if [ "$(id -u)" -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

log_message() {
    local message="$1"
    local level="${2:-INFO}"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "$timestamp - $level - $message" >> "$LOG_FILE" 2>/dev/null || true
}

# ============================================================================
# Installation Functions
# ============================================================================

copy_safe() {
    local source="$1"
    local destination="$2"
    local filter="${3:-*}"
    local copied_count=0

    if [ ! -d "$source" ]; then
        write_warning "Source not found: $source (skipping)"
        echo "0"
        return
    fi

    # Create destination directory if it doesn't exist
    mkdir -p "$destination"

    # Find and copy files (append-safe: won't overwrite unless different)
    while IFS= read -r -d '' file; do
        local relative_path="${file#$source/}"
        local target_path="$destination/$relative_path"
        local target_dir="$(dirname "$target_path")"

        # Create parent directory if needed
        if [ ! -d "$target_dir" ]; then
            mkdir -p "$target_dir"
        fi

        # Only copy if file doesn't exist or is different (compare sizes)
        if [ ! -f "$target_path" ]; then
            cp "$file" "$target_path"
            ((copied_count++))
        else
            # Compare file sizes - if different, copy
            local source_size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
            local target_size=$(stat -c%s "$target_path" 2>/dev/null || stat -f%z "$target_path" 2>/dev/null)
            if [ "$source_size" -ne "$target_size" ]; then
                cp "$file" "$target_path"
                ((copied_count++))
            fi
        fi
    done < <(find "$source" -type f -name "$filter" -print0 2>/dev/null)

    echo "$copied_count"
}

create_manifest() {
    local manifest_path="$1"
    local manifest_dir="$(dirname "$manifest_path")"

    mkdir -p "$manifest_dir"

    # Start JSON structure
    local install_date=$(date +"%Y-%m-%d %H:%M:%S")
    cat > "$manifest_path" << EOF
{
  "version": "1.0.0",
  "install_date": "$install_date",
  "project_path": "$PROJECT_ROOT",
  "copilot_path": "$COPILOT_PATH",
  "installed_components": [
EOF

    local first=true

    # Scan installed components
    if [ -d "$COPILOT_PATH/instructions" ]; then
        while IFS= read -r -d '' file; do
            local filename="$(basename "$file")"
            local name="${filename%.md}"
            if [ "$first" = true ]; then
                first=false
            else
                echo "," >> "$manifest_path"
            fi
            printf '    {"type": "agent", "name": "%s", "path": "%s"}' "$name" "$file" >> "$manifest_path"
        done < <(find "$COPILOT_PATH/instructions" -type f -name "*.md" -print0 2>/dev/null)
    fi

    if [ -d "$COPILOT_PATH/context" ]; then
        while IFS= read -r -d '' file; do
            local filename="$(basename "$file")"
            local name="${filename%.md}"
            local relative_path="${file#$COPILOT_PATH/}"
            local category="$(dirname "$relative_path" | cut -d'/' -f2)"
            if [ "$first" = true ]; then
                first=false
            else
                echo "," >> "$manifest_path"
            fi
            printf '    {"type": "context", "name": "%s", "category": "%s", "path": "%s"}' "$name" "$category" "$file" >> "$manifest_path"
        done < <(find "$COPILOT_PATH/context" -type f -name "*.md" -print0 2>/dev/null)
    fi

    if [ -d "$COPILOT_PATH/knowledge" ]; then
        while IFS= read -r -d '' file; do
            local filename="$(basename "$file")"
            local name="${filename%.md}"
            local relative_path="${file#$COPILOT_PATH/}"
            local path_parts=(${relative_path//\// })
            local category="${path_parts[1]:-general}"
            local subcategory="${path_parts[2]:-general}"
            if [ "$first" = true ]; then
                first=false
            else
                echo "," >> "$manifest_path"
            fi
            printf '    {"type": "knowledge", "name": "%s", "category": "%s", "subcategory": "%s", "path": "%s"}' "$name" "$category" "$subcategory" "$file" >> "$manifest_path"
        done < <(find "$COPILOT_PATH/knowledge" -type f -name "*.md" -print0 2>/dev/null)
    fi

    # Close JSON structure
    cat >> "$manifest_path" << EOF

  ]
}
EOF
}

# ============================================================================
# Command: Status
# ============================================================================

invoke_status() {
    write_info "Checking installation status..."
    log_message "Checking installation status"
    echo ""

    if [ ! -d "$COPILOT_PATH" ]; then
        write_warning "Automotive Copilot Agents NOT installed"
        echo ""
        write_info "Run: ./setup.sh"
        return
    fi

    # Count components
    local agent_count=$(get_file_count "$COPILOT_PATH/instructions" "*.md")
    local skill_count=$(get_file_count "$COPILOT_PATH/context" "*.md")
    local knowledge_count=$(get_file_count "$COPILOT_PATH/knowledge" "*.md")
    local total_size=$(get_directory_size "$COPILOT_PATH")

    write_success "Automotive Copilot Agents INSTALLED"
    echo ""
    write_info "Installation Summary:"
    echo "  Location: $COPILOT_PATH"
    echo ""
    write_info "Components:"
    echo "  Agents:       $agent_count"
    echo "  Skills:       $skill_count (context files)"
    echo "  Knowledge:    $knowledge_count (reference docs)"
    echo "  Total Size:   $(format_file_size "$total_size")"
    echo ""

    # Check for manifest
    if [ -f "$MANIFEST_FILE" ]; then
        write_info "Manifest:"
        if command -v jq &> /dev/null; then
            echo "  Version:      $(jq -r '.version' "$MANIFEST_FILE")"
            echo "  Installed:    $(jq -r '.install_date' "$MANIFEST_FILE")"
        else
            grep -o '"version": *"[^"]*"' "$MANIFEST_FILE" | cut -d'"' -f4 | sed 's/^/  Version:      /'
            grep -o '"install_date": *"[^"]*"' "$MANIFEST_FILE" | cut -d'"' -f4 | sed 's/^/  Installed:    /'
        fi
        echo ""
    fi

    # List agents
    if [ "$agent_count" -gt 0 ]; then
        write_info "Installed Agents:"
        find "$COPILOT_PATH/instructions" -type f -name "*.md" -exec basename {} .md \; | sort | while read -r name; do
            echo "  - $name"
        done
        echo ""
    fi

    # List skill categories
    if [ "$skill_count" -gt 0 ]; then
        write_info "Skill Categories:"
        find "$COPILOT_PATH/context" -mindepth 1 -maxdepth 1 -type d | sort | while read -r dir; do
            local cat_name="$(basename "$dir")"
            local cat_count=$(get_file_count "$dir" "*.md")
            echo "  - $cat_name: $cat_count files"
        done
        echo ""
    fi

    # Check VS Code integration
    local vscode_settings_path="$PROJECT_ROOT/.vscode/settings.json"
    if [ -f "$vscode_settings_path" ]; then
        write_info "VS Code Integration:"
        if grep -q '"github.copilot.chat.codeGeneration.enabled": *true' "$vscode_settings_path" 2>/dev/null; then
            write_success "  Copilot Chat enabled"
        else
            write_warning "  Copilot Chat may need manual enable"
        fi
    else
        write_info "  No .vscode/settings.json found (will use global Copilot settings)"
    fi

    echo ""
    write_info "To uninstall: ./setup.sh --uninstall"
}

# ============================================================================
# Command: Uninstall
# ============================================================================

invoke_uninstall() {
    write_info "Starting uninstallation..."
    log_message "Starting uninstallation"
    echo ""

    if [ ! -d "$COPILOT_PATH" ]; then
        write_warning "Nothing to uninstall - .github/copilot does not exist"
        log_message "Nothing to uninstall - .github/copilot does not exist" "WARNING"
        return
    fi

    # Confirm uninstall
    read -p "Are you sure you want to remove all automotive copilot agents? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        write_info "Uninstall cancelled"
        log_message "Uninstall cancelled by user"
        return
    fi

    # Remove .github/copilot directory
    write_info "Removing: $COPILOT_PATH"
    log_message "Removing copilot directory: $COPILOT_PATH"
    rm -rf "$COPILOT_PATH"

    write_success "Automotive Copilot Agents uninstalled"
    log_message "Uninstallation complete"
    echo ""
    write_info "Note: This only removes the .github/copilot directory"
    write_info "Your .vscode/settings.json and other project files are unchanged"
}

# ============================================================================
# Command: Install
# ============================================================================

invoke_install() {
    write_info "Starting installation..."
    log_message "Starting installation"
    echo ""

    # Verify source directory
    if [ ! -d "$SOURCE_PATH" ]; then
        write_error "Source directory not found: $SOURCE_PATH"
        write_error "Make sure you're running this script from the project root"
        log_message "Source directory not found: $SOURCE_PATH" "ERROR"
        exit 1
    fi
    log_message "Source validated: $SOURCE_PATH"

    # Display what will be installed
    local source_agents=$(get_file_count "$SOURCE_PATH/instructions" "*.md")
    local source_skills=$(get_file_count "$SOURCE_PATH/context" "*.md")
    local source_knowledge=$(get_file_count "$SOURCE_PATH/knowledge" "*.md")
    local source_size=$(get_directory_size "$SOURCE_PATH")

    write_info "Source Content:"
    echo "  Agents:       $source_agents"
    echo "  Skills:       $source_skills (context files)"
    echo "  Knowledge:    $source_knowledge (reference docs)"
    echo "  Total Size:   $(format_file_size "$source_size")"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        write_info "DRY RUN MODE - No changes will be made"
        log_message "DRY RUN MODE - No changes will be made"
        echo ""
        write_info "Would install to: $COPILOT_PATH"
        echo ""

        if [ -d "$COPILOT_PATH" ]; then
            write_warning "Target directory already exists - files will be merged"
            local existing_agents=$(get_file_count "$COPILOT_PATH/instructions" "*.md")
            if [ "$existing_agents" -gt 0 ]; then
                echo "  Existing agents: $existing_agents (will be preserved)"
            fi
        else
            write_info "Target directory will be created"
        fi

        return
    fi

    # Perform installation
    # Backup existing installation if it exists
    if [ -d "$COPILOT_PATH" ]; then
        local timestamp=$(date +"%Y%m%d_%H%M%S")
        local backup_path="$COPILOT_PATH.backup.$timestamp"
        write_info "Creating backup: $backup_path"
        log_message "Creating backup: $backup_path"
        cp -r "$COPILOT_PATH" "$backup_path"
        log_message "Backup created successfully: $backup_path"
        echo ""
    fi

    write_info "Installing to: $COPILOT_PATH"
    echo ""

    # Copy components
    local copied_count=0
    local count

    # Copy instructions (agents)
    if [ -d "$SOURCE_PATH/instructions" ]; then
        count=$(copy_safe "$SOURCE_PATH/instructions" "$COPILOT_PATH/instructions")
        write_success "Copied $count agent instruction files"
        log_message "Copied $count agent instruction files"
        copied_count=$((copied_count + count))
    fi

    # Copy context (skills)
    if [ -d "$SOURCE_PATH/context" ]; then
        count=$(copy_safe "$SOURCE_PATH/context" "$COPILOT_PATH/context")
        write_success "Copied $count skill context files"
        log_message "Copied $count skill context files"
        copied_count=$((copied_count + count))
    fi

    # Copy knowledge base
    if [ -d "$SOURCE_PATH/knowledge" ]; then
        count=$(copy_safe "$SOURCE_PATH/knowledge" "$COPILOT_PATH/knowledge")
        write_success "Copied $count knowledge files"
        log_message "Copied $count knowledge files"
        copied_count=$((copied_count + count))
    fi

    # Copy triggers
    if [ -d "$SOURCE_PATH/triggers" ]; then
        count=$(copy_safe "$SOURCE_PATH/triggers" "$COPILOT_PATH/triggers")
        write_success "Copied $count trigger files"
        log_message "Copied $count trigger files"
        copied_count=$((copied_count + count))
    fi

    # Copy personas
    if [ -d "$SOURCE_PATH/personas" ]; then
        count=$(copy_safe "$SOURCE_PATH/personas" "$COPILOT_PATH/personas")
        write_success "Copied $count persona files"
        log_message "Copied $count persona files"
        copied_count=$((copied_count + count))
    fi

    echo ""
    write_success "Installation complete! ($copied_count files copied)"
    log_message "Installation complete: $copied_count files copied"
    echo ""

    # Create manifest
    create_manifest "$MANIFEST_FILE"
    write_info "Created installation manifest"
    log_message "Created installation manifest"

    echo ""
    write_info "================================================================"
    write_info "Next Steps:"
    echo ""
    write_info "1. Restart VS Code to activate GitHub Copilot integration"
    echo ""
    write_info "2. Verify installation:"
    echo "   ./setup.sh --status"
    echo ""
    write_info "3. Start using automotive agents in Copilot Chat:"
    echo "   - Ask about sensor fusion: 'How do I implement EKF for camera-radar fusion?'"
    echo "   - Ask about safety: 'What ASIL-D requirements apply to brake control?'"
    echo "   - Ask about AUTOSAR: 'Show me an AUTOSAR Adaptive service definition'"
    echo ""
    write_info "4. Uninstall (if needed):"
    echo "   ./setup.sh --uninstall"
    write_info "================================================================"
}

# ============================================================================
# Parse Command Line Arguments
# ============================================================================

DRY_RUN=false
STATUS=false
UNINSTALL=false
PROJECT_PATH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --status)
            STATUS=true
            shift
            ;;
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        --project)
            PROJECT_PATH="$2"
            shift 2
            ;;
        -h|--help)
            echo "Automotive Copilot Agents Setup Script"
            echo ""
            echo "Usage: ./setup.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run      Preview installation without making changes"
            echo "  --status       Show current installation status"
            echo "  --uninstall    Remove automotive copilot agents"
            echo "  --project PATH Install to specific project path"
            echo "  -h, --help     Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./setup.sh                    # Install"
            echo "  ./setup.sh --dry-run          # Preview installation"
            echo "  ./setup.sh --status           # Check installation status"
            echo "  ./setup.sh --uninstall        # Remove agents"
            echo "  ./setup.sh --project /path    # Install to specific project"
            exit 0
            ;;
        *)
            write_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Override project path if specified
if [ -n "$PROJECT_PATH" ]; then
    PROJECT_ROOT="$PROJECT_PATH"
    COPILOT_PATH="$PROJECT_ROOT/.github/copilot"
    MANIFEST_FILE="$PROJECT_ROOT/.github/copilot/.install.manifest.json"
fi

# ============================================================================
# Main Entry Point
# ============================================================================

echo ""
echo "========================================"
echo "  Automotive Copilot Agents Setup"
echo "  Version 1.0.0"
echo "========================================"
echo ""

if [ "$STATUS" = true ]; then
    invoke_status
elif [ "$UNINSTALL" = true ]; then
    invoke_uninstall
else
    invoke_install
fi
