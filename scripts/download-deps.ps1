# download-deps.ps1 - Загрузка зависимостей Java и Solr
# Использование: .\download-deps.ps1 [-Force]

param(
    [switch]$Force,
    [string]$JavaUrl = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.12_7.zip",
    [string]$SolrUrl = "https://archive.apache.org/dist/solr/solr/9.4.1/solr-9.4.1.zip"
)

$ErrorActionPreference = "Stop"

# Импорт общих функций
Import-Module $PSScriptRoot\common.ps1

Write-Header "Загрузка зависимостей Nikita"

try {
    # Проверка предусловий
    Test-Prerequisites

    # Загрузка Java
    $javaPath = Download-Java -JavaUrl $JavaUrl
    if ($Force -and (Test-Path "$PSScriptRoot\..\java")) {
        Write-Info "Удаление старой версии Java..."
        Remove-Item "$PSScriptRoot\..\java" -Recurse -Force
        $javaPath = Download-Java -JavaUrl $JavaUrl
    }

    # Загрузка Solr
    $solrPath = Download-Solr -SolrUrl $SolrUrl
    if ($Force -and (Test-Path "$PSScriptRoot\..\solr")) {
        Write-Info "Удаление старой версии Solr..."
        Remove-Item "$PSScriptRoot\..\solr" -Recurse -Force
        $solrPath = Download-Solr -SolrUrl $SolrUrl
    }

    Write-Success "Все зависимости загружены успешно"
    Write-Info "Java: $javaPath"
    Write-Info "Solr: $solrPath"

} catch {
    Write-Error "Ошибка при загрузке зависимостей: $($_.Exception.Message)"
    exit 1
}

Write-Info "Для продолжения используйте: .\build.ps1"
