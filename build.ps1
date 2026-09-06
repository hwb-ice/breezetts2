param([string]$VsInstall = '', [int]$Jobs = 8)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$upstreamCommit = 'a2a4d4f34c0960edf1bf78e392de1fbce5a855e6'
function Run-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed: $LASTEXITCODE" }
}
New-Item -ItemType Directory -Force downloads,logs,runtime,runtime-stream | Out-Null
if (-not (Test-Path 'runtime-source/.git')) {
    Run-Checked git @('clone','--depth','1','--branch','v0.7.2','https://github.com/0xShug0/audio.cpp.git','runtime-source')
}
if ((git -C runtime-source rev-parse HEAD) -ne $upstreamCommit) { throw 'Unexpected upstream revision; use the pinned v0.7.2 source.' }
$previousErrorPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
git -C runtime-source apply --reverse --check ../patches/audio-cpp-streaming.patch 2>$null
$patchApplied = $LASTEXITCODE -eq 0
$ErrorActionPreference = $previousErrorPreference
if (-not $patchApplied) {
    Run-Checked git @('-C','runtime-source','apply','--check','../patches/audio-cpp-streaming.patch')
    Run-Checked git @('-C','runtime-source','apply','../patches/audio-cpp-streaming.patch')
}
& ./runtime-source/scripts/build_windows.ps1 -Preset windows-cpu-release -ModelSet custom -Models breeze_tts -Target audiocpp_server -VsInstall $VsInstall -DynamicBackends -Jobs $Jobs
if ($LASTEXITCODE -ne 0) { throw 'Native build failed' }
foreach ($asset in @('bin','cudart')) {
    $name = "audio-v0.7.2-$asset-windows-x64-cuda12.4.zip"
    $archive = Join-Path 'downloads' $name
    if (-not (Test-Path $archive)) {
        Run-Checked curl.exe @('-L','--fail','--retry','3','-o',$archive,"https://github.com/0xShug0/audio.cpp/releases/download/v0.7.2/$name")
    }
    Expand-Archive -LiteralPath $archive -DestinationPath runtime -Force
}
Copy-Item runtime/*.dll runtime-stream -Force
Copy-Item runtime-source/build/windows-cpu-release/bin/*.dll runtime-stream -Force
Copy-Item runtime-source/build/windows-cpu-release/bin/audiocpp_server.exe runtime-stream -Force
Write-Host 'Build complete. Prepare the model using MODEL_SETUP.md, then run start.bat.'
