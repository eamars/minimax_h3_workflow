param(
    [string]$Destination = (Join-Path $env:USERPROFILE '.codex\skills')
)

$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\skills')).Path
$skillNames = @(
    'production-orchestrator', 'request-normalizer', 'reference-canon-manager',
    'plot-architect', 'scene-performance-writer', 'sound-dialogue-planner',
    'storyboard-director', 'animatic-previs-planner', 'production-preflight-reviewer',
    'minimax-h3-adapter', 'keyframe-handoff-builder', 'comfyui-workflow-compiler',
    'render-orchestrator', 'continuity-qc-supervisor', 'repair-director', 'post-editor'
)

New-Item -ItemType Directory -Path $Destination -Force | Out-Null
foreach ($name in $skillNames) {
    $source = Join-Path $sourceRoot $name
    if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))) {
        throw "Skill package is incomplete: $source"
    }
    $target = Join-Path $Destination $name
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Copy-Item -Path (Join-Path $source '*') -Destination $target -Recurse -Force
    Write-Output "Installed $name -> $target"
}

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sharedRoot = Join-Path $Destination 'production-orchestrator\references\shared'
New-Item -ItemType Directory -Path $sharedRoot -Force | Out-Null
Copy-Item -Path (Join-Path $repositoryRoot 'schemas') -Destination $sharedRoot -Recurse -Force
Copy-Item -Path (Join-Path $repositoryRoot 'workflow-catalog') -Destination $sharedRoot -Recurse -Force
Write-Output "Installed shared schemas and workflow catalog -> $sharedRoot"
