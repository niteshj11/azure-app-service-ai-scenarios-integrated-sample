# Clean azd Environment for Fresh Deployment
# This script prepares the environment for a clean azd deployment experience
# Useful for testing templates or preparing for customer deployments

param(
    [switch]$ComprehensiveClean,    # Enable comprehensive cleanup for testing
    [switch]$TestMode               # Enable test mode with additional validations
)

Write-Host "🧹 Cleaning azd Environment for Fresh Deployment" -ForegroundColor Cyan
Write-Host "This will remove all azd configuration and environments to simulate a fresh customer experience" -ForegroundColor Gray
if ($ComprehensiveClean) {
    Write-Host "🔧 Comprehensive cleanup mode enabled for testing scenarios" -ForegroundColor Yellow
}
Write-Host ""

# 1. Clear azd configuration defaults
Write-Host "1. Clearing azd config defaults..." -ForegroundColor Yellow
$currentConfig = azd config show 2>$null | ConvertFrom-Json
if ($currentConfig.defaults) {
    if ($currentConfig.defaults.subscription) {
        azd config unset defaults.subscription
        Write-Host "   ✓ Removed subscription default" -ForegroundColor Green
    }
    if ($currentConfig.defaults.location) {
        azd config unset defaults.location
        Write-Host "   ✓ Removed location default" -ForegroundColor Green
    }
    if ($currentConfig.defaults.Keys.Count -eq 0) {
        Write-Host "   ✓ No defaults to clear" -ForegroundColor Green
    }
} else {
    Write-Host "   ✓ No defaults to clear" -ForegroundColor Green
}

# 2. Remove all azd environments
Write-Host "`n2. Removing azd environments..." -ForegroundColor Yellow
if (Test-Path ".azure") {
    Remove-Item -Path ".azure" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   ✓ Removed .azure directory" -ForegroundColor Green
} else {
    Write-Host "   ✓ No .azure directory found" -ForegroundColor Green
}

# 2b. Comprehensive cleanup (if enabled)
if ($ComprehensiveClean) {
    Write-Host "   Performing comprehensive cleanup..." -ForegroundColor White
    
    # Clear all Azure environment variables
    $env:AZURE_LOCATION = $null
    $env:AZURE_SUBSCRIPTION_ID = $null
    $env:AZURE_ENV_NAME = $null
    $env:AZURE_RESOURCE_GROUP = $null
    $env:AZURE_TENANT_ID = $null
    Write-Host "   ✓ Cleared Azure environment variables" -ForegroundColor Green
    
    # Clear global azd config (backup first)
    $globalAzdConfig = "$env:USERPROFILE\.azd"
    if (Test-Path $globalAzdConfig) {
        $configFile = "$globalAzdConfig\config.json"
        if (Test-Path $configFile) {
            $backupFile = "$configFile.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Copy-Item $configFile $backupFile -Force -ErrorAction SilentlyContinue
            Remove-Item $configFile -Force -ErrorAction SilentlyContinue
            Write-Host "   ✓ Cleared global azd config (backed up to $(Split-Path $backupFile -Leaf))" -ForegroundColor Green
        }
    }
    
    # Kill any hanging azd processes
    $azdProcesses = Get-Process -Name azd -ErrorAction SilentlyContinue
    if ($azdProcesses) {
        $azdProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host "   ✓ Terminated hanging azd processes" -ForegroundColor Green
    }
}

# 3. Verify cleanup
Write-Host "`n3. Verifying clean state..." -ForegroundColor Yellow
$envList = azd env list 2>$null
if ($envList -match "NAME.*DEFAULT.*LOCAL.*REMOTE" -and $envList.Split("`n").Count -le 2) {
    Write-Host "   ✓ No environments found" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ Some environments may still exist" -ForegroundColor Yellow
}

$cleanConfig = azd config show 2>$null | ConvertFrom-Json
if ($cleanConfig.defaults.Keys.Count -eq 0 -or !$cleanConfig.defaults) {
    Write-Host "   ✓ No config defaults found" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ Some config defaults may still exist" -ForegroundColor Yellow
}

Write-Host "`n🎯 Environment Cleanup Complete!" -ForegroundColor Green
Write-Host "Ready for fresh azd up deployment (will prompt for all inputs)" -ForegroundColor Gray

if ($TestMode) {
    Write-Host "`n📋 Expected prompts during azd up (based on testing experience):" -ForegroundColor Cyan
    Write-Host "   1. Environment name" -ForegroundColor White
    Write-Host "   2. Subscription selection" -ForegroundColor White  
    Write-Host "   3. Location selection" -ForegroundColor White
    Write-Host "   4. Environment name (again)" -ForegroundColor White
    Write-Host "   5. Create new resource group (Y/n)" -ForegroundColor White
    Write-Host "   6. Resource group name" -ForegroundColor White
    Write-Host "   7. Resource group name (confirmation)" -ForegroundColor White
    Write-Host "`n   Total: 7 prompts expected" -ForegroundColor Yellow
} else {
    Write-Host "`n📋 Expected prompts during azd up:" -ForegroundColor Cyan
    Write-Host "   • Environment name" -ForegroundColor White
    Write-Host "   • Azure subscription (if multiple available)" -ForegroundColor White
    Write-Host "   • Azure location" -ForegroundColor White
    Write-Host "   • Resource group selection/creation" -ForegroundColor White
    Write-Host "   • Project name confirmation" -ForegroundColor White
}

# Return success code for automation
exit 0