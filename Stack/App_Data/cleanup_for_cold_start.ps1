# Photo Factory - Cold Start Cleanup Script
# This script safely removes containers and images while preserving data volumes

Write-Host "=== Photo Factory Cold Start Cleanup ===" -ForegroundColor Cyan
Write-Host ""

# Navigate to docker-compose directory
Set-Location $PSScriptRoot

Write-Host "1. Stopping all containers..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "2. Removing containers..." -ForegroundColor Yellow
docker-compose rm -f

Write-Host ""
Write-Host "3. Listing Photo Factory images..." -ForegroundColor Yellow
docker images | Select-String "photo-factory|factory"

Write-Host ""
$confirm = Read-Host "Remove Photo Factory images? This will force a full rebuild (y/N)"
if ($confirm -eq "y" -or $confirm -eq "Y") {
    Write-Host "Removing Photo Factory images..." -ForegroundColor Yellow
    docker images --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -like "*photo-factory*" -or $_ -like "*factory*" } | ForEach-Object {
        docker rmi $_ -f
    }
    Write-Host "Images removed." -ForegroundColor Green
} else {
    Write-Host "Skipping image removal. Images will be reused." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "4. Checking volumes (these are preserved)..." -ForegroundColor Yellow
docker volume ls

Write-Host ""
Write-Host "=== Cleanup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Data volumes are preserved. Your data is safe." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Rebuild: docker-compose build" -ForegroundColor White
Write-Host "  2. Start:   docker-compose up -d" -ForegroundColor White
Write-Host "  3. Check:   docker-compose ps" -ForegroundColor White

