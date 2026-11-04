#!/usr/bin/env pwsh
<#
.SYNOPSIS
    NIWI Load Testing - Both User Workflows
    
.DESCRIPTION
    Tests two user workflows:
    1. New/Random User: Visits base URL, manually enters org code
    2. Invited User: Uses tokenized URL with embedded org
    
.PARAMETER Workflow
    Which workflow to test: "manual" or "token" or "both" (default)
#>

param(
    [ValidateSet("manual", "token", "both")]
    [string]$Workflow = "both"
)

$ErrorActionPreference = "Continue"
$BASE_URL = "https://niwi.orchvate.in"

# Test configurations: org code mapped to VU count
$TestConfigs = @(
    @{ Org = "SIWI10"; VUs = 10 }
    @{ Org = "SIWI20"; VUs = 20 }
    @{ Org = "SIWI40"; VUs = 40 }
    @{ Org = "SIWI60"; VUs = 60 }
    @{ Org = "SIWI80"; VUs = 80 }
    @{ Org = "SIWI100"; VUs = 100 }
)

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  NIWI LOAD TESTING - DUAL WORKFLOW VALIDATION" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$Results = @()

# ============================================================================
# WORKFLOW 1: NEW/RANDOM USER (Manual Org Entry)
# ============================================================================
if ($Workflow -eq "manual" -or $Workflow -eq "both") {
    Write-Host ""
    Write-Host "🌐 WORKFLOW 1: NEW/RANDOM USER (Manual Org Entry)" -ForegroundColor Yellow
    Write-Host "   User visits: $BASE_URL" -ForegroundColor Gray
    Write-Host "   User manually enters org code in the UI" -ForegroundColor Gray
    Write-Host ""
    
    foreach ($Config in $TestConfigs) {
        $Org = $Config.Org
        $VUs = $Config.VUs
        
        Write-Host "▶  Testing $Org with $VUs concurrent users..." -ForegroundColor White
        
        $StartTime = Get-Date
        
        k6 run `
            -e BASE_URL="$BASE_URL" `
            -e ORG_CODE="$Org" `
            -e VUS=$VUs `
            -e CONFIRM_PROD=true `
            -e MANUAL_ORG_ENTRY=true `
            tests/performance/niwi-submission-load.js
        
        $ExitCode = $LASTEXITCODE
        $Duration = ((Get-Date) - $StartTime).TotalSeconds
        
        $Status = if ($ExitCode -eq 0) { "✅ PASS" } else { "❌ FAIL" }
        
        Write-Host "   $Status - Completed in $([math]::Round($Duration, 1))s" -ForegroundColor $(if ($ExitCode -eq 0) { "Green" } else { "Red" })
        Write-Host ""
        
        $Results += [PSCustomObject]@{
            Workflow = "Manual Entry"
            Organization = $Org
            VUs = $VUs
            Status = if ($ExitCode -eq 0) { "PASS" } else { "FAIL" }
            Duration = [math]::Round($Duration, 1)
        }
        
        Start-Sleep -Seconds 2
    }
}

# ============================================================================
# WORKFLOW 2: INVITED USER (Tokenized URL)
# ============================================================================
if ($Workflow -eq "token" -or $Workflow -eq "both") {
    Write-Host ""
    Write-Host "🔗 WORKFLOW 2: INVITED USER (Tokenized URL)" -ForegroundColor Yellow
    Write-Host "   User receives URL: $BASE_URL/audit?t=TOKEN" -ForegroundColor Gray
    Write-Host "   Org embedded in token" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "⚠️  NOTE: Token-based testing requires generating audit tokens first" -ForegroundColor Magenta
    Write-Host "   Skipping for now - requires backend token generation API" -ForegroundColor Gray
    Write-Host ""
    
    # TODO: Implement token generation and testing
    # foreach ($Config in $TestConfigs) {
    #     Generate token for org
    #     Run test with AUDIT_TOKEN parameter
    # }
}

# ============================================================================
# SUMMARY REPORT
# ============================================================================
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  TEST SUMMARY" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
}

if ($Results.Count -gt 0) {
    $Results | Format-Table -AutoSize
    
    $TotalTests = $Results.Count
    $PassedTests = ($Results | Where-Object { $_.Status -eq "PASS" }).Count
    $FailedTests = $TotalTests - $PassedTests
    
    Write-Host ""
    Write-Host "Total Tests:   $TotalTests" -ForegroundColor White
    Write-Host "Passed:        $PassedTests" -ForegroundColor Green
    Write-Host "Failed:        $FailedTests" -ForegroundColor $(if ($FailedTests -gt 0) { "Red" } else { "Green" })
    Write-Host ""
    
    if ($FailedTests -eq 0) {
        Write-Host "✅ ALL TESTS PASSED!" -ForegroundColor Green
    } else {
        Write-Host "❌ SOME TESTS FAILED - Check reports in tests/performance/reports/" -ForegroundColor Red
    }
} else {
    Write-Host "No tests were executed." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
