# Photo Factory - Database Viewer Script
# Quick commands to view database contents

param(
    [string]$Command = "help"
)

$container = "factory_postgres"
$db = "photo_factory"
$user = "photo_factory"

function Show-Help {
    Write-Host "=== Photo Factory Database Viewer ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\view_db.ps1 [command]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Green
    Write-Host "  help          - Show this help"
    Write-Host "  tables        - List all tables"
    Write-Host "  assets        - Show all media assets"
    Write-Host "  assets-recent - Show 10 most recent assets"
    Write-Host "  status        - Show system status (current heartbeats)"
    Write-Host "  history       - Show system status history (last 20 records)"
    Write-Host "  history-count - Show history record counts per service"
    Write-Host "  stats         - Show database statistics"
    Write-Host "  interactive   - Open interactive psql session"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\view_db.ps1 assets"
    Write-Host "  .\view_db.ps1 interactive"
    Write-Host ""
}

function Invoke-Query {
    param([string]$Query)
    docker exec $container psql -U $user -d $db -c $Query
}

switch ($Command.ToLower()) {
    "help" {
        Show-Help
    }
    "tables" {
        Write-Host "Listing all tables..." -ForegroundColor Yellow
        Invoke-Query "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
    }
    "assets" {
        Write-Host "Showing all media assets..." -ForegroundColor Yellow
        Invoke-Query "SELECT id, original_name, file_hash, size_bytes, captured_at, ingested_at FROM media_assets ORDER BY ingested_at DESC;"
    }
    "assets-recent" {
        Write-Host "Showing 10 most recent assets..." -ForegroundColor Yellow
        Invoke-Query "SELECT original_name, file_hash, size_bytes, captured_at, ingested_at FROM media_assets ORDER BY ingested_at DESC LIMIT 10;"
    }
    "status" {
        Write-Host "Showing system status (current)..." -ForegroundColor Yellow
        Invoke-Query "SELECT service_name, status, last_heartbeat, current_task, updated_at FROM system_status ORDER BY service_name;"
    }
    "history" {
        Write-Host "Showing system status history (last 20 records)..." -ForegroundColor Yellow
        Invoke-Query "SELECT service_name, status, current_task, heartbeat_timestamp FROM system_status_history ORDER BY heartbeat_timestamp DESC LIMIT 20;"
    }
    "history-count" {
        Write-Host "Showing history record counts..." -ForegroundColor Yellow
        Invoke-Query "SELECT service_name, COUNT(*) as record_count, MIN(heartbeat_timestamp) as oldest, MAX(heartbeat_timestamp) as newest FROM system_status_history GROUP BY service_name ORDER BY service_name;"
    }
    "stats" {
        Write-Host "Database Statistics:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Total Assets:" -ForegroundColor Cyan
        Invoke-Query "SELECT COUNT(*) as total_assets FROM media_assets;"
        Write-Host ""
        Write-Host "Assets by Date:" -ForegroundColor Cyan
        Invoke-Query "SELECT DATE(ingested_at) as date, COUNT(*) as count FROM media_assets GROUP BY DATE(ingested_at) ORDER BY date DESC LIMIT 10;"
        Write-Host ""
        Write-Host "Service Status:" -ForegroundColor Cyan
        Invoke-Query "SELECT service_name, status, last_heartbeat FROM system_status;"
    }
    "interactive" {
        Write-Host "Opening interactive psql session..." -ForegroundColor Yellow
        Write-Host "Type '\q' to exit, '\dt' to list tables, '\d table_name' to describe a table" -ForegroundColor Gray
        docker exec -it $container psql -U $user -d $db
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help
    }
}

