# Direct Confluence API Test
param(
    [string]$PageId = "131421"
)

Write-Host "`n=== Testing Confluence Page $PageId ===" -ForegroundColor Cyan

# Load credentials from .env
$envFile = "backend\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.+)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Variable -Name $key -Value $value -Scope Script
        }
    }
} else {
    Write-Host "ERROR: backend\.env not found!" -ForegroundColor Red
    exit
}

Write-Host "`nConfiguration:" -ForegroundColor Yellow
Write-Host "  URL: $CONFLUENCE_URL"
Write-Host "  User: $CONFLUENCE_USER_EMAIL"
Write-Host "  Token: $(if($CONFLUENCE_API_TOKEN){'✓ Present'}else{'✗ Missing'})"

# Construct API URL
$apiUrl = "$CONFLUENCE_URL/wiki/rest/api/content/$PageId"
Write-Host "`nAPI Request:" -ForegroundColor Yellow
Write-Host "  $apiUrl`?expand=body.storage,metadata.labels,space"

# Create auth header
$base64Auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${CONFLUENCE_USER_EMAIL}:${CONFLUENCE_API_TOKEN}"))
$headers = @{
    "Authorization" = "Basic $base64Auth"
    "Accept" = "application/json"
}

Write-Host "`nMaking request..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$apiUrl`?expand=body.storage,metadata.labels,space" -Headers $headers -Method Get
    
    Write-Host "`n✅ SUCCESS!" -ForegroundColor Green
    Write-Host "  Title: $($response.title)" -ForegroundColor Cyan
    Write-Host "  ID: $($response.id)"
    Write-Host "  Type: $($response.type)"
    Write-Host "  Space: $($response.space.key) - $($response.space.name)"
    Write-Host "  URL: $CONFLUENCE_URL$($response._links.webui)"
    
    if ($response.space.type -eq 'personal') {
        Write-Host "`n⚠️  WARNING: This is a PERSONAL space!" -ForegroundColor Yellow
        Write-Host "   Personal space pages may have different permissions." -ForegroundColor Yellow
    } else {
        Write-Host "`n✓ This is a TEAM space" -ForegroundColor Green
    }
    
} catch {
    Write-Host "`n❌ FAILED!" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "  Status Code: $statusCode"
        
        switch ($statusCode) {
            401 { Write-Host "  → Check your API token and email" -ForegroundColor Yellow }
            403 { Write-Host "  → You don't have permission to access this page" -ForegroundColor Yellow }
            404 { Write-Host "  → Page not found or wrong page ID" -ForegroundColor Yellow }
        }
    }
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
