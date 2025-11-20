#!/usr/bin/env pwsh
<#
.SYNOPSIS
Quick setup script for using existing AI Foundry with azd deployment

.DESCRIPTION
This script sets the required azd environment variables for using an existing AI Foundry project,
bypassing the interactive prompts during azd up.

.EXAMPLE
.\scripts\setup-existing-ai.ps1
#>

param(
    [Parameter()]
    [string]$AIFoundryEndpoint = "https://niteshjainaifoundary.services.ai.azure.com/models",
    
    [Parameter()]
    [string]$ChatModelName = "gpt-4o-mini",
    
    [Parameter()]
    [string]$AudioModelName = "gpt-4o-mini-audio-preview"
)

Write-Host "🚀 Setting up azd environment for existing AI Foundry..." -ForegroundColor Green

# Set the required environment variables
azd env set aSetupChoice "existing"
azd env set bFoundryEndpoint $AIFoundryEndpoint
azd env set cChatModelName $ChatModelName
azd env set dAudioModelName $AudioModelName

Write-Host "✅ Environment configured for existing AI Foundry:" -ForegroundColor Green
Write-Host "   Setup Choice: existing" -ForegroundColor Cyan
Write-Host "   Endpoint: $AIFoundryEndpoint" -ForegroundColor Cyan
Write-Host "   Chat Model: $ChatModelName" -ForegroundColor Cyan  
Write-Host "   Audio Model: $AudioModelName" -ForegroundColor Cyan

Write-Host ""
Write-Host "🎯 Ready to run: azd up" -ForegroundColor Yellow
Write-Host "   This will now deploy without interactive AI setup prompts." -ForegroundColor Gray