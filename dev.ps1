# Development runner - starts both backend and frontend
# Because opening two terminals is annoying

$jobs = @()

Write-Host "🚀 Starting Eddie development servers..." -ForegroundColor Cyan

# Start backend
Write-Host "`n🐍 Starting backend on http://localhost:8000..." -ForegroundColor Yellow
$backend = Start-Job -ScriptBlock {
    Set-Location $using:PWD\backend
    .\venv\Scripts\Activate.ps1
    uvicorn app.main:app --reload
}
$jobs += $backend

# Give backend a second to start
Start-Sleep -Seconds 2

# Start frontend
Write-Host "⚛️ Starting frontend on http://localhost:3000..." -ForegroundColor Yellow
$frontend = Start-Job -ScriptBlock {
    Set-Location $using:PWD\frontend
    npm run dev
}
$jobs += $frontend

Write-Host "`n✅ Both servers starting..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop both servers`n" -ForegroundColor Cyan

# Monitor jobs and display output
try {
    while ($true) {
        foreach ($job in $jobs) {
            $output = Receive-Job -Job $job
            if ($output) {
                Write-Host $output
            }
        }
        Start-Sleep -Milliseconds 500
        
        # Check if jobs are still running
        $runningJobs = $jobs | Where-Object { $_.State -eq 'Running' }
        if ($runningJobs.Count -eq 0) {
            Write-Host "All servers stopped" -ForegroundColor Red
            break
        }
    }
} finally {
    Write-Host "`n🛑 Stopping servers..." -ForegroundColor Yellow
    $jobs | Stop-Job
    $jobs | Remove-Job
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
}
