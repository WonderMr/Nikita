# create-installer.ps1 - Создание Windows инсталлятора с автоматической загрузкой NSIS
# Использование: .\create-installer.ps1

$ErrorActionPreference                              =   "Stop"

# Импорт общих функций
Import-Module $PSScriptRoot\common.ps1

Write-Header "Создание Windows инсталлятора"

try {
    # Переход в корень проекта
    Push-Location (Split-Path -Parent $PSScriptRoot)

    # ======================================================================================================================
    # ЭТАП 1: ПРОВЕРКА ПРЕДУСЛОВИЙ
    # ======================================================================================================================
    
    Write-Header "Этап 1/3: Проверка предусловий"

    # Проверка наличия дистрибутива
    if (!(Test-Path "dist\Nikita\Nikita.exe")) {
        throw "Дистрибутив не найден! Сначала запустите сборку: .\scripts\build.ps1"
    }
    
    Write-Success "Дистрибутив найден: dist\Nikita\Nikita.exe"
    
    # Проверка наличия NSI скрипта
    $nsiScript                                      =   "scripts\c.installer.nsi"
    if (!(Test-Path $nsiScript)) {
        throw "NSI скрипт не найден: $nsiScript"
    }
    
    Write-Success "NSI скрипт найден: $nsiScript"

    # ======================================================================================================================
    # ЭТАП 2: ПОДГОТОВКА NSIS
    # ======================================================================================================================
    
    Write-Header "Этап 2/3: Подготовка NSIS"

    # Поиск или загрузка NSIS
    Write-Info "Поиск NSIS..."
    
    $nsisPath                                       =   $null
    $nsisLocations                                  =   @(
        "$env:PROGRAMFILES\NSIS\makensis.exe",
        "${env:PROGRAMFILES(X86)}\NSIS\makensis.exe",
        "nsis\makensis.exe"
    )

    foreach ($location in $nsisLocations) {
        if (Test-Path $location) {
            $nsisPath                               =   (Resolve-Path $location).Path
            Write-Success "NSIS найден: $nsisPath"
            break
        }
    }

    # Если NSIS не найден — загружаем
    if (!$nsisPath) {
        Write-Info "NSIS не найден, установка..."
        try {
            $nsisDir                                =   Download-NSIS
            
            if ($nsisDir) {
                # Проверяем, является ли $nsisDir путём к файлу или к папке
                if (Test-Path "$nsisDir\makensis.exe") {
                    $nsisPath                       =   "$nsisDir\makensis.exe"
                } elseif (Test-Path $nsisDir -PathType Leaf) {
                    $nsisPath                       =   $nsisDir
                } else {
                    throw "makensis.exe не найден после загрузки: $nsisDir"
                }
                
                Write-Success "NSIS установлен: $nsisPath"
            } else {
                throw "Download-NSIS вернул пустой путь"
            }
        } catch {
            Write-Error "Не удалось установить NSIS: $($_.Exception.Message)"
            throw
        }
    }
    
    # ======================================================================================================================
    # ЭТАП 3: СОЗДАНИЕ ИНСТАЛЛЯТОРА
    # ======================================================================================================================
    
    Write-Header "Этап 3/3: Создание инсталлятора"
    Write-Info "Запуск NSIS для создания инсталлятора..."
    Write-Info "Команда: $nsisPath $nsiScript"
    
    $process                                        =   Start-Process -FilePath $nsisPath `
                                                        -ArgumentList "`"$(Resolve-Path $nsiScript)`"" `
                                                        -NoNewWindow `
                                                        -Wait `
                                                        -PassThru

    if ($process.ExitCode -eq 0) {
        Write-Success "Инсталлятор создан успешно!"
        
        # Поиск созданного инсталлятора
        $installers                                 =   Get-ChildItem -Path "scripts" -Filter "Nikita*.exe" -File | 
                                                        Where-Object { $_.Name -match "setup" }
        
        if ($installers) {
            foreach ($installer in $installers) {
                Write-Success "Инсталлятор: $($installer.FullName)"
                Write-Success "Размер: $([math]::Round($installer.Length / 1MB, 2)) MB"
            }
        } else {
            Write-Warning "Инсталлятор должен быть в папке scripts/"
        }
    } else {
        throw "NSIS завершился с ошибкой (код: $($process.ExitCode))"
    }

} catch {
    Write-Error "Ошибка создания инсталлятора: $($_.Exception.Message)"
    exit 1
} finally {
    Pop-Location
}

Write-Success "Создание инсталлятора завершено"

