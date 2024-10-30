# Define the base Users path
$usersPath = "C:\Users"

# Create a hash set to store unique file extensions
$uniqueExtensions = @{}

# Loop through each user folder in the Users directory
Get-ChildItem -Path $usersPath | ForEach-Object {
    # Construct the Desktop path for each user
    $desktopPath = Join-Path -Path $_.FullName -ChildPath "Desktop"
    
    # Check if the Desktop path exists for the user
    if (Test-Path -Path $desktopPath) {
        # Get all files on the Desktop and check each file's extension
        Get-ChildItem -Path $desktopPath -File | ForEach-Object {
            $extension = $_.Extension.ToLower() # Convert to lowercase for consistency
            # Add the extension to the hash set if it's not already there
            if (-not $uniqueExtensions.ContainsKey($extension)) {
                $uniqueExtensions[$extension] = 1
            }
        }
    }
}

# Display the unique file extensions found
Write-Output "Unique file extensions across all users' desktops:"
$uniqueExtensions.Keys | ForEach-Object { Write-Output $_ }

Write-Output "Total unique file types: $($uniqueExtensions.Count)"
