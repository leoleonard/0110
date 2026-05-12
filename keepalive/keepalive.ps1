param(
    [int]$IntervalSeconds = 60,
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms

Add-Type -Namespace KeepAlive -Name Power -MemberDefinition @"
    [System.Runtime.InteropServices.DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint esFlags);
"@

$ES_CONTINUOUS       = [uint32]"0x80000000"
$ES_SYSTEM_REQUIRED  = [uint32]"0x00000001"
$ES_DISPLAY_REQUIRED = [uint32]"0x00000002"
$KEEP_AWAKE_FLAGS    = $ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED -bor $ES_DISPLAY_REQUIRED

function Write-Tick($msg) {
    if (-not $Quiet) {
        $ts = (Get-Date).ToString('HH:mm:ss')
        Write-Host "[$ts] $msg"
    }
}

try {
    [void][KeepAlive.Power]::SetThreadExecutionState($KEEP_AWAKE_FLAGS)
    Write-Tick "sleep prevention armed (interval=${IntervalSeconds}s)"

    while ($true) {
        [void][KeepAlive.Power]::SetThreadExecutionState($KEEP_AWAKE_FLAGS)

        $pos = [System.Windows.Forms.Cursor]::Position
        [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point(($pos.X + 1), $pos.Y)
        Start-Sleep -Milliseconds 50
        [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($pos.X, $pos.Y)

        Write-Tick "jiggled"
        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally {
    [void][KeepAlive.Power]::SetThreadExecutionState($ES_CONTINUOUS)
    Write-Tick "sleep prevention released"
}
