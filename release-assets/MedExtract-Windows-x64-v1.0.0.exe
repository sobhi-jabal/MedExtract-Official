@echo off
:: MedExtract Installer v5.4 - Maximum Compatibility Edition
:: This version uses ONLY the most basic batch commands

:: Keep window open - Method 1
if not "%1"=="KEEPOPEN" (
    cmd /k "%~f0" KEEPOPEN
    exit
)

:: Keep window open - Method 2
title MedExtract Installer v5.4
color 0B

:: Clear screen and show banner
cls
echo.
echo   __  __          _ _____      _                  _   
echo  ^|  \/  ^|        ^| ^|  ___ ^|    ^| ^|                ^| ^|  
echo  ^| \  / ^| ___  __^| ^| ^|__  __ _^| ^|_ _ __ __ _  ___^| ^|_ 
echo  ^| ^|\/^| ^|/ _ \/ _ ^|  __^| \ \/ / __^| '__/ _ ^|/ __^| __^|
echo  ^| ^|  ^| ^|  __/ (_^| ^| ^|____ ^>  ^<^| ^|_^| ^| ^| (_^| ^| (__^| ^|_
echo  ^|_^|  ^|_^|\___^|\__,_\____/_/_/\_\\__^|_^|  \__,_^|\___^|\__^|
echo.
echo        MedExtract Installer v5.4
echo    Maximum Compatibility - No Syntax Errors
echo ============================================
echo.

:: Create debug log
echo MedExtract Install Log > "%TEMP%\medextract-install.log"
echo Started: %date% %time% >> "%TEMP%\medextract-install.log"

:: Variables
set INSTALL_DIR=%USERPROFILE%\MedExtract
set STEP=0

:: STEP 1: Admin check
set /a STEP=STEP+1
echo [%STEP%] Checking administrator privileges...
echo [%STEP%] Checking admin >> "%TEMP%\medextract-install.log"

net session >nul 2>&1
if errorlevel 1 goto NOTADMIN
echo     [OK] Running as Administrator
echo.
goto CHECKDOCKER

:NOTADMIN
echo.
echo     ERROR: Administrator required
echo.
echo     Please:
echo     1. Close this window
echo     2. Right-click the installer
echo     3. Select "Run as administrator"
echo.
pause
exit

:CHECKDOCKER
:: STEP 2: Docker check (no version parsing!)
set /a STEP=STEP+1
echo [%STEP%] Checking Docker Desktop...
echo [%STEP%] Checking Docker >> "%TEMP%\medextract-install.log"

:: Just check if docker command exists
docker --help >nul 2>&1
if errorlevel 1 goto NODOCKER
echo     [OK] Docker command found
echo.
goto CHECKDOCKERRUN

:NODOCKER
echo.
echo     ERROR: Docker Desktop not installed
echo.
echo     Install Docker Desktop from:
echo     https://docker.com
echo.
pause
exit

:CHECKDOCKERRUN
:: STEP 3: Check if Docker daemon running
set /a STEP=STEP+1
echo [%STEP%] Checking if Docker is running...
echo [%STEP%] Docker daemon check >> "%TEMP%\medextract-install.log"

docker ps >nul 2>&1
if errorlevel 1 goto DOCKERNOTRUNNING
echo     [OK] Docker is running
echo.
goto CLEANUP

:DOCKERNOTRUNNING
echo     Docker not running - starting...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
echo     Waiting 60 seconds for Docker to start...

:: Simple wait without complex loops
timeout /t 60 /nobreak >nul
docker ps >nul 2>&1
if errorlevel 1 goto DOCKERFAIL
echo     [OK] Docker started
echo.
goto CLEANUP

:DOCKERFAIL
echo.
echo     ERROR: Docker failed to start
echo     Start Docker Desktop manually
echo.
pause
exit

:CLEANUP
:: STEP 4: Cleanup old installation
set /a STEP=STEP+1
echo [%STEP%] Cleaning previous installation...
echo [%STEP%] Cleanup >> "%TEMP%\medextract-install.log"

if exist "%INSTALL_DIR%" (
    cd /d "%USERPROFILE%"
    
    :: Stop containers - simple approach
    docker ps -aq --filter "name=medextract" > "%TEMP%\containers.txt" 2>nul
    for /f %%i in (%TEMP%\containers.txt) do (
        docker stop %%i >nul 2>&1
        docker rm %%i >nul 2>&1
    )
    del "%TEMP%\containers.txt" 2>nul
    
    :: Remove images
    docker rmi medextract-backend:latest >nul 2>&1
    docker rmi medextract-frontend:latest >nul 2>&1
    
    :: Remove directory
    rmdir /s /q "%INSTALL_DIR%" 2>nul
)
echo     [OK] Cleanup complete
echo.

:DOWNLOAD
:: STEP 5: Download
set /a STEP=STEP+1
echo [%STEP%] Downloading MedExtract...
echo [%STEP%] Download >> "%TEMP%\medextract-install.log"

:: Simple PowerShell download
powershell -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; (New-Object Net.WebClient).DownloadFile('https://github.com/sobhi-jabal/medextract-llm/archive/refs/heads/main.zip', '%TEMP%\medextract.zip')"

if not exist "%TEMP%\medextract.zip" goto DOWNLOADFAIL
echo     [OK] Download complete
echo.
goto EXTRACT

:DOWNLOADFAIL
echo.
echo     ERROR: Download failed
echo     Check internet connection
echo.
pause
exit

:EXTRACT
:: STEP 6: Extract
set /a STEP=STEP+1
echo [%STEP%] Extracting files...
echo [%STEP%] Extract >> "%TEMP%\medextract-install.log"

:: Create directory
mkdir "%INSTALL_DIR%" 2>nul

:: Extract with PowerShell
powershell -Command "Expand-Archive -Path '%TEMP%\medextract.zip' -DestinationPath '%TEMP%' -Force"

:: Move files
if exist "%TEMP%\medextract-llm-main" (
    xcopy "%TEMP%\medextract-llm-main\*" "%INSTALL_DIR%\" /E /H /Y /Q >nul
    rmdir /s /q "%TEMP%\medextract-llm-main" 2>nul
) else (
    echo     ERROR: Extract failed
    pause
    exit
)

del "%TEMP%\medextract.zip" 2>nul
echo     [OK] Files extracted
echo.

:CONFIGURE
:: STEP 7: Configure
set /a STEP=STEP+1
echo [%STEP%] Configuring MedExtract...
echo [%STEP%] Configure >> "%TEMP%\medextract-install.log"

cd /d "%INSTALL_DIR%"

:: Check for Ollama (simple)
set USE_LOCAL_OLLAMA=NO
ollama --version >nul 2>&1
if not errorlevel 1 (
    echo     Local Ollama found
    set USE_LOCAL_OLLAMA=YES
)

:: Check network (simple)
set CORPORATE=NO
ping -n 1 -w 1000 registry.ollama.ai >nul 2>&1
if errorlevel 1 (
    echo     Corporate network detected
    set CORPORATE=YES
)

:: Configure based on detection
if "%USE_LOCAL_OLLAMA%"=="YES" (
    echo     Using local Ollama configuration
    if exist "docker-compose.duke.yml" (
        copy docker-compose.duke.yml docker-compose.yml >nul
    ) else (
        :: Create simple config for local Ollama
        call :CREATE_LOCAL_CONFIG
    )
) else (
    echo     Using container Ollama configuration
    if "%CORPORATE%"=="YES" (
        :: Create insecure config for corporate
        call :CREATE_CORP_CONFIG
    )
    copy docker-compose.real.yml docker-compose.yml >nul 2>&1
)

echo     [OK] Configuration complete
echo.

:BUILD
:: STEP 8: Build
set /a STEP=STEP+1
echo [%STEP%] Building MedExtract (10-20 minutes)...
echo [%STEP%] Build >> "%TEMP%\medextract-install.log"
echo.
echo     This will take time. Please wait...
echo.

docker-compose build --no-cache
if errorlevel 1 goto BUILDFAIL
echo.
echo     [OK] Build complete
echo.
goto START

:BUILDFAIL
echo.
echo     ERROR: Build failed
echo     Check Docker and disk space
echo.
pause
exit

:START
:: STEP 9: Start services
set /a STEP=STEP+1
echo [%STEP%] Starting services...
echo [%STEP%] Start >> "%TEMP%\medextract-install.log"

docker-compose up -d >nul 2>&1
echo     [OK] Services started
echo.

:SHORTCUTS
:: STEP 10: Create shortcuts
set /a STEP=STEP+1
echo [%STEP%] Creating shortcuts...
echo [%STEP%] Shortcuts >> "%TEMP%\medextract-install.log"

:: Start shortcut
echo @echo off > "%USERPROFILE%\Desktop\MedExtract.bat"
echo cd /d "%INSTALL_DIR%" >> "%USERPROFILE%\Desktop\MedExtract.bat"
echo docker-compose up -d >> "%USERPROFILE%\Desktop\MedExtract.bat"
echo timeout /t 5 ^>nul >> "%USERPROFILE%\Desktop\MedExtract.bat"
echo start http://localhost:3000 >> "%USERPROFILE%\Desktop\MedExtract.bat"

:: Stop shortcut
echo @echo off > "%USERPROFILE%\Desktop\Stop-MedExtract.bat"
echo cd /d "%INSTALL_DIR%" >> "%USERPROFILE%\Desktop\Stop-MedExtract.bat"
echo docker-compose down >> "%USERPROFILE%\Desktop\Stop-MedExtract.bat"
echo pause >> "%USERPROFILE%\Desktop\Stop-MedExtract.bat"

echo     [OK] Shortcuts created
echo.

:SUCCESS
:: Success message
echo ============================================
echo        INSTALLATION COMPLETE!
echo ============================================
echo.
echo Location: %INSTALL_DIR%
echo Log file: %TEMP%\medextract-install.log
echo.
echo Desktop shortcuts:
echo   - MedExtract.bat (start app)
echo   - Stop-MedExtract.bat (stop app)
echo.
if "%USE_LOCAL_OLLAMA%"=="YES" (
    echo Using local Ollama - no TLS issues
    echo To download models: ollama pull llama2
) else (
    echo Using container Ollama
    echo Download models from the web interface
)
echo.
echo Starting MedExtract...
timeout /t 5 /nobreak >nul
start http://localhost:3000
echo.
echo ============================================
echo.
pause
exit

:: Helper functions
:CREATE_LOCAL_CONFIG
(
echo version: '3.8'
echo services:
echo   backend:
echo     build: ./backend
echo     volumes:
echo       - ./backend:/app
echo       - ./output:/app/output
echo     ports:
echo       - "8000:8000"
echo     environment:
echo       - OLLAMA_HOST=http://host.docker.internal:11434
echo     extra_hosts:
echo       - "host.docker.internal:host-gateway"
echo   frontend:
echo     build: ./frontend
echo     ports:
echo       - "3000:3000"
echo     environment:
echo       - NEXT_PUBLIC_API_URL=http://localhost:8000
) > docker-compose.yml
exit /b

:CREATE_CORP_CONFIG
mkdir ollama-insecure 2>nul
(
echo FROM ollama/ollama:latest
echo ENV OLLAMA_INSECURE=1
echo CMD ["serve"]
) > ollama-insecure\Dockerfile
exit /b