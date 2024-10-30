# Define the base Users path and create a folder on the current user's Desktop for specific files
$usersPath = "C:\Users"
$targetFolderPath = [System.IO.Path]::Combine([System.Environment]::GetFolderPath("Desktop"), "Specified_Files")

# Create the Specified_Files folder if it doesn't already exist
if (!(Test-Path -Path $targetFolderPath)) {
    New-Item -Path $targetFolderPath -ItemType Directory | Out-Null
}

# Define the list of file extensions to copy
$targetExtensions = @(".reg", ".msc", ".pdf", ".oxps", ".pfx", ".xml")

# Initialize a hash set to track unique file extensions found
$uniqueExtensions = @{}

# Loop through each user folder in the Users directory
Get-ChildItem -Path $usersPath | ForEach-Object {
    # Construct the Desktop path for each user
    $desktopPath = Join-Path -Path $_.FullName -ChildPath "Desktop"
    
    # Check if the Desktop path exists for the user
    if (Test-Path -Path $desktopPath) {
        # Get the username (folder name in Users path)
        $username = $_.Name
        
        # Get all files on the Desktop
        Get-ChildItem -Path $desktopPath -File | ForEach-Object {
            $extension = $_.Extension.ToLower() # Convert to lowercase for consistency
            
            # Track unique extensions
            if (-not $uniqueExtensions.ContainsKey($extension)) {
                $uniqueExtensions[$extension] = 1
            }

            # Copy files with specified extensions to the target folder
            if ($targetExtensions -contains $extension) {
                $newFileName = "${username}_$($_.Name)"
                $destinationPath = Join-Path -Path $targetFolderPath -ChildPath $newFileName
                Copy-Item -Path $_.FullName -Destination $destinationPath
            }
        }
    }
}

# Display the unique file extensions found across all users' desktops
Write-Output "Unique file extensions across all users' desktops:"
$uniqueExtensions.Keys | ForEach-Object { Write-Output $_ }

Write-Output "Total unique file types: $($uniqueExtensions.Count)"
Write-Output "Specified files have been copied and renamed in the folder: $targetFolderPath"
