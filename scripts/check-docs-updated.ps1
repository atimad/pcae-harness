$ErrorActionPreference = "Stop"

$RequiredFiles = @(
    "AGENTS.md",
    "PROJECT_STATUS.md",
    "CHANGELOG.md",
    "tasks/TODO.md",
    "tasks/DONE.md",
    "tasks/DECISIONS.md"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -Path $File -PathType Leaf)) {
        Write-Error "Missing required PCAE file: $File"
        exit 1
    }
}
