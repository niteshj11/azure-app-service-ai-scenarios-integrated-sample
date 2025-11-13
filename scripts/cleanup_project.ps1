# =====================================================================================
# Project Cleanup Automation Script
# =====================================================================================
# Purpose: Automate the cleanup of development projects for production deployment
# Based on: TechMart AI Chatbot cleanup experience
# Usage: .\scripts\cleanup_project.ps1 -Phase All -Confirm:$false
# =====================================================================================

param(
    [ValidateSet("All", "Backup", "Runtime", "Docs", "Tests", "Empty", "Archive")]
    [string]$Phase = "All",
    
    [switch]$Confirm = $true,
    
    [switch]$DryRun = $false,
    
    [string]$LogFile = "scripts\cleanup_log.txt"
)

# Initialize logging
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $LogFile -Value $logEntry
}

function Remove-ItemSafely {
    param(
        [string[]]$Path,
        [string]$Description
    )
    
    Write-Log "=== $Description ===" "PHASE"
    
    foreach ($item in $Path) {
        if (Test-Path $item) {
            $size = (Get-ChildItem $item -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            $sizeStr = if ($size) { "{0:N2} MB" -f ($size / 1MB) } else { "Unknown size" }
            
            if ($DryRun) {
                Write-Log "DRY RUN: Would remove '$item' ($sizeStr)" "DRY"
            } else {
                if (-not $Confirm -or (Read-Host "Remove '$item' ($sizeStr)? (y/N)") -eq 'y') {
                    try {
                        Remove-Item $item -Recurse -Force -ErrorAction Stop
                        Write-Log "Removed: $item ($sizeStr)" "SUCCESS"
                    } catch {
                        Write-Log "Failed to remove: $item - $($_.Exception.Message)" "ERROR"
                    }
                } else {
                    Write-Log "Skipped: $item" "SKIP"
                }
            }
        } else {
            Write-Log "Not found: $item" "INFO"
        }
    }
}

function Get-ProjectSize {
    $totalSize = (Get-ChildItem . -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    return "{0:N2} MB" -f ($totalSize / 1MB)
}

function Test-ApplicationIntegrity {
    Write-Log "=== Testing Application Integrity ===" "PHASE"
    
    # Check if core files exist
    $coreFiles = @("app.py", "wsgi.py", "requirements.txt", "azure.yaml", "AIPlaygroundCode/config.py")
    $missing = @()
    
    foreach ($file in $coreFiles) {
        if (-not (Test-Path $file)) {
            $missing += $file
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Log "WARNING: Missing core files: $($missing -join ', ')" "WARNING"
        return $false
    }
    
    # Test if Python app can import (basic syntax check)
    try {
        $result = python -c "import app; print('App imports successfully')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Application integrity check: PASSED" "SUCCESS"
            return $true
        } else {
            Write-Log "Application integrity check: FAILED - $result" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Could not test application integrity - Python not available" "WARNING"
        return $true  # Continue anyway
    }
}

# =====================================================================================
# MAIN EXECUTION
# =====================================================================================

Write-Log "Project Cleanup Started - Phase: $Phase, DryRun: $DryRun" "START"
Write-Log "Current directory: $(Get-Location)" "INFO"

# Record initial size
$initialSize = Get-ProjectSize
Write-Log "Initial project size: $initialSize" "INFO"

# Create backup commit if git is available and not in dry run mode
if (-not $DryRun -and (Test-Path ".git")) {
    try {
        git add .
        git commit -m "Pre-cleanup backup - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        Write-Log "Created git backup commit" "SUCCESS"
    } catch {
        Write-Log "Could not create git backup - continuing anyway" "WARNING"
    }
}

# Phase 1: Backup and Test Files
if ($Phase -eq "All" -or $Phase -eq "Backup") {
    $backupFiles = @(
        "*.backup",
        "*.bak", 
        "*.test",
        ".azdignore.backup",
        ".azdignore.bak",
        ".azdignore.test",
        ".webappignore.bak",
        "test-*"
    )
    Remove-ItemSafely -Path $backupFiles -Description "Phase 1: Backup and Test Files"
}

# Phase 2: Runtime and Cache Files
if ($Phase -eq "All" -or $Phase -eq "Runtime") {
    Write-Log "=== Phase 2: Runtime and Cache Files ===" "PHASE"
    
    # Remove log files (including cleanup_log.txt from previous runs)
    $logFiles = @(
        "scripts\cleanup_log.txt",
        "app.log", 
        "*.log"
    )
    Remove-ItemSafely -Path $logFiles -Description "Removing log files"
    
    # Remove Python cache directories recursively (improved)
    if ($DryRun) {
        Write-Log "DRY RUN: Would remove all __pycache__ directories and .pyc files" "DRY"
    } else {
        # Remove __pycache__ directories
        Get-ChildItem -Path . -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq "__pycache__" } | ForEach-Object { 
            Write-Log "Removed: $($_.FullName)" "SUCCESS"
            Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
        
        # Remove .pyc and .pyo files
        Get-ChildItem -Path . -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -eq ".pyc" -or $_.Extension -eq ".pyo" } | ForEach-Object {
            Write-Log "Removed: $($_.FullName)" "SUCCESS"
            Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
        }
        
        # Remove root uploads folder (should be in AIPlaygroundCode only)
        if (Test-Path "uploads") {
            Remove-Item "uploads" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "Removed: root uploads directory (should be in AIPlaygroundCode)" "SUCCESS"
        }
    }
}

# Phase 3: Documentation and Scripts Cleanup  
if ($Phase -eq "All" -or $Phase -eq "Docs") {
    Write-Log "=== Phase 3: Documentation and Scripts Cleanup ===" "PHASE"
    
    # Remove redundant documentation files
    $redundantDocs = @(
        "docs\azd-deployment-*.md",
        "docs\DEPLOYMENT*.md", 
        "docs\Testing_Documentation.md"
    )
    Remove-ItemSafely -Path $redundantDocs -Description "Removing redundant documentation"
    
    # Remove archive directory completely
    if (Test-Path "docs\archive") {
        Remove-ItemSafely -Path @("docs\archive") -Description "Removing docs archive directory"
    }
    
    # Remove redundant scripts
    $redundantScripts = @(
        "scripts\cleanup_azd_cache.*",
        "scripts\clear_azure_cache.*"
    )
    Remove-ItemSafely -Path $redundantScripts -Description "Removing redundant scripts"
}

# Phase 4: Test Directory Cleanup
if ($Phase -eq "All" -or $Phase -eq "Tests") {
    Write-Log "=== Phase 4: Test Directory Cleanup ===" "PHASE"
    
    # Remove analysis and log files from azd-tests (keep test scripts)
    $azdAnalysisFiles = @(
        "tests\azd-tests\*-analysis*.md",
        "tests\azd-tests\*-summary*.md", 
        "tests\azd-tests\*-output*.txt",
        "tests\azd-tests\FINAL-ANALYSIS.md",
        "tests\azd-tests\REAL-TEST-RESULTS.md"
    )
    Remove-ItemSafely -Path $azdAnalysisFiles -Description "Removing azd-tests analysis files"
    
    # Remove temporary documentation
    if (Test-Path "tests\URL_UPDATE_SUMMARY.md") {
        Remove-ItemSafely -Path @("tests\URL_UPDATE_SUMMARY.md") -Description "Removing temporary documentation"
    }
    
    # Empty test reports
    if (Test-Path "tests\reports") {
        if ($DryRun) {
            Write-Log "DRY RUN: Would empty tests\reports directory" "DRY"
        } else {
            if (-not $Confirm -or (Read-Host "Empty tests\reports directory? (y/N)") -eq 'y') {
                Remove-Item "tests\reports\*" -Recurse -Force -ErrorAction SilentlyContinue
                Write-Log "Emptied: tests\reports directory" "SUCCESS"
            }
        }
    }
}

# Phase 5: Empty Directories
if ($Phase -eq "All" -or $Phase -eq "Empty") {
    Write-Log "=== Phase 5: Empty Directory Cleanup ===" "PHASE"
    
    $emptyDirs = Get-ChildItem . -Directory -Recurse | Where-Object {
        (Get-ChildItem $_.FullName -Force -ErrorAction SilentlyContinue | Measure-Object).Count -eq 0
    }
    
    if ($emptyDirs) {
        foreach ($dir in $emptyDirs) {
            $relativePath = $dir.FullName -replace [regex]::Escape((Get-Location).Path + "\"), ""
            if ($DryRun) {
                Write-Log "DRY RUN: Would remove empty directory: $relativePath" "DRY"
            } else {
                if (-not $Confirm -or (Read-Host "Remove empty directory '$relativePath'? (y/N)") -eq 'y') {
                    try {
                        Remove-Item $dir.FullName -Force
                        Write-Log "Removed empty directory: $relativePath" "SUCCESS"
                    } catch {
                        Write-Log "Failed to remove empty directory: $relativePath - $($_.Exception.Message)" "ERROR"
                    }
                }
            }
        }
    } else {
        Write-Log "No empty directories found" "INFO"
    }
}

# Phase 6: Archive Directory
if ($Phase -eq "All" -or $Phase -eq "Archive") {
    Write-Log "=== Phase 6: Archive Directory Cleanup ===" "PHASE"
    
    if (Test-Path "to_be_deleted") {
        if ($DryRun) {
            Write-Log "DRY RUN: Would empty to_be_deleted directory" "DRY"
        } else {
            if (-not $Confirm -or (Read-Host "Empty to_be_deleted directory? (y/N)") -eq 'y') {
                Remove-Item "to_be_deleted\*" -Recurse -Force -ErrorAction SilentlyContinue
                Write-Log "Emptied: to_be_deleted directory" "SUCCESS"
            }
        }
    }
}

# Final integrity check
if (-not $DryRun) {
    $integrityOk = Test-ApplicationIntegrity
    if (-not $integrityOk) {
        Write-Log "WARNING: Application integrity check failed. Consider restoring from backup." "WARNING"
    }
}

# Final size comparison
$finalSize = Get-ProjectSize
Write-Log "Final project size: $finalSize (was $initialSize)" "INFO"

# Calculate size reduction
try {
    $initialMB = [double]($initialSize -replace " MB", "")
    $finalMB = [double]($finalSize -replace " MB", "")
    $reduction = $initialMB - $finalMB
    $reductionPercent = ($reduction / $initialMB) * 100
    Write-Log "Size reduction: {0:N2} MB ({1:N1}%)" -f $reduction, $reductionPercent "SUCCESS"
} catch {
    Write-Log "Could not calculate size reduction" "INFO"
}

Write-Log "Project Cleanup Completed" "END"

# Summary
Write-Host "`n=== CLEANUP SUMMARY ===" -ForegroundColor Green
Write-Host "Log file: $LogFile" -ForegroundColor Yellow
Write-Host "Initial size: $initialSize" -ForegroundColor Cyan
Write-Host "Final size: $finalSize" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "`nThis was a DRY RUN - no files were actually removed." -ForegroundColor Yellow
    Write-Host "Run again without -DryRun to perform actual cleanup." -ForegroundColor Yellow
} else {
    Write-Host "`nRecommended next steps:" -ForegroundColor Green
    Write-Host "1. Test application: python app.py" -ForegroundColor White
    Write-Host "2. Run tests: python -m pytest tests/" -ForegroundColor White
    Write-Host "3. Test packaging: azd package --environment dev" -ForegroundColor White
}