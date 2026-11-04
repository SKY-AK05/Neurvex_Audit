#!/usr/bin/env pwsh
# NIWI Load Testing - Tokenized URL Workflow (Invited Users)
# Tests: User receives tokenized link and clicks to complete assessment

param()

$ErrorActionPreference = "Continue"
$BASE_URL = "https://niwi.orchvate.in"

# Load tokens from file
$TokensFile = "tests/performance/audit_tokens.txt"

if (-not (Test-Path $TokensFile)) {
    Write-Host "❌ Tokens file not found: $TokensFile" -ForegroundColor Red
    Write-Host "   Run: python generate_audit_tokens.py" -ForegroundColor Yellow
    exit 1
}

# Parse tokens
$Tokens = @{}
Get-Content $TokensFile | ForEach-Object {
    if ($_ -match '(\w+)=(.+)') {
        $Tokens[$matches[1]] = $matches[2]
    }
}

# Test configurations
$TestConfigs = @(
    @{ Org = "SIWI10"; VUs = 10 },
    @{ Org = "SIWI20"; VUs = 20 },
    @{ Org = "SIWI40"; VUs = 40 },
    @{ Org = "SIWI60"; VUs = 60 },
    @{ Org = "SIWI80"; VUs = 80 },
    @{ Org = "SIWI100"; VUs = 100 }
)

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  NIWI - TOKENIZED URL WORKFLOW TESTING (INVITED USERS)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Workflow: User receives $BASE_URL/audit?t=TOKEN and clicks link" -ForegroundColor Yellow
Write-Host ""

$Results = @()

foreach ($Config in $TestConfigs) {
    $Org = $Config.Org
    $VUs = $Config.VUs
    $Token = $Tokens[$Org]
    
    if (-not $Token) {
        Write-Host "❌ Token not found for $Org" -ForegroundColor Red
        continue
    }
    
    Write-Host "Testing $Org with $VUs concurrent users (token: $($Token.Substring(0,20))...)..." -ForegroundColor White
    
    $StartTime = Get-Date
    
    k6 run -e BASE_URL="$BASE_URL" -e AUDIT_TOKEN="$Token" -e VUS=$VUs -e CONFIRM_PROD=true tests/performance/niwi-submission-load.js
    
    $ExitCode = $LASTEXITCODE
    $Duration = ((Get-Date) - $StartTime).TotalSeconds
    
    $Status = if ($ExitCode -eq 0) { "PASS" } else { "FAIL" }
    $StatusIcon = if ($ExitCode -eq 0) { "✅" } else { "❌" }
    
    Write-Host "$StatusIcon $Status - Completed in $([math]::Round($Duration, 1))s" -ForegroundColor $(if ($ExitCode -eq 0) { "Green" } else { "Red" })
    Write-Host ""
    
    $Results += [PSCustomObject]@{
        Organization = $Org
        VUs = $VUs
        Status = $Status
        Duration = [math]::Round($Duration, 1)
    }
    
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  TEST SUMMARY" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

$Results | Format-Table -AutoSize

$TotalTests = $Results.Count
$PassedTests = ($Results | Where-Object { $_.Status -eq "PASS" }).Count
$FailedTests = $TotalTests - $PassedTests

Write-Host ""
Write-Host "Total Tests: $TotalTests" -ForegroundColor White
Write-Host "Passed:      $PassedTests" -ForegroundColor Green
Write-Host "Failed:      $FailedTests" -ForegroundColor $(if ($FailedTests -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($FailedTests -eq 0) {
    Write-Host "✅ ALL TESTS PASSED!" -ForegroundColor Green
} else {
    Write-Host "❌ SOME TESTS FAILED" -ForegroundColor Red
}

Write-Host ""
