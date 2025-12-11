# common.ps1 - Общие функции для сборки Nikita
# Использование: Import-Module $PSScriptRoot\common.ps1

$Script:JavaVersion                                 =   "17"
$Script:SolrVersion                                 =   "9.10.0"
$Script:NSISVersion                                 =   "3.10"
$Script:ProjectRoot                                 =   Split-Path -Parent $PSScriptRoot

function Write-Header {
    param([string]$Message)
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Yellow
    Write-Host "==================================================" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Blue
}

function Find-Python {
    <#
    .SYNOPSIS
        Ищет установленный Python в Windows через сканирование файловой системы
    .DESCRIPTION
        Сканирует стандартные пути установки Python, проверяет версии и возвращает путь к последней подходящей версии (3.8-3.14)
    .OUTPUTS
        [string] Полный путь к python.exe или $null если не найден
    #>
    
    Write-Info "Поиск Python в системе (3.8 - 3.14)..."
    
    # Кеш для избежания повторного поиска в одной сессии
    if ($Script:FoundPythonPath) {
        Write-Info "Используется кешированный путь: $Script:FoundPythonPath"
        return $Script:FoundPythonPath
    }
    
    # Пути для поиска
    $searchPaths                                            =   @(
        "C:\Python*\python.exe",
        "C:\Program Files\Python*\python.exe",
        "C:\Program Files (x86)\Python*\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe",
        "$env:APPDATA\Python\Python*\python.exe"
    )
    
    $foundPythons                                           =   @()
    
    # Сканирование путей
    foreach ($pattern in $searchPaths) {
        try {
            $paths                                          =   Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
            foreach ($path in $paths) {
                if (Test-Path $path) {
                    try {
                        # Получаем версию Python
                        $versionOutput                      =   & $path --version 2>&1 | Out-String
                        
                        # Парсим версию через regex: Python 3.X.Y
                        if ($versionOutput -match 'Python\s+(\d+)\.(\d+)\.(\d+)') {
                            $major                          =   [int]$matches[1]
                            $minor                          =   [int]$matches[2]
                            $patch                          =   [int]$matches[3]
                            
                            # Фильтр: 3.8 <= версия <= 3.14
                            if ($major -eq 3 -and $minor -ge 8 -and $minor -le 14) {
                                $foundPythons               +=  @{
                                    Path                    =   $path.FullName
                                    Major                   =   $major
                                    Minor                   =   $minor
                                    Patch                   =   $patch
                                    Version                 =   "$major.$minor.$patch"
                                }
                                Write-Info "  Найден: Python $major.$minor.$patch - $($path.FullName)"
                            }
                        }
                    } catch {
                        # Игнорируем ошибки при проверке конкретного python.exe
                        continue
                    }
                }
            }
        } catch {
            # Игнорируем ошибки доступа к каталогам
            continue
        }
    }
    
    if ($foundPythons.Count -eq 0) {
        Write-Info "Python 3.8-3.14 не найден в стандартных путях"
        return $null
    }
    
    # Сортируем по версии (major.minor.patch) и выбираем последнюю
    $selectedPython                                         =   $foundPythons | 
                                                                Sort-Object -Property Major, Minor, Patch -Descending | 
                                                                Select-Object -First 1
    
    Write-Success "Выбран Python $($selectedPython.Version): $($selectedPython.Path)"
    
    # Кешируем результат
    $Script:FoundPythonPath                                 =   $selectedPython.Path
    
    return $selectedPython.Path
}

function Test-Prerequisites {
    Write-Info "Проверка необходимых компонентов..."

    # Проверка Python через Find-Python
    try {
        $pythonPath                                         =   $null
        Write-Info "Поиск Python..."

        # Попробовать команду python из PATH
        if (Get-Command python -ErrorAction SilentlyContinue) {
            try {
                $pythonVersion                              =   python --version 2>&1
                # Проверить, что это не Microsoft Store alias
                if ($pythonVersion -notmatch "Microsoft Store" -and $pythonVersion -notmatch "was not found") {
                    $pythonPath                             =   (Get-Command python).Source
                    Write-Success "Python найден в PATH: $pythonVersion"
                }
            } catch {
                # Игнорируем ошибки
            }
        }

        # Если в PATH не нашли — используем Find-Python
        if (!$pythonPath) {
            $pythonPath                                     =   Find-Python
            if (!$pythonPath) {
                Write-Error "Python 3.8-3.14 не найден в системе"
                throw "Python not found in any location"
            }
        }

        # Сохраняем путь для дальнейшего использования
        $Script:PythonPath                                  =   $pythonPath
        
    } catch {
        Write-Error "Python не найден. Установите Python 3.8-3.14"
        throw "Python не найден"
    }

    # Проверка pip
    try {
        if (Get-Command pip -ErrorAction SilentlyContinue) {
            $pipVersion                                     =   pip --version 2>&1
            Write-Success "pip найден: $pipVersion"
        } elseif ($Script:PythonPath) {
            $pipVersion                                     =   & $Script:PythonPath -m pip --version 2>&1
            Write-Success "pip найден: $pipVersion"
        } else {
            throw "pip not found"
        }
    } catch {
        Write-Error "pip не найден. Установите pip"
        throw "pip не найден"
    }

    # Проверка git (для некоторых операций)
    try {
        $gitVersion                                         =   git --version 2>&1
        Write-Success "Git найден: $gitVersion"
    } catch {
        Write-Warning "Git не найден. Некоторые операции могут быть недоступны"
    }

    Write-Success "Все необходимые компоненты найдены"
}

function Download-Java {
    param(
        [string]$TargetPath = "$ProjectRoot\java",
        [string]$JavaUrl = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.12_7.zip"
    )

    Write-Info "Загрузка Java $JavaVersion..."

    if (Test-Path $TargetPath) {
        Write-Info "Java уже установлена в $TargetPath"
        return $TargetPath
    }

    $tempFile = "$env:TEMP\java_$JavaVersion.zip"

    try {
        Write-Info "Загрузка с $JavaUrl..."
        Invoke-WebRequest -Uri $JavaUrl -OutFile $tempFile -UseBasicParsing

        Write-Info "Распаковка в $TargetPath..."
        Expand-Archive -Path $tempFile -DestinationPath $TargetPath -Force

        # Найти папку с JDK
        $jdkFolder = Get-ChildItem $TargetPath | Where-Object { $_.PSIsContainer } | Select-Object -First 1
        if ($jdkFolder) {
            $jdkPath = Join-Path $TargetPath $jdkFolder.Name
            Write-Success "Java установлена в $jdkPath"
            return $jdkPath
        } else {
            throw "Не удалось найти JDK папку после распаковки"
        }
    } catch {
        Write-Error "Ошибка при загрузке Java: $($_.Exception.Message)"
        throw
    } finally {
        if (Test-Path $tempFile) {
            Remove-Item $tempFile -Force
        }
    }
}

function Download-Solr {
    param(
        [string]$TargetPath = "$ProjectRoot\solr"
    )

    Write-Info "Загрузка Apache Solr $SolrVersion..."

    if (Test-Path $TargetPath) {
        Write-Info "Solr уже установлен в $TargetPath"
        return $TargetPath
    }

    # Официальный зеркальный URL для Solr
    $solrUrls                                       =   @(
        "https://www.apache.org/dyn/closer.lua/solr/solr/$SolrVersion/solr-$SolrVersion.tgz?action=download",
        "https://archive.apache.org/dist/solr/solr/$SolrVersion/solr-$SolrVersion.tgz",
        "https://dlcdn.apache.org/solr/solr/$SolrVersion/solr-$SolrVersion.tgz"
    )

    $tempFile                                       =   "$env:TEMP\solr_$SolrVersion.tgz"
    $downloadSuccess                                =   $false

    foreach ($solrUrl in $solrUrls) {
        try {
            Write-Info "Попытка загрузки с $solrUrl..."
            Invoke-WebRequest -Uri $solrUrl -OutFile $tempFile -UseBasicParsing -TimeoutSec 120 -MaximumRedirection 10
            $downloadSuccess                        =   $true
            Write-Success "Загрузка успешна!"
            break
        } catch {
            Write-Warning "Не удалось загрузить с $solrUrl : $($_.Exception.Message)"
            continue
        }
    }

    if (!$downloadSuccess) {
        throw "Не удалось загрузить Solr ни с одного зеркала"
    }

    try {
        Write-Info "Распаковка Solr (это может занять минуту)..."
        
        # Проверяем наличие tar (встроен в Windows 10+)
        if (Get-Command tar -ErrorAction SilentlyContinue) {
            Write-Info "Использование встроенного tar для распаковки..."
            New-Item -ItemType Directory -Path "$ProjectRoot\temp_solr" -Force | Out-Null
            
            # tar -xzf распаковывает .tgz
            & tar -xzf $tempFile -C "$ProjectRoot\temp_solr"
            
            if ($LASTEXITCODE -ne 0) {
                throw "Ошибка распаковки через tar (код: $LASTEXITCODE)"
            }
        } else {
            throw "Команда tar не найдена. Требуется Windows 10+ или установка tar/7-Zip"
        }

        # Найти папку с Solr и переместить её
        $solrFolder                                 =   Get-ChildItem "$ProjectRoot\temp_solr" | 
                                                        Where-Object { $_.PSIsContainer -and $_.Name -like "solr-*" } | 
                                                        Select-Object -First 1
        
        if ($solrFolder) {
            Move-Item $solrFolder.FullName $TargetPath -Force
            Remove-Item "$ProjectRoot\temp_solr" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Success "Solr установлен в $TargetPath"
            return $TargetPath
        } else {
            throw "Не удалось найти Solr папку после распаковки"
        }
    } catch {
        Write-Error "Ошибка при установке Solr: $($_.Exception.Message)"
        throw
    } finally {
        if (Test-Path $tempFile) {
            Remove-Item $tempFile -Force
        }
        if (Test-Path "$ProjectRoot\temp_solr") {
            Remove-Item "$ProjectRoot\temp_solr" -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

function Download-NSIS {
    param(
        [string]$TargetPath = "$ProjectRoot\nsis"
    )

    Write-Info "Поиск NSIS $NSISVersion..."

    # Проверяем установленный NSIS в стандартных местах
    $nsisLocations                                  =   @(
        "$env:PROGRAMFILES\NSIS\makensis.exe",
        "${env:PROGRAMFILES(X86)}\NSIS\makensis.exe",
        "$TargetPath\makensis.exe"
    )

    foreach ($location in $nsisLocations) {
        if (Test-Path $location) {
            Write-Success "NSIS найден: $location"
            return (Split-Path -Parent $location)
        }
    }

    Write-Info "NSIS не найден, установка..."

    # Пробуем использовать Chocolatey (если установлен)
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        try {
            Write-Info "Установка NSIS через Chocolatey..."
            & choco install nsis -y --no-progress
            
            # Проверяем повторно
            foreach ($location in $nsisLocations) {
                if (Test-Path $location) {
                    Write-Success "NSIS установлен: $location"
                    return (Split-Path -Parent $location)
                }
            }
        } catch {
            Write-Warning "Не удалось установить через Chocolatey: $($_.Exception.Message)"
        }
    }

    # Если Chocolatey недоступен, загружаем установщик напрямую
    Write-Info "Загрузка NSIS установщика..."
    $nsisUrl                                        =   "https://downloads.sourceforge.net/project/nsis/NSIS%203/$NSISVersion/nsis-$NSISVersion-setup.exe"
    $tempInstaller                                  =   "$env:TEMP\nsis-setup.exe"

    try {
        Write-Info "Загрузка с SourceForge..."
        # Используем альтернативный URL с прямой ссылкой
        Invoke-WebRequest -Uri $nsisUrl -OutFile $tempInstaller -UseBasicParsing -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -TimeoutSec 120 -MaximumRedirection 5

        Write-Info "Установка NSIS в $TargetPath..."
        # Установка в локальную папку проекта без требования админ-прав
        New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
        
        # Запускаем установщик в тихом режиме с указанием пути
        $installArgs                                =   "/S /D=$TargetPath"
        $process                                    =   Start-Process -FilePath $tempInstaller -ArgumentList $installArgs -Wait -PassThru -NoNewWindow

        if ($process.ExitCode -eq 0 -and (Test-Path "$TargetPath\makensis.exe")) {
            Write-Success "NSIS установлен в $TargetPath"
            return $TargetPath
        } else {
            throw "Установка не удалась (код: $($process.ExitCode))"
        }
    } catch {
        Write-Error "Ошибка при установке NSIS: $($_.Exception.Message)"
        Write-Warning "Попробуйте установить NSIS вручную с https://nsis.sourceforge.io/"
        throw
    } finally {
        if (Test-Path $tempInstaller) {
            Remove-Item $tempInstaller -Force -ErrorAction SilentlyContinue
        }
    }
}

function Invoke-PyInstaller {
    param(
        [switch]$Optimize,
        [string[]]$ExtraHiddenImports = @(),
        [string]$OutputName = "Nikita"
    )

    Write-Info "Запуск PyInstaller..."

    # Базовые аргументы
    $pyinstallerArgs = @(
        "$ProjectRoot\Nikita.py",
        "--onedir",
        "--console",
        "--clean",
        "--exclude-module", "numpy",
        "--exclude-module", "cryptography",
        "--exclude-module", "lib2to3",
        "--exclude-module", "win32com",
        "--hidden-import", "subprocess",
        "--hidden-import", "cherrypy",
        "--hidden-import", "urllib",
        "--hidden-import", "threading",
        "--hidden-import", "requests",
        "--hidden-import", "re",
        "--hidden-import", "time",
        "--hidden-import", "operator",
        "--hidden-import", "json",
        "--hidden-import", "psutil",
        "--hidden-import", "shlex",
        "--hidden-import", "platform",
        "--hidden-import", "socket",
        "--hidden-import", "sqlite3",
        "--hidden-import", "src.parser",
        "--hidden-import", "src.reader",
        "--hidden-import", "src.dictionaries",
        "--hidden-import", "src.messenger",
        "--hidden-import", "src.globals",
        "--hidden-import", "src.tools",
        "--hidden-import", "src.solr",
        "--hidden-import", "src.sender",
        "--hidden-import", "src.redis_manager",
        "--hidden-import", "src.state_manager",
        "--hidden-import", "src.parser_state",
        "--hidden-import", "src.cherry",
        "--log-level", "DEBUG",
        "--name", $OutputName
    )

    # Дополнительные hidden imports
    foreach ($import in $ExtraHiddenImports) {
        $pyinstallerArgs += @("--hidden-import", $import)
    }

    # Оптимизация
    if ($Optimize) {
        $env:PYTHONOPTIMIZE = "1"
        $pyinstallerArgs += @("--exclude-module", "gevent")
        $pyinstallerArgs += @("--exclude-module", "matplotlib")
        $pyinstallerArgs += @("--exclude-module", "__PyInstaller_hooks_0_pandas_io_formats_style")
        $pyinstallerArgs += @("--hidden-import", "clickhouse_driver")
        $pyinstallerArgs += @("--hidden-import", "win32timezone")
    }

    try {
        # Определяем путь к pyinstaller
        $pyinstallerPath                                    =   $null
        if (Get-Command pyinstaller -ErrorAction SilentlyContinue) {
            $pyinstallerPath                                =   "pyinstaller"
        } elseif ($Script:PythonPath) {
            # Пробуем найти pyinstaller рядом с найденным Python
            $pythonDir                                      =   Split-Path -Parent $Script:PythonPath
            $scriptsDir                                     =   Join-Path $pythonDir "Scripts"
            $pyinstallerExe                                 =   Join-Path $scriptsDir "pyinstaller.exe"
            
            if (Test-Path $pyinstallerExe) {
                $pyinstallerPath                            =   $pyinstallerExe
            } else {
                # Пробуем запустить через python -m PyInstaller
                $pyinstallerPath                            =   $Script:PythonPath
                $pyinstallerArgs                            =   @("-m", "PyInstaller") + $pyinstallerArgs
            }
        } else {
            throw "PyInstaller не найден и путь к Python неизвестен"
        }

        Write-Info "Команда: $pyinstallerPath $($pyinstallerArgs -join ' ')"
        & $pyinstallerPath @pyinstallerArgs

        if ($LASTEXITCODE -eq 0) {
            Write-Success "PyInstaller завершён успешно"
        } else {
            throw "PyInstaller завершился с кодом $LASTEXITCODE"
        }
    } catch {
        Write-Error "Ошибка PyInstaller: $($_.Exception.Message)"
        throw
    } finally {
        if ($env:PYTHONOPTIMIZE) {
            Remove-Item env:PYTHONOPTIMIZE
        }
    }
}

function Copy-Dlls {
    param([string]$TargetDir = "$ProjectRoot\dist\Nikita")

    Write-Info "Копирование DLL файлов..."

    $dlls = Get-ChildItem "$ProjectRoot\dlls\*.dll"
    foreach ($dll in $dlls) {
        Copy-Item $dll.FullName $TargetDir
        Write-Info "Скопирован: $($dll.Name)"
    }

    Write-Success "DLL файлы скопированы"
}

function Copy-JavaSolr {
    param(
        [string]$JavaPath,
        [string]$SolrPath,
        [string]$TargetDir = "$ProjectRoot\dist\Nikita"
    )

    Write-Info "Копирование Java и Solr в дистрибутив..."

    if ($JavaPath -and (Test-Path $JavaPath)) {
        $javaTarget = Join-Path $TargetDir "java"
        Write-Info "Копирование Java из $JavaPath в $javaTarget"
        Copy-Item $JavaPath $javaTarget -Recurse -Force
    }

    if ($SolrPath -and (Test-Path $SolrPath)) {
        $solrTarget = Join-Path $TargetDir "solr"
        Write-Info "Копирование Solr из $SolrPath в $solrTarget"
        Copy-Item $SolrPath $solrTarget -Recurse -Force
    }

    Write-Success "Java и Solr скопированы"
}

function Test-Application {
    param([string]$AppPath = "$ProjectRoot\dist\Nikita\Nikita.exe")

    Write-Info "Тестирование собранного приложения..."

    if (!(Test-Path $AppPath)) {
        Write-Error "Приложение не найдено: $AppPath"
        return $false
    }

    try {
        Write-Info "Проверка запуска приложения..."
        $process = Start-Process $AppPath -ArgumentList "--version" -NoNewWindow -Wait -PassThru

        if ($process.ExitCode -eq 0) {
            Write-Success "Приложение запускается корректно"
            return $true
        } else {
            Write-Error "Приложение завершилось с кодом $($process.ExitCode)"
            return $false
        }
    } catch {
        Write-Error "Ошибка при тестировании: $($_.Exception.Message)"
        return $false
    }
}

# Функции доступны для использования в скриптах
