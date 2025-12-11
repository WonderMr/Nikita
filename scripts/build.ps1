# build.ps1 - Основная сборка Nikita
# Использование: .\build.ps1 [-Optimize] [-NoTest]

param(
    [switch]$Optimize,
    [switch]$NoTest,
    [switch]$SkipSolr,
    [string]$OutputName = "Nikita"
)

$ErrorActionPreference = "Stop"

# Импорт общих функций
Import-Module $PSScriptRoot\common.ps1

Write-Header "Сборка Nikita"

try {
    # Проверка предусловий
    Test-Prerequisites

    # Переход в корень проекта
    Push-Location (Split-Path -Parent $PSScriptRoot)

    # ======================================================================================================================
    # ЭТАП 1: ПОДГОТОВКА ЗАВИСИМОСТЕЙ
    # ======================================================================================================================
    
    Write-Header "Этап 1/3: Подготовка зависимостей"
    
    # Загрузка Java (если отсутствует)
    $javaPath                                               =   $null
    
    # Проверяем наличие Java (папка должна существовать И не быть пустой)
    $javaExists                                             =   $false
    if (Test-Path "java") {
        $javaContent                                        =   Get-ChildItem "java" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($javaContent) {
            $javaExists                                     =   $true
        } else {
            Write-Warning "Папка java существует, но пустая - будет удалена"
            Remove-Item "java" -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    
    if (!$javaExists) {
        Write-Info "Java не найдена, загрузка..."
        try {
            $javaPath                                       =   Download-Java
            Write-Success "Java загружена успешно: $javaPath"
        } catch {
            Write-Warning "Не удалось загрузить Java: $($_.Exception.Message)"
            Write-Warning "Сборка продолжится без Java"
        }
    } else {
        $javaPath                                           =   Resolve-Path "java"
        Write-Success "Java уже установлена: $javaPath"
    }

    # Загрузка Solr (если отсутствует)
    $solrPath                                               =   $null
    
    # Проверяем наличие Solr (папка должна существовать И не быть пустой)
    $solrExists                                             =   $false
    if (Test-Path "solr") {
        $solrContent                                        =   Get-ChildItem "solr" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($solrContent) {
            $solrExists                                     =   $true
        } else {
            Write-Warning "Папка solr существует, но пустая - будет удалена"
            Remove-Item "solr" -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    
    if ($SkipSolr) {
        Write-Warning "Пропуск загрузки Solr (параметр -SkipSolr)"
    } elseif (!$solrExists) {
        Write-Info "Solr не найдена, загрузка..."
        try {
            $solrPath                                       =   Download-Solr
            Write-Success "Solr загружена успешно: $solrPath"
        } catch {
            Write-Error "Не удалось загрузить Solr: $($_.Exception.Message)"
            Write-Host ""
            Write-Host "============================================================" -ForegroundColor Red
            Write-Host "  ⛔ ТРЕБУЕТСЯ РУЧНАЯ УСТАНОВКА SOLR" -ForegroundColor Yellow
            Write-Host "============================================================" -ForegroundColor Red
            Write-Host ""
            Write-Host "❌ Автоматическая загрузка не удалась (404 Not Found)" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "📋 ДВА ВАРИАНТА РЕШЕНИЯ:" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "ВАРИАНТ 1: Установить Solr вручную" -ForegroundColor Green
            Write-Host "  ────────────────────────────────────" -ForegroundColor Gray
            Write-Host "  1. Откройте браузер и перейдите:" -ForegroundColor White
            Write-Host "     https://solr.apache.org/downloads.html" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  2. Скачайте Solr (любая версия 8.x или 9.x):" -ForegroundColor White
            Write-Host "     • Рекомендуется: 9.6.1, 9.5.0, 8.11.3" -ForegroundColor Gray
            Write-Host "     • Файл: solr-X.X.X.zip (~250 MB)" -ForegroundColor Gray
            Write-Host ""
            Write-Host "  3. Распакуйте архив в папку проекта:" -ForegroundColor White
            Write-Host "     $((Get-Location).Path)\solr\" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "  4. Итоговая структура:" -ForegroundColor White
            Write-Host "     solr\" -ForegroundColor Gray
            Write-Host "       └── solr-X.X.X\" -ForegroundColor Gray
            Write-Host "           ├── bin\solr.cmd" -ForegroundColor Gray
            Write-Host "           ├── server\" -ForegroundColor Gray
            Write-Host "           └── ..." -ForegroundColor Gray
            Write-Host ""
            Write-Host "  5. Запустите сборку снова:" -ForegroundColor White
            Write-Host "     .\scripts\!c.build.win.distr.cmd" -ForegroundColor Green
            Write-Host ""
            Write-Host "ВАРИАНТ 2: Собрать без Solr (если не нужен)" -ForegroundColor Green
            Write-Host "  ────────────────────────────────────" -ForegroundColor Gray
            Write-Host "  Запустите сборку с параметром -SkipSolr:" -ForegroundColor White
            Write-Host "  .\scripts\build.ps1 -Optimize -NoTest -SkipSolr" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "============================================================" -ForegroundColor Red
            throw "Сборка остановлена: Solr не установлена"
        }
    } else {
        $solrPath                                           =   Resolve-Path "solr"
        Write-Success "Solr уже установлена: $solrPath"
    }
    
    Write-Success "Все зависимости подготовлены!"
    
    # ======================================================================================================================
    # ЭТАП 2: СБОРКА ПРИЛОЖЕНИЯ
    # ======================================================================================================================
    
    Write-Header "Этап 2/3: Сборка приложения"

    # Очистка предыдущих сборок
    Write-Info "Очистка предыдущих сборок..."
    if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
    if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
    
    # Очистка старых .yp файлов (если остались после предыдущих сборок)
    $ypFiles                                                =   Get-ChildItem "src\*.yp" -ErrorAction SilentlyContinue
    if ($ypFiles) {
        Write-Info "Очистка старых .yp файлов..."
        foreach ($file in $ypFiles) {
            Remove-Item $file.FullName -Force
            Write-Info "  Удалён: $($file.Name)"
        }
    }

    # Компиляция Python модулей в .pyd (опционально)
    # ПРИМЕЧАНИЕ: Компиляция Cython временно отключена, так как:
    # 1. Требуется наличие .py файлов для компиляции
    # 2. Результаты (.pyd) всё равно удаляются после сборки
    # 3. PyInstaller корректно работает с .py файлами
    # Если нужна реальная компиляция в .pyd, эту секцию нужно переделать
    if ($Optimize) {
        Write-Info "Очистка старых .pyd файлов (если есть)..."
        if (Test-Path "src\*.pyd") { Remove-Item "src\*.pyd" -Force }
        Write-Info "Компиляция Cython пропущена (файлы будут упакованы PyInstaller)"
    }

    # Сборка с PyInstaller
    $extraImports = @()
    if ($Optimize) {
        $extraImports = @("clickhouse_driver", "win32timezone")
    }

    Invoke-PyInstaller -Optimize:$Optimize -ExtraHiddenImports $extraImports -OutputName $OutputName
    
    # Проверка успешности PyInstaller
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller завершился с ошибкой (код: $LASTEXITCODE)"
    }
    
    if (!(Test-Path "dist\$OutputName\$OutputName.exe")) {
        throw "Исполняемый файл не создан: dist\$OutputName\$OutputName.exe"
    }

    # Копирование DLL файлов
    Copy-Dlls
    
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
        throw "Ошибка копирования DLL файлов"
    }
    
    # ======================================================================================================================
    # ЭТАП 3: КОПИРОВАНИЕ ЗАВИСИМОСТЕЙ В ДИСТРИБУТИВ
    # ======================================================================================================================
    
    Write-Header "Этап 3/3: Копирование зависимостей"

    # Копирование Java и Solr в дистрибутив (если они были загружены)
    if ($javaPath -or $solrPath) {
        Copy-JavaSolr -JavaPath $javaPath -SolrPath $solrPath
        
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
            throw "Ошибка копирования Java/Solr"
        }
    } else {
        Write-Warning "Java и Solr отсутствуют, пропускаем копирование"
    }

    # Тестирование собранного приложения
    if (!$NoTest) {
        $appPath = "dist\$OutputName\$OutputName.exe"
        if (!(Test-Application -AppPath $appPath)) {
            throw "Собранное приложение не проходит тестирование"
        }
    }

    Write-Success "Сборка завершена успешно!"
    Write-Info "Результат: $(Resolve-Path "dist\$OutputName")"

} catch {
    Write-Error "Ошибка сборки: $($_.Exception.Message)"
    exit 1
} finally {
    Pop-Location
}

Write-Info "Для создания инсталлятора используйте: .\!c.build.win.distr.cmd"
