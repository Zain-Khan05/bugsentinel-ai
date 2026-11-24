$certificateDirectory = Join-Path $PSScriptRoot '..\nginx\certs'
New-Item -ItemType Directory -Force -Path $certificateDirectory | Out-Null
$cert = New-SelfSignedCertificate -DnsName 'localhost' -CertStoreLocation 'Cert:\CurrentUser\My' -NotAfter (Get-Date).AddYears(1)
$password = ConvertTo-SecureString -String 'local-dev-only' -Force -AsPlainText
$pfxPath = Join-Path $certificateDirectory 'localhost.pfx'
Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $password | Out-Null
Write-Host 'PFX created. Convert it to localhost.crt and localhost.key with OpenSSL:'
Write-Host "openssl pkcs12 -in $pfxPath -clcerts -nokeys -out (Join-Path `$certificateDirectory 'localhost.crt') -passin pass:local-dev-only"
Write-Host "openssl pkcs12 -in $pfxPath -nocerts -nodes -out (Join-Path `$certificateDirectory 'localhost.key') -passin pass:local-dev-only"
