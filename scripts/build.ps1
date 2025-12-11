# build.ps1 - Основная сборка Nikita
# Использование: .\build.ps1 [-Optimize] [-NoTest]

param(
    [switch]$Optimize,
    [switch]$NoTest,
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

    # Очистка предыдущих сборок
    Write-Info "Очистка предыдущих сборок..."
    if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
    if (Test-Path "build") { Remove-Item "build" -Recurse -Force }

    # Переименование .yp обратно в .py для сборки (если они есть)
    Write-Info "Подготовка исходников (переименование .yp → .py)..."
    $ypFiles                                                =   Get-ChildItem "src\*.yp" -ErrorAction SilentlyContinue
    if ($ypFiles) {
        foreach ($file in $ypFiles) {
            $newName                                        =   $file.Name -replace '\.yp$', '.py'
            $newPath                                        =   Join-Path $file.DirectoryName $newName
            # Если уже есть .py файл — удаляем .yp
            if (Test-Path $newPath) {
                Remove-Item $file.FullName -Force
                Write-Info "  Удалён дубликат: $($file.Name) (есть $newName)"
            } else {
                Rename-Item $file.FullName $newName
                Write-Info "  Переименован: $($file.Name) → $newName"
            }
        }
    }

    # Компиляция Python модулей в .pyd (опционально)
    if ($Optimize) {
        Write-Info "Компиляция .pyd файлов..."
        if (Test-Path "src\*.pyd") { Remove-Item "src\*.pyd" -Force }

        # Переименование .py в .yp для защиты
        Get-ChildItem "src\*.py" | Where-Object { $_.Name -ne "cherry.py" } | ForEach-Object {
            $newName = $_.Name -replace '\.py$', '.yp'
            Rename-Item $_.FullName $newName
        }
        Rename-Item "src\cherry.py" "src\cherry.p"

        # Запуск компиляции Cython
        python "scripts\b.compiles2pyd.py" build_ext --inplace

        # Восстановление имен файлов
        Rename-Item "src\cherry.p" "src\cherry.py"
        Get-ChildItem "src\*.yp" | ForEach-Object {
            $newName = $_.Name -replace '\.yp$', '.py'
            Rename-Item $_.FullName $newName
        }

        Remove-Item "src\*.pyd" -Force
    }

    # Сборка с PyInstaller
    $extraImports = @()
    if ($Optimize) {
        $extraImports = @("clickhouse_driver", "win32timezone")
    }

    Invoke-PyInstaller -Optimize:$Optimize -ExtraHiddenImports $extraImports -OutputName $OutputName

    # Копирование DLL файлов
    Copy-Dlls

    # Загрузка и копирование Java/Solr если отсутствуют
    $javaPath = $null
    $solrPath = $null

    if (!(Test-Path "java")) {
        Write-Info "Java не найдена, загрузка..."
        try {
            $javaPath = Download-Java
        } catch {
            Write-Warning "Не удалось загрузить Java, сборка продолжится без неё: $($_.Exception.Message)"
        }
    } else {
        $javaPath = Resolve-Path "java"
        Write-Info "Использование существующей Java: $javaPath"
    }

    if (!(Test-Path "solr")) {
        Write-Info "Solr не найдена, загрузка..."
        try {
            $solrPath = Download-Solr
        } catch {
            Write-Warning "Не удалось загрузить Solr, сборка продолжится без неё: $($_.Exception.Message)"
        }
    } else {
        $solrPath = Resolve-Path "solr"
        Write-Info "Использование существующей Solr: $solrPath"
    }

    # Копирование Java и Solr в дистрибутив (если они загрузились)
    if ($javaPath -or $solrPath) {
        Copy-JavaSolr -JavaPath $javaPath -SolrPath $solrPath
    }

    # Тестирование собранного приложения
    if (!$NoTest) {
        $appPath = "dist\$OutputName\$OutputName.exe"
        if (!(Test-Application -AppPath $appPath)) {
            throw "Собранное приложение не проходит тестирование"
        }
    }

    # Возврат .py обратно в .yp для защиты исходников
    Write-Info "Защита исходников (переименование .py → .yp)..."
    $pyFiles                                                =   Get-ChildItem "src\*.py" -ErrorAction SilentlyContinue | 
                                                                Where-Object { $_.Name -ne "cherry.py" -and $_.Name -ne "__init__.py" }
    if ($pyFiles) {
        foreach ($file in $pyFiles) {
            $newName                                        =   $file.Name -replace '\.py$', '.yp'
            $newPath                                        =   Join-Path $file.DirectoryName $newName
            # Удаляем старый .yp если существует
            if (Test-Path $newPath) {
                Remove-Item $newPath -Force
            }
            Rename-Item $file.FullName $newName
            Write-Info "  Переименован: $($file.Name) → $newName"
        }
    }

    Write-Success "Сборка завершена успешно!"
    Write-Info "Результат: $(Resolve-Path "dist\$OutputName")"

} catch {
    Write-Error "Ошибка сборки: $($_.Exception.Message)"
    
    # Даже при ошибке возвращаем файлы обратно в .yp
    Write-Info "Откат: возврат .py → .yp..."
    $pyFiles                                                =   Get-ChildItem "src\*.py" -ErrorAction SilentlyContinue | 
                                                                Where-Object { $_.Name -ne "cherry.py" -and $_.Name -ne "__init__.py" }
    if ($pyFiles) {
        foreach ($file in $pyFiles) {
            $newName                                        =   $file.Name -replace '\.py$', '.yp'
            $newPath                                        =   Join-Path $file.DirectoryName $newName
            if (Test-Path $newPath) {
                Remove-Item $newPath -Force -ErrorAction SilentlyContinue
            }
            Rename-Item $file.FullName $newName -ErrorAction SilentlyContinue
        }
    }
    
    exit 1
} finally {
    Pop-Location
}

Write-Info "Для создания инсталлятора используйте: .\!c.build.win.distr.cmd"
