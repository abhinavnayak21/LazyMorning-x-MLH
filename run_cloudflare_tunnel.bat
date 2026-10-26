@echo off
echo ========================================================
echo   Starting Cloudflare Tunnel for Local Ollama
echo   Exposing http://localhost:11434 securely to Cloudflare
echo ========================================================
echo.
echo 1. Ensure Ollama is running on your machine (http://localhost:11434).
echo 2. Cloudflare will generate a public URL ending in .trycloudflare.com
echo 3. Copy that URL and paste it into Render Environment Variables:
echo    OLLAMA_BASE_URL=https://your-tunnel-url.trycloudflare.com
echo.
cloudflared tunnel --url http://localhost:11434
pause
