Write-Output "WARNING: This will delete your GitHub Copilot cached data and sign you out."
$confirm = Read-Host "Are you sure you want to proceed? (yes/no)"

if ($confirm -eq "yes") {
    $globalStorage = "$env:APPDATA\Code\User\globalStorage"
    $folders = @("github.copilot", "github.copilot-chat")

    foreach ($folder in $folders) {
        $path = Join-Path $globalStorage $folder
        if (Test-Path $path) {
            try {
                Remove-Item -Recurse -Force $path
                Write-Output "Deleted folder: $path"
            } catch {
                Write-Output "Failed to delete $path. Error: $_"
            }
        } else {
            Write-Output "Folder not found: $path"
        }
    }
    Write-Output "Done. Please restart VS Code and sign in to GitHub Copilot again."
} else {
    Write-Output "Operation cancelled. No changes were made."
}

# Optional: wait for user input before closing terminal
# Read-Host -Prompt "Press Enter to exit"
