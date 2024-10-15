Add-Type -AssemblyName System.IO.Compression.FileSystem

$server = "localhost\@$!2017"
$username = "sa"
$password = ""
$connectionString = "Server=$server;User Id=$username;Password=$password;Database=master;TrustServerCertificate=True"
$db_id = 11111
$get_version = @"

USE [DB_$db_id]
DECLARE @return_value int,
        @versionNo nvarchar(10)
EXEC @return_value = [dbo].[DatabaseVersion]
    @versionNo = @versionNo OUTPUT
SELECT @versionNo as N'@versionNo'
SELECT 'Return Value' = @return_value
"@

if (Test-Path "C:\single\temp") {
    Remove-Item -Path "C:\single\temp" -Recurse -Force
}

# Define backup directory

if (!(Test-Path "C:\single\temp\bak")) {
    New-Item -ItemType Directory -Path "C:\single\temp\bak"
}
$bak = "C:\single\temp\bak"
$zip = "C:\single\temp"


$get_version = Invoke-SqlCmd -ConnectionString $connectionString -Query $get_version
$versionNo = $get_version[0].'@versionNo'

$versionNo = $versionNo -replace '\.', '-'
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$ffbackupFile = "$bak\db_name_$db_id" + "_" + $versionNo + "_" +$timestamp + ".bak"
$ppbackupFile = "$bak\db_name_" + "$db_id" + "_" + "$versionNo" + "_" + $timestamp + ".bak"

$ff = "BACKUP DATABASE [DB_$db_id] TO DISK='$ffbackupFile'"
$pp = "BACKUP DATABASE [DB_$db_id] TO DISK='$ppbackupFile'"

if (!(Test-Path $bak)) {
        New-Item -ItemType Directory -Path $bak
}

Invoke-SqlCmd -ConnectionString $connectionString -Query $fd -ErrorAction Stop -QueryTimeout 1000
Invoke-SqlCmd -ConnectionString $connectionString -Query $pg -ErrorAction Stop -QueryTimeout 1000

[System.IO.Compression.ZipFile]::CreateFromDirectory("$bak", "$zip\DB_$db_id" + "_" + $versionNo + "_" +$timestamp + ".zip")

$bkups = "$zip\DB_$db_id" + "_" + $versionNo + "_" +$timestamp + ".zip"
