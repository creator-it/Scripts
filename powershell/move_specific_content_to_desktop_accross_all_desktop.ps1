# Define the base Users path and create a folder on the current user's Desktop for PDF files
$usersPath = "C:\Users"
$pdfFolderPath = [System.IO.Path]::Combine([System.Environment]::GetFolderPath("Desktop"), "PDF_Files")

# Create the PDF_Files folder if it doesn't already exist
if (!(Test-Path -Path $pdfFolderPath)) {
    New-Item -Path $pdfFolderPath -ItemType Directory | Out-Null
}

# Loop through each user folder in the Users directory
Get-ChildItem -Path $usersPath | ForEach-Object {
    # Construct the Desktop path for each user
    $desktopPath = Join-Path -Path $_.FullName -ChildPath "Desktop"
    
    # Check if the Desktop path exists for the user
    if (Test-Path -Path $desktopPath) {
        # Get the username (folder name in Users path)
        $username = $_.Name
        
        # Get list of PDF files on the Desktop
        $pdfFiles = Get-ChildItem -Path $desktopPath -Filter *.pdf

        # Copy and rename each PDF file to the PDF_Files folder
        $pdfFiles | ForEach-Object {
            # Construct the new filename as username_pdforiginalname.pdf
            $newFileName = "${username}_$($_.Name)"
            $destinationPath = Join-Path -Path $pdfFolderPath -ChildPath $newFileName

            # Copy the file to the new folder with the new name
            Copy-Item -Path $_.FullName -Destination $destinationPath
        }
    }
}

Write-Output "All PDF files have been copied and renamed in the folder: $pdfFolderPath"
