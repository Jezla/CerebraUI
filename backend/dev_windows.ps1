# Open WebUI 开发环境启动脚本
# 功能：启动后端服务器，配置CORS，支持开发模式

Write-Host "Starting Open WebUI Backend Server..." -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

#设置CORS环境变量，允许前端访问
$env:CORS_ALLOW_ORIGIN = "http://localhost:5173"
Write-Host "CORS_ALLOW_ORIGIN set to: $env:CORS_ALLOW_ORIGIN" -ForegroundColor Yellow

# 设置端口（如果没有设置PORT环境变量，默认使用8080）
if (-not $env:PORT) {
    $env:PORT = "8080"
    Write-Host "PORT not set, using default: $env:PORT" -ForegroundColor Yellow
} else {
    Write-Host "Using PORT: $env:PORT" -ForegroundColor Yellow
}

# 检查Python和uvicorn是否可用
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "Error: Python not found or not in PATH" -ForegroundColor Red
    Write-Host "Please ensure Python is installed and added to PATH" -ForegroundColor Red
    exit 1
}

try {
    $uvicornVersion = uvicorn --version 2>&1
    Write-Host "Uvicorn version: $uvicornVersion" -ForegroundColor Cyan
} catch {
    Write-Host "Error: Uvicorn not found" -ForegroundColor Red
    Write-Host "Please install uvicorn: pip install uvicorn" -ForegroundColor Red
    exit 1
}

Write-Host "=====================================" -ForegroundColor Green
Write-Host "Starting server on http://localhost:$env:PORT" -ForegroundColor Green
Write-Host "CORS enabled for: $env:CORS_ALLOW_ORIGIN" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red
Write-Host "=====================================" -ForegroundColor Green

# 启动后端服务器
try {
    uvicorn open_webui.main:app --port=$env:PORT --host=0.0.0.0 --forwarded-allow-ips="*" --reload
} catch {
    Write-Host "Error starting server: $_" -ForegroundColor Red
    Write-Host "Please check if the port $env:PORT is available" -ForegroundColor Red
    exit 1
}
