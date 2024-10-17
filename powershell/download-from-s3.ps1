[CmdletBinding()]
param (
    [Parameter(Mandatory=$true)]
    [string]$backend
)

$fullbkp = "full-backup-0.0"
$diffbkp = "diff-backup-0.0"
$fullbkp_path = "C:\Users\$env:USERNAME\Downloads\sev1backup\fullbkp"
$diffbkp_path = "C:\Users\$env:USERNAME\Downloads\sev1backup\diffbkp"

if (!(Test-Path $fullbkp_path)) {
    New-Item -ItemType Directory -Path $fullbkp_path
}

if (!(Test-Path $diffbkp_path)) {
    New-Item -ItemType Directory -Path $diffbkp_path
}

$x = @(aws s3 ls $fullbkp)
$y = @(aws s3 ls $diffbkp)

# Initialize variables to store the latest folder information
$latestFolder = $null
$latestDate = [datetime]::MinValue

# this will only work if folder name in this pattern 'yyyymmdd'
foreach ($folder in $x) {
    # Extract the date string from the folder name and trim any leading or trailing whitespace
    $dateString = $folder -replace "PRE ", "" -replace "/", "" | ForEach-Object { $_.Trim() }
    # Check if the date string matches the yyyymmdd pattern
    if ($dateString -match '^\d{8}$') {
        try {
            # Parse the date string as a date
            $folderDate = [datetime]::ParseExact($dateString, 'yyyyMMdd', $null)
            # Check if this folder is the latest one
            if ($folderDate -gt $latestDate) {
                $latestDate = $folderDate
                $latestFolder = $folder
            }
        } catch {
            Write-Warning "Failed to parse date: $dateString"
        }
    } else {
        Write-Warning "Invalid date format: $dateString"
    }
}

# Output the last uploaded folder
if ($latestFolder) {
    $cleanedLatestFolder = $latestFolder -replace "PRE ", "" -replace "/", "" | ForEach-Object { $_.Trim() }
    #aws s3 ls "s3://$fullbkp/$cleanedLatestFolder/$backend/"
    aws s3 cp "s3://$fullbkp/$cleanedLatestFolder/$backend/" $fullbkp_path --recursive

} else {
    Write-Output "No valid folders found."
}

# Now this proccess for diff backup
foreach ($folder in $y) {
    # Extract the date string from the folder name and trim any leading or trailing whitespace
    $dateString = $folder -replace "PRE ", "" -replace "/", "" | ForEach-Object { $_.Trim() }

    # Check if the date string matches the yyyymmdd pattern
    if ($dateString -match '^\d{8}$') {
        try {
            # Parse the date string as a date
            $folderDate = [datetime]::ParseExact($dateString, 'yyyyMMdd', $null)

            # Check if this folder is the latest one
            if ($folderDate -gt $latestDate) {
                $latestDate = $folderDate
                $latestFolder = $folder
            }
        } catch {
            Write-Warning "Failed to parse date: $dateString"
        }
    } else {
        Write-Warning "Invalid date format: $dateString"
    }
}

# Output the last uploaded folder
if ($latestFolder) {
    $cleanedLatestFolder = $latestFolder -replace "PRE ", "" -replace "/", "" | ForEach-Object { $_.Trim() }
    #aws s3 cp "s3://$diffbkp/$cleanedLatestFolder/$backend/" $diffbkp_path --recursive
} else {
    Write-Output "No valid folders found."
}
