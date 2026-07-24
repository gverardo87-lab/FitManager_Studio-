[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$legoVersion = "5.2.1"
$archiveSha256 = "3e87c133bcb0a6fd4236d11e0583967ecd2f04f454d2ff48286f1ab1183d699e"
$executableSha256 = "e2d5f33c26032197db5953f8cfd93aa960f08cf2014c887b79ba950cb5b525e5"
$licenseSha256 = "bf12923e71046c564f4163c00c3aa6b3581b51858f099a035f5baf2216addf6e"
$archiveName = "lego_v${legoVersion}_windows_amd64.zip"
$downloadUrl = "https://github.com/go-acme/lego/releases/download/v${legoVersion}/${archiveName}"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../.."))
$destinationDir = Join-Path $repoRoot "tools/bin"
$destinationPath = Join-Path $destinationDir "lego.exe"
$trackedLicensePath = Join-Path $repoRoot "tools/licenses/lego-MIT.txt"

$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$scratchDir = [System.IO.Path]::GetFullPath(
    (Join-Path $tempRoot ("fitmanager-lego-" + [guid]::NewGuid().ToString("N")))
)
if (-not $scratchDir.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Scratch directory non confinata nel temp root: $scratchDir"
}

try {
    New-Item -ItemType Directory -Path $scratchDir | Out-Null
    $archivePath = Join-Path $scratchDir $archiveName
    $extractDir = Join-Path $scratchDir "extracted"

    Write-Host "Download lego v$legoVersion da release immutabile..."
    Invoke-WebRequest -Uri $downloadUrl -OutFile $archivePath -MaximumRedirection 5

    $actualArchiveSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $archivePath).Hash.ToLowerInvariant()
    if ($actualArchiveSha256 -ne $archiveSha256) {
        throw "Archive SHA-256 mismatch. Atteso $archiveSha256, trovato $actualArchiveSha256"
    }

    Expand-Archive -LiteralPath $archivePath -DestinationPath $extractDir
    $executablePath = Join-Path $extractDir "lego.exe"
    $archiveLicensePath = Join-Path $extractDir "LICENSE"

    $actualExecutableSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $executablePath).Hash.ToLowerInvariant()
    if ($actualExecutableSha256 -ne $executableSha256) {
        throw "lego.exe SHA-256 mismatch. Atteso $executableSha256, trovato $actualExecutableSha256"
    }

    $actualArchiveLicenseSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $archiveLicensePath).Hash.ToLowerInvariant()
    if ($actualArchiveLicenseSha256 -ne $licenseSha256) {
        throw "LICENSE SHA-256 mismatch. Atteso $licenseSha256, trovato $actualArchiveLicenseSha256"
    }
    $actualTrackedLicenseSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $trackedLicensePath).Hash.ToLowerInvariant()
    if ($actualTrackedLicenseSha256 -ne $licenseSha256) {
        throw "Licenza tracked SHA-256 mismatch. Atteso $licenseSha256, trovato $actualTrackedLicenseSha256"
    }

    $versionOutput = (& $executablePath --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $versionOutput -ne "lego version $legoVersion windows/amd64") {
        throw "Versione/target lego inattesi: $versionOutput"
    }

    New-Item -ItemType Directory -Force -Path $destinationDir | Out-Null
    Copy-Item -LiteralPath $executablePath -Destination $destinationPath -Force
    $stagedSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $destinationPath).Hash.ToLowerInvariant()
    if ($stagedSha256 -ne $executableSha256) {
        throw "lego.exe corrotto durante la copia in tools/bin"
    }

    Write-Host "lego.exe v$legoVersion installato in tools/bin (SHA-256 $stagedSha256)"
}
finally {
    if (Test-Path -LiteralPath $scratchDir) {
        $resolvedScratch = [System.IO.Path]::GetFullPath($scratchDir)
        if (-not $resolvedScratch.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Cleanup rifiutato fuori dal temp root: $resolvedScratch"
        }
        Remove-Item -LiteralPath $resolvedScratch -Recurse -Force
    }
}
