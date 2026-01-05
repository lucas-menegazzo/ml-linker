@echo off
echo ========================================
echo  Gerador de Posts Instagram - Web
echo  Modo: Internet (ngrok)
echo ========================================
echo.
echo IMPORTANTE: Voce precisa ter o ngrok instalado!
echo Baixe em: https://ngrok.com/download
echo.
echo Iniciando servidor web...
echo.
start cmd /k "python server.py"
timeout /t 3
echo.
echo Iniciando ngrok...
echo A URL publica sera exibida abaixo:
echo.
ngrok http 5000
pause

