[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.fitmanagerstudio\.com$")]
    [string]$Hostname,

    [string]$PublicUrlFile = ""
)

$ErrorActionPreference = "Stop"
$timeout = [TimeSpan]::FromSeconds(12)

function Get-HttpStatus {
    param([Parameter(Mandatory = $true)][Uri]$Uri)

    $handler = [System.Net.Http.HttpClientHandler]::new()
    $handler.AllowAutoRedirect = $false
    $client = [System.Net.Http.HttpClient]::new($handler)
    $client.Timeout = $timeout
    $null = $client.DefaultRequestHeaders.TryAddWithoutValidation(
        "User-Agent",
        "FitManager-R015-Probe/1.0"
    )
    try {
        $response = $client.GetAsync($Uri).GetAwaiter().GetResult()
        return [int]$response.StatusCode
    }
    finally {
        $client.Dispose()
        $handler.Dispose()
    }
}

function Get-StrictTlsEvidence {
    param([Parameter(Mandatory = $true)][string]$TargetHost)

    $tcpClient = [System.Net.Sockets.TcpClient]::new()
    try {
        $connectTask = $tcpClient.ConnectAsync($TargetHost, 443)
        if (-not $connectTask.Wait($timeout)) {
            throw "Timeout TCP 443"
        }
        $sslStream = [System.Net.Security.SslStream]::new($tcpClient.GetStream(), $false)
        try {
            # Nessuna callback custom: chain e hostname sono verificati dallo store di sistema.
            $sslStream.AuthenticateAsClient($TargetHost)
            $certificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(
                $sslStream.RemoteCertificate
            )
            return [pscustomobject]@{
                Issuer = $certificate.Issuer
                NotAfter = $certificate.NotAfter.ToUniversalTime().ToString("o")
            }
        }
        finally {
            $sslStream.Dispose()
        }
    }
    finally {
        $tcpClient.Dispose()
    }
}

$nonce = [guid]::NewGuid().ToString("N")
$httpStatus = Get-HttpStatus -Uri ([Uri]"http://$Hostname/fitmanager-r015-$nonce")
if ($httpStatus -ne 404) {
    throw "HTTP non-challenge deve essere 404; ricevuto $httpStatus"
}
Write-Output "HTTP_NON_CHALLENGE=404"

$tlsEvidence = Get-StrictTlsEvidence -TargetHost $Hostname
Write-Output "TLS_STRICT=PASS"
Write-Output "TLS_ISSUER=$($tlsEvidence.Issuer)"
Write-Output "TLS_NOT_AFTER=$($tlsEvidence.NotAfter)"

$privateStatus = Get-HttpStatus -Uri ([Uri]"https://$Hostname/api/clients")
if ($privateStatus -ne 404) {
    throw "Route privata pubblica deve essere 404; ricevuto $privateStatus"
}
Write-Output "HTTPS_PRIVATE=404"

if ([string]::IsNullOrWhiteSpace($PublicUrlFile)) {
    Write-Output "HTTPS_PUBLIC_200=SKIPPED (fornire -PublicUrlFile per il closeout)"
    exit 0
}

$resolvedPublicUrlFile = Resolve-Path -LiteralPath $PublicUrlFile
$publicUrl = (Get-Content -LiteralPath $resolvedPublicUrlFile -Raw).Trim()
$publicUri = [Uri]$publicUrl
if ($publicUri.Scheme -ne "https" -or $publicUri.Host -ne $Hostname) {
    throw "Il link pubblico deve usare HTTPS e lo stesso hostname del probe"
}
if (-not $publicUri.AbsolutePath.StartsWith("/public/", [System.StringComparison]::Ordinal)) {
    throw "Il link di closeout deve appartenere a /public/"
}

$publicStatus = Get-HttpStatus -Uri $publicUri
if ($publicStatus -ne 200) {
    throw "Route pubblica attesa 200; ricevuto $publicStatus"
}
Write-Output "HTTPS_PUBLIC_200=PASS"
Write-Output "R0.1.5_STRICT_PROBE=PASS"
