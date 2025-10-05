# Simple Confluence Test
Write-Host "`n=== Confluence Integration Test ===" -ForegroundColor Cyan

# Test 1: Backend
Write-Host "`n[1] Testing backend..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/"
    Write-Host "OK Backend running: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "ERROR Backend not responding" -ForegroundColor Red
    exit
}

# Test 2: Get a page
Write-Host "`n[2] To test Confluence, I need a page ID." -ForegroundColor Yellow
Write-Host "Go to your Confluence, open any page, and look at the URL:" -ForegroundColor Gray
Write-Host "Example: https://crocodilman.atlassian.net/wiki/spaces/ABC/pages/123456/Title" -ForegroundColor Gray
Write-Host "The page ID is the number: 123456`n" -ForegroundColor Gray

$pageId = Read-Host "Enter a page ID to test (or leave blank to skip)"

if ($pageId) {
    Write-Host "`nFetching page $pageId..." -ForegroundColor Yellow
    try {
        $page = Invoke-RestMethod -Uri "http://localhost:8000/api/confluence/page/$pageId"
        Write-Host "SUCCESS Fetched page: $($page.title)" -ForegroundColor Green
        Write-Host "Space: $($page.space_key)" -ForegroundColor Gray
        Write-Host "`nConfluence integration is WORKING!" -ForegroundColor Green
    } catch {
        Write-Host "FAILED Could not fetch page" -ForegroundColor Red
        Write-Host "Check: Page ID is correct, you have access, API token is valid" -ForegroundColor Yellow
    }
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
Write-Host "Next: Open http://localhost:3000 and create a course!`n" -ForegroundColor Gray
