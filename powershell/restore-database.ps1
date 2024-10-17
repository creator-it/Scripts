$server = "localhost\@$!2017"
$username = "sa"
$password = ""
$connectionString = "Server=$server;User Id=$username;Password=$password;Database=master;TrustServerCertificate=True"

$fullbkp_path = "C:\Users\$env:USERNAME\Downloads\sev1backup\fullbkp"
$destination = "C:\Users\$env:USERNAME\Downloads\sev1backup\fullbkp\temp"

$zipFiles = Get-ChildItem -Path $fullbkp_path -Filter *.zip | Where-Object { $_.Name -like '*uniq_identity_from_file_name*' }
$startTime = Get-Date
try {
    Remove-Item -Path $destination -Recurse -Force
    foreach ($zipFile in $zipFiles) {
        
        if (Test-Path $destination) {
            Remove-Item -Path $destination -Recurse -Force
        }
        #getting client id from file name
        $client_id = ($zipFile -split '_')[1]

        Expand-Archive -Path $($zipFile.FullName) -DestinationPath $destination

        $extractedFiles = Get-ChildItem -Path $destination -Recurse | ForEach-Object { Get-ChildItem -Path $_.FullName -Recurse -File }
        Write-Output $client_id

        if ($extractedFiles[0] -match "@$!ff") {
            $ff = @"
DECLARE @dbName NVARCHAR(128) = N'@$!ff_$600{client_id}';
DECLARE @logicalNameData NVARCHAR(128);
DECLARE @logicalNameLog NVARCHAR(128);
DECLARE @sql NVARCHAR(MAX);

SET @logicalNameData = N'@$!ff_$600';
SET @logicalNameLog = N'@$!ff_$600_log';

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'@$!ff_$600_${client_id}')
BEGIN
     SET @sql = N'CREATE DATABASE ' + QUOTENAME(@dbName);
     EXEC sp_executesql @sql;
END
ELSE
BEGIN
    -- Get the logical file names for the existing database
    SELECT 
        @logicalNameData = name 
    FROM 
        sys.master_files 
    WHERE 
        type_desc = 'ROWS' 
        AND database_id = DB_ID(@dbName);

    SELECT 
        @logicalNameLog = name 
    FROM 
        sys.master_files 
    WHERE 
        type_desc = 'LOG' 
        AND database_id = DB_ID(@dbName);
END

RESTORE DATABASE [@$!ff_$600_$client_id]
FROM DISK = '$($extractedFiles[0])'
WITH REPLACE,
MOVE @logicalNameData TO 'C:\Program Files\Microsoft SQL Server\MSSQL14.ASI2017\MSSQL\DATA\@$!ff_$600_${client_id}.mdf',
MOVE @logicalNameLog TO 'C:\Program Files\Microsoft SQL Server\MSSQL14.ASI2017\MSSQL\DATA\@$!ff_$600_${client_id}_log.ldf';
"@

            Invoke-SqlCmd -ConnectionString $connectionString -Query $ff -QueryTimeout 180
        }

        if ($extractedFiles[1] -match "@$!pp") {
            $pp = @"
DECLARE @dbName NVARCHAR(128) = N'@$!pp_${client_id}';
DECLARE @logicalNameData NVARCHAR(128);
DECLARE @logicalNameLog NVARCHAR(128);
DECLARE @sql NVARCHAR(MAX);

SET @logicalNameData = N'@$!pp';
SET @logicalNameLog = N'@$!pp_log';

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = @dbName)
BEGIN
    SET @sql = N'CREATE DATABASE ' + QUOTENAME(@dbName);
    EXEC sp_executesql @sql;
END
ELSE
BEGIN
    -- Get the logical file names for the existing database
    SELECT 
        @logicalNameData = name 
    FROM 
        sys.master_files 
    WHERE 
        type_desc = 'ROWS' 
        AND database_id = DB_ID(@dbName);

    SELECT 
        @logicalNameLog = name 
    FROM 
        sys.master_files 
    WHERE 
        type_desc = 'LOG' 
        AND database_id = DB_ID(@dbName);
END

-- Restore the database using the correct logical file names
RESTORE DATABASE [@$!pp_$client_id]
FROM DISK = '$($extractedFiles[1])'
WITH REPLACE,
MOVE @logicalNameData TO 'C:\Program Files\Microsoft SQL Server\MSSQL14.ASI2017\MSSQL\DATA\@$!pp_${client_id}.mdf',
MOVE @logicalNameLog TO 'C:\Program Files\Microsoft SQL Server\MSSQL14.ASI2017\MSSQL\DATA\@$!pp_${client_id}_log.ldf';
"@

            Invoke-SqlCmd -ConnectionString $connectionString -Query $pg -QueryTimeout 180
        }
        Remove-Item -Path $destination -Recurse -Force
    }
} catch {
    Write-Output "Error : $_"
}
$end_Time = Get-Date

$executionTime = $end_Time - $startTime

Write-Output $executionTime
