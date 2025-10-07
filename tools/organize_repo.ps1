param(
  [switch]$DisableSparse
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Info($m){ Write-Host "[INFO]" $m -ForegroundColor Cyan }
function Ok($m){ Write-Host "[OK]" $m -ForegroundColor Green }
function Warn($m){ Write-Host "[WARN]" $m -ForegroundColor Yellow }

# 0) Valida git
try { git rev-parse --is-inside-work-tree *> $null } catch {
  throw "Este diretório não é um repositório git."
}
$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot
Info "Repo: $repoRoot"

# 1) Sparse-checkout
$sparse = ""
try { $sparse = (git config --get core.sparseCheckout).Trim() } catch {}
if ($DisableSparse) {
  if ($sparse -eq "true") {
    Info "Desativando sparse-checkout..."
    git sparse-checkout disable
    Ok "Sparse-checkout desativado."
  } else { Warn "Sparse-checkout já está desativado." }
} else {
  if ($sparse -ne "true") {
    Info "Inicializando sparse-checkout (cone)..."
    git sparse-checkout init --cone
  }
  Info "Adicionando pastas ao cone do sparse-checkout..."
  git sparse-checkout add scripts
  git sparse-checkout add examples
  git sparse-checkout add docs
  git sparse-checkout add notebooks
  git sparse-checkout add outputs
  Ok "Pastas adicionadas ao sparse-checkout."
}

# 2) Pastas básicas
foreach($p in @("tools","scripts","examples","docs")){
  New-Item -ItemType Directory -Path $p -Force | Out-Null
}
Ok "Pastas garantidas."

# 3) Utilitários
function IsTracked($path){
  & git ls-files --error-unmatch $path *> $null
  return $LASTEXITCODE -eq 0
}
function MoveSmart($src, $dst){
  if (-not (Test-Path $src)) { return }
  $dstDir = Split-Path $dst -Parent
  New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
  if (IsTracked $src) {
    Info "git mv $src -> $dst"
    git mv $src $dst
  } else {
    Info "Move-Item $src -> $dst"
    Move-Item -Force $src $dst
  }
}

# 4) Mover arquivos para a estrutura
MoveSmart "net_metrics.py" "scripts/net_metrics.py"
MoveSmart "example_usage.py" "examples/example_usage.py"
MoveSmart "README_net_metrics.md" "docs/README_net_metrics.md"

# 5) Atualiza .gitignore (append sem duplicar)
$ignPath = ".gitignore"
$want = @(
  ".venv/",
  "outputs/",
  "**/__pycache__/",
  ".ipynb_checkpoints/",
  ".env"
)
if (-not (Test-Path $ignPath)) { New-Item -ItemType File -Path $ignPath | Out-Null }
$curr = Get-Content $ignPath -Raw
$added = $false
foreach($line in $want){
  if ($curr -notmatch [regex]::Escape($line)){
    Add-Content $ignPath "`n$line"
    $added = $true
  }
}
if ($added){ Ok ".gitignore atualizado." } else { Info ".gitignore já estava ok." }

# 6) Commit
git add -A
$pending = (git status --porcelain)
if ($pending){
  Info "Efetuando commit..."
  git commit -m "chore(repo): organiza scripts/examples/docs e ajusta sparse-checkout"
  Ok "Commit criado."
} else {
  Info "Nada a commitar."
}

Ok "Organização concluída. Dica: execute novamente com -DisableSparse se quiser trabalhar sem sparse-checkout."
