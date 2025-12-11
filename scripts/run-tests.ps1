# run-tests.ps1 - Запуск тестов Nikita для Windows
# Использование: .\run-tests.ps1 [-Verbose] [-CreateVenv]

param(
    [switch]$Verbose,
    [switch]$CreateVenv,
    [string]$VenvPath = "venv"
)

$ErrorActionPreference = "Stop"

# Импорт общих функций
Import-Module $PSScriptRoot\common.ps1

Write-Header "Запуск тестов Nikita"

try {
    # Проверка предусловий
    Test-Prerequisites

    # Переход в корень проекта
    Push-Location (Split-Path -Parent $PSScriptRoot)

    # Создание виртуального окружения
    if ($CreateVenv -or !(Test-Path $VenvPath)) {
        Write-Info "Создание виртуального окружения..."
        python -m venv $VenvPath
        Write-Success "Виртуальное окружение создано в $VenvPath"
    }

    # Активация виртуального окружения
    Write-Info "Активация виртуального окружения..."
    & "$VenvPath\Scripts\Activate.ps1"

    # Установка зависимостей для тестов
    Write-Info "Установка зависимостей для тестов..."
    pip install -r tests\requirements.test.txt --quiet

    # Запуск тестов
    Write-Info "Запуск тестов..."
    $testArgs = @("discover", "tests")

    if ($Verbose) {
        $testArgs += @("-v")
    }

    $result = & python -m unittest $testArgs

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Все тесты пройдены успешно!"
    } else {
        Write-Error "Некоторые тесты провалились (код выхода: $LASTEXITCODE)"
        exit $LASTEXITCODE
    }

} catch {
    Write-Error "Ошибка при запуске тестов: $($_.Exception.Message)"
    exit 1
} finally {
    # Деактивация виртуального окружения
    if (Test-Path "$VenvPath\Scripts\deactivate.bat") {
        Write-Info "Деактивация виртуального окружения..."
        & "$VenvPath\Scripts\deactivate.bat"
    }
    Pop-Location
}

Write-Success "Тестирование завершено"



