#!/bin/bash
# Automotive Copilot Agents - Installation Validation Script (Linux/Mac)
# Validates the integrity and completeness of installed agents
# Append-safe: read-only validation, no modifications

set -e

# ============================================================================
# Configuration
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
COPILOT_PATH="$PROJECT_ROOT/.github/copilot"
MANIFEST_FILE="$PROJECT_ROOT/.github/copilot/.install.manifest.json"

# Minimum expected content
MIN_AGENTS=5        # At least 5 agents for MVP
MIN_SKILLS=10       # At least 10 skill context files
MIN_KNOWLEDGE=20    # At least 20 knowledge files

# Colors for output
COLOR_INFO='\033[0;36m'    # Cyan
COLOR_SUCCESS='\033[0;32m' # Green
COLOR_WARNING='\033[0;33m' # Yellow
COLOR_ERROR='\033[0;31m'   # Red
COLOR_RESET='\033[0m'

# Validation results
VALIDATION_PASSED=true
WARNINGS=()
ERRORS=()
CHECKS_PASSED=0
CHECKS_FAILED=0

# Command line options
VERBOSE=false
FIX=false
OUTPUT_FORMAT="text"  # text, json, junit

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

get_file_count() {
    local path="$1"
    local filter="${2:-*.md}"
    if [ -d "$path" ]; then
        find "$path" -type f -name "$filter" 2>/dev/null | wc -l | tr -d ' '
    else
        echo "0"
    fi
}

get_directory_size() {
    local path="$1"
    if [ -d "$path" ]; then
        du -sb "$path" 2>/dev/null | cut -f1
    else
        echo "0"
    fi
}

format_file_size() {
    local size="$1"
    if [ "$size" -gt 1073741824 ]; then
        printf "%.2f GB" "$(echo "scale=2; $size / 1073741824" | bc -l)"
    elif [ "$size" -gt 1048576 ]; then
        printf "%.2f MB" "$(echo "scale=2; $size / 1048576" | bc -l)"
    elif [ "$size" -gt 1024 ]; then
        printf "%.2f KB" "$(echo "scale=2; $size / 1024" | bc -l)"
    else
        printf "%d B" "$size"
    fi
}

add_check() {
    local name="$1"
    local description="$2"
    local passed="$3"
    local details="$4"
    local severity="${5:-error}"

    if [ "$passed" = "true" ]; then
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
        if [ "$severity" = "error" ]; then
            VALIDATION_PASSED=false
            ERRORS+=("$name: $details")
        elif [ "$severity" = "warning" ]; then
            WARNINGS+=("$name: $details")
        fi
    fi
}

# ============================================================================
# Validation Checks
# ============================================================================

invoke_validation_checks() {
    write_info "Starting validation..."
    echo ""

    # -------------------------------------------------------------------------
    # Check 1: Copilot Directory Exists
    # -------------------------------------------------------------------------
    write_info "Checking directory structure..."
    local dir_exists="false"
    [ -d "$COPILOT_PATH" ] && dir_exists="true"

    add_check "Copilot Directory" ".github/copilot directory exists" "$dir_exists" \
        "$(if [ "$dir_exists" = "true" ]; then echo "Found at $COPILOT_PATH"; else echo "Directory not found"; fi)"

    if [ "$dir_exists" = "true" ]; then
        write_success "Copilot directory found"
    else
        write_error ".github/copilot directory not found"
        write_info "Run: ./setup.sh to install"
        return 1
    fi
    echo ""

    # -------------------------------------------------------------------------
    # Check 2: Manifest File Exists
    # -------------------------------------------------------------------------
    write_info "Checking installation manifest..."
    local manifest_exists="false"
    [ -f "$MANIFEST_FILE" ] && manifest_exists="true"

    add_check "Installation Manifest" ".install.manifest.json exists" "$manifest_exists" \
        "$(if [ "$manifest_exists" = "true" ]; then echo "Found"; else echo "Missing - install may be incomplete"; fi)" "warning"

    if [ "$manifest_exists" = "true" ]; then
        write_success "Manifest file found"
    else
        write_warning "Manifest file missing"
    fi
    echo ""

    # -------------------------------------------------------------------------
    # Check 3: Agent Count Validation
    # -------------------------------------------------------------------------
    write_info "Validating agents..."
    local agent_path="$COPILOT_PATH/instructions"
    local agent_count=$(get_file_count "$agent_path" "*.md")
    local agent_min_met="false"
    [ "$agent_count" -ge "$MIN_AGENTS" ] && agent_min_met="true"

    add_check "Agent Count" "Minimum agent count ($MIN_AGENTS)" "$agent_min_met" \
        "$agent_count agents found"

    if [ "$agent_min_met" = "true" ]; then
        write_success "Agent count: $agent_count (minimum: $MIN_AGENTS)"
    else
        write_warning "Agent count below minimum: $agent_count < $MIN_AGENTS"
    fi

    # List agents if verbose
    if [ "$VERBOSE" = "true" ] && [ -d "$agent_path" ]; then
        write_info "  Installed agents:"
        find "$agent_path" -type f -name "*.md" -exec basename {} .md \; 2>/dev/null | sort | while read -r name; do
            echo "    - $name"
        done
    fi
    echo ""

    # -------------------------------------------------------------------------
    # Check 4: Skill Context Validation
    # -------------------------------------------------------------------------
    write_info "Validating skills..."
    local context_path="$COPILOT_PATH/context"
    local skill_count=$(get_file_count "$context_path" "*.md")
    local skill_min_met="false"
    [ "$skill_count" -ge "$MIN_SKILLS" ] && skill_min_met="true"

    add_check "Skill Context Count" "Minimum skill count ($MIN_SKILLS)" "$skill_min_met" \
        "$skill_count skill files found"

    if [ "$skill_min_met" = "true" ]; then
        write_success "Skill count: $skill_count (minimum: $MIN_SKILLS)"
    else
        write_warning "Skill count below minimum: $skill_count < $MIN_SKILLS"
    fi

    # List skill categories if verbose
    if [ "$VERBOSE" = "true" ] && [ -d "$context_path" ]; then
        write_info "  Skill categories:"
        find "$context_path" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | while read -r dir; do
            local cat_name="$(basename "$dir")"
            local cat_count=$(get_file_count "$dir" "*.md")
            echo "    - $cat_name: $cat_count files"
        done
    fi
    echo ""

    # -------------------------------------------------------------------------
    # Check 5: Knowledge Base Validation
    # -------------------------------------------------------------------------
    write_info "Validating knowledge base..."
    local knowledge_path="$COPILOT_PATH/knowledge"
    local knowledge_count=$(get_file_count "$knowledge_path" "*.md")
    local knowledge_min_met="false"
    [ "$knowledge_count" -ge "$MIN_KNOWLEDGE" ] && knowledge_min_met="true"

    add_check "Knowledge Base Count" "Minimum knowledge count ($MIN_KNOWLEDGE)" "$knowledge_min_met" \
        "$knowledge_count knowledge files found"

    if [ "$knowledge_min_met" = "true" ]; then
        write_success "Knowledge count: $knowledge_count (minimum: $MIN_KNOWLEDGE)"
    else
        write_warning "Knowledge count below minimum: $knowledge_count < $MIN_KNOWLEDGE"
    fi

    # List knowledge categories if verbose
    if [ "$VERBOSE" = "true" ] && [ -d "$knowledge_path" ]; then
        write_info "  Knowledge categories:"
        find "$knowledge_path" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | while read -r dir; do
            local cat_name="$(basename "$dir")"
            local cat_count=$(get_file_count "$dir" "*.md")
            echo "    - $cat_name: $cat_count files"
        done
    fi
    echo ""

    # -------------------------------------------------------------------------
    # Check 6: File Size Validation (No Empty Files)
    # -------------------------------------------------------------------------
    write_info "Validating file integrity..."
    local empty_files=()

    if [ -d "$COPILOT_PATH" ]; then
        while IFS= read -r file; do
            if [ -f "$file" ] && [ ! -s "$file" ]; then
                empty_files+=("$file")
            fi
        done < <(find "$COPILOT_PATH" -type f -name "*.md" 2>/dev/null)
    fi

    local no_empty_files="true"
    [ ${#empty_files[@]} -gt 0 ] && no_empty_files="false"

    add_check "File Integrity" "No empty markdown files" "$no_empty_files" \
        "$(if [ "$no_empty_files" = "true" ]; then echo "All files have content"; else echo "${#empty_files[@]} empty files found"; fi)"

    if [ "$no_empty_files" = "true" ]; then
        write_success "All files have content"
    else
        write_warning "${#empty_files[@]} empty files found:"
        for empty_file in "${empty_files[@]}"; do
            write_warning "  - $empty_file"
        done

        if [ "$FIX" = "true" ]; then
            write_info "  Removing empty files..."
            for empty_file in "${empty_files[@]}"; do
                rm -f "$empty_file"
                write_success "  Removed: $empty_file"
            done
        fi
    fi
    echo ""

    # -------------------------------------------------------------------------
    # Check 7: Agent Format Validation
    # -------------------------------------------------------------------------
    write_info "Validating agent format..."
    local malformed_agents=()

    if [ -d "$agent_path" ]; then
        while IFS= read -r agent_file; do
            # Check for required sections
            if ! grep -q "^# .\+" "$agent_file" 2>/dev/null; then
                malformed_agents+=("$agent_file")
            elif ! grep -q "## When to Activate" "$agent_file" 2>/dev/null; then
                malformed_agents+=("$agent_file")
            fi
        done < <(find "$agent_path" -type f -name "*.md" 2>/dev/null)
    fi

    local agents_well_formed="true"
    [ ${#malformed_agents[@]} -gt 0 ] && agents_well_formed="false"

    add_check "Agent Format" "Agents follow required format" "$agents_well_formed" \
        "$(if [ "$agents_well_formed" = "true" ]; then echo "All agents well-formed"; else echo "${#malformed_agents[@]} malformed agents"; fi)" "warning"

    if [ "$agents_well_formed" = "true" ]; then
        write_success "All agents follow required format"
    else
        write_warning "${#malformed_agents[@]} agents may be malformed:"
        for malformed in "${malformed_agents[@]}"; do
            write_warning "  - $(basename "$malformed")"
        done
    fi
    echo ""

    # -------------------------------------------------------------------------
    # Check 8: Total Installation Size
    # -------------------------------------------------------------------------
    write_info "Checking installation size..."
    local total_size=$(get_directory_size "$COPILOT_PATH")
    local size_formatted=$(format_file_size "$total_size")

    write_success "Total installation size: $size_formatted"
    echo ""

    # -------------------------------------------------------------------------
    # Check 9: VS Code Integration Check
    # -------------------------------------------------------------------------
    write_info "Checking VS Code integration..."
    local vscode_settings_path="$PROJECT_ROOT/.vscode/settings.json"
    local vscode_found="false"
    [ -f "$vscode_settings_path" ] && vscode_found="true"

    add_check "VS Code Settings" ".vscode/settings.json exists" "$vscode_found" \
        "$(if [ "$vscode_found" = "true" ]; then echo "Found"; else echo "Not found - will use global Copilot settings"; fi)" "info"

    if [ "$vscode_found" = "true" ]; then
        if grep -q '"github.copilot.chat.codeGeneration.enabled".*true' "$vscode_settings_path" 2>/dev/null; then
            write_success "Copilot Chat enabled in workspace settings"
        else
            write_warning "Copilot Chat not explicitly enabled (may use global setting)"
        fi
    else
        write_info "No workspace settings found - Copilot will use global configuration"
    fi
    echo ""

    # -------------------------------------------------------------------------
    # Check 10: Manifest Consistency (if manifest exists)
    # -------------------------------------------------------------------------
    if [ "$manifest_exists" = "true" ]; then
        write_info "Validating manifest consistency..."

        if command -v jq &> /dev/null; then
            local manifest_component_count=$(jq '.installed_components | length' "$MANIFEST_FILE" 2>/dev/null || echo "0")
            local actual_count=$((agent_count + skill_count + knowledge_count))

            local manifest_matches="false"
            [ "$manifest_component_count" = "$actual_count" ] && manifest_matches="true"

            add_check "Manifest Consistency" "Manifest matches installed files" "$manifest_matches" \
                "Manifest: $manifest_component_count components, Actual: $actual_count files" "info"

            if [ "$manifest_matches" = "true" ]; then
                write_success "Manifest consistent with installation"
            else
                write_warning "Manifest may be out of sync (run ./setup.sh to update)"
            fi
        else
            write_info "jq not installed - skipping manifest consistency check"
            add_check "Manifest Consistency" "jq tool available" "false" "jq not installed" "info"
        fi
        echo ""
    fi
}

# ============================================================================
# Summary Output
# ============================================================================

write_summary() {
    echo ""
    echo "================================================================"
    echo "  VALIDATION SUMMARY"
    echo "================================================================"
    echo ""

    local total_checks=$((CHECKS_PASSED + CHECKS_FAILED))

    echo "Total Checks:  $total_checks"
    write_success "Passed:        $CHECKS_PASSED"
    if [ "$CHECKS_FAILED" -gt 0 ]; then
        write_error "Failed:        $CHECKS_FAILED"
    fi
    echo ""

    if [ ${#WARNINGS[@]} -gt 0 ]; then
        write_warning "Warnings:        ${#WARNINGS[@]}"
    fi

    echo ""

    if [ "$VALIDATION_PASSED" = "true" ]; then
        write_success "VALIDATION PASSED"
        echo "Installation is complete and valid."
    else
        write_error "VALIDATION FAILED"
        echo "Installation has issues that need attention."
        echo ""
        echo "Errors:"
        for err in "${ERRORS[@]}"; do
            write_error "  - $err"
        done
    fi

    echo ""
    echo "================================================================"
}

export_results() {
    local format="$1"

    case "$format" in
        "json")
            local output_path="$PROJECT_ROOT/validation-results.json"
            local timestamp=$(date +"%Y-%m-%d %H:%M:%S")

            cat > "$output_path" << EOF
{
  "timestamp": "$timestamp",
  "project_path": "$PROJECT_ROOT",
  "copilot_path": "$COPILOT_PATH",
  "overall_status": "$( [ "$VALIDATION_PASSED" = "true" ] && echo "PASS" || echo "FAIL" )",
  "checks_passed": $CHECKS_PASSED,
  "checks_failed": $CHECKS_FAILED,
  "warnings_count": ${#WARNINGS[@]},
  "errors_count": ${#ERRORS[@]}
}
EOF
            write_info "Results exported to: $output_path"
            ;;
        "junit")
            local output_path="$PROJECT_ROOT/validation-results.xml"
            local timestamp=$(date +"%Y-%m-%d %H:%M:%S")

            cat > "$output_path" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="AutomotiveCopilotValidation" tests="$((CHECKS_PASSED + CHECKS_FAILED))" failures="$CHECKS_FAILED">
  <testsuite name="InstallationValidation" tests="$((CHECKS_PASSED + CHECKS_FAILED))" failures="$CHECKS_FAILED">
EOF
            # Note: Full JUnit export would require tracking individual checks
            # This is a simplified version

            cat >> "$output_path" << EOF
  </testsuite>
</testsuites>
EOF
            write_info "Results exported to: $output_path"
            ;;
    esac
}

# ============================================================================
# Parse Command Line Arguments
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --fix)
            FIX=true
            shift
            ;;
        --output-format|--format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --project)
            PROJECT_ROOT="$2"
            COPILOT_PATH="$PROJECT_ROOT/.github/copilot"
            MANIFEST_FILE="$PROJECT_ROOT/.github/copilot/.install.manifest.json"
            shift 2
            ;;
        -h|--help)
            echo "Automotive Copilot Agents - Installation Validation"
            echo ""
            echo "Usage: ./validate-install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose           Show detailed validation output"
            echo "  --fix                   Attempt to fix common issues"
            echo "  --format FORMAT         Output format: text, json, junit"
            echo "  --project PATH          Validate specific project path"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./validate-install.sh                    # Basic validation"
            echo "  ./validate-install.sh -v                 # Verbose output"
            echo "  ./validate-install.sh --fix              # Fix issues"
            echo "  ./validate-install.sh --format json      # JSON output"
            echo "  ./validate-install.sh --project /path    # Validate specific project"
            exit 0
            ;;
        *)
            write_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# ============================================================================
# Main Entry Point
# ============================================================================

echo ""
echo "========================================"
echo "  Automotive Copilot Agents Validation"
echo "  Version 1.0.0"
echo "========================================"
echo ""

invoke_validation_checks
write_summary

if [ "$OUTPUT_FORMAT" != "text" ]; then
    export_results "$OUTPUT_FORMAT"
fi

# Exit with appropriate code
if [ "$VALIDATION_PASSED" = "true" ]; then
    exit 0
else
    exit 1
fi
