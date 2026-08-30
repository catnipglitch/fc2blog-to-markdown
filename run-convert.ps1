#Requires -Version 5.1
<#
  FC2 ブログのエクスポートファイルを Markdown へ一括変換するスクリプト
  uv のインストールと Python 環境の準備も自動で行います。

  使い方: .\run-convert.ps1 [-InputFile <パス>] [-OutputDir <パス>] [-Category <名前> ...] [-DownloadImages]
  引数をすべて省略すると、ファイル選択ダイアログと質問による対話モードで動きます。

  実行ポリシーでブロックされる場合は、PowerShell を開いて次の 1 行で起動してください。
    powershell -NoProfile -ExecutionPolicy Bypass -File .\run-convert.ps1
#>
param(
    [string]$InputFile,
    [string]$OutputDir,
    [string[]]$Category,
    [switch]$DownloadImages
)

$ErrorActionPreference = 'Stop'
# Ensure Japanese text renders correctly on Windows PowerShell 5.1
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

Write-Host "FC2 ブログのエクスポートファイルを Markdown へ変換します"
Write-Host ""

$interactive = -not $PSBoundParameters.ContainsKey('InputFile')

try {
    # Resolve the input path before changing directory, so relative paths keep working
    if ($InputFile) {
        if (-not (Test-Path $InputFile)) {
            throw "入力ファイルが見つかりません: $InputFile"
        }
        $InputFile = (Resolve-Path $InputFile).Path
    }
    Set-Location $PSScriptRoot

    if (-not $InputFile) {
        Write-Host "変換するエクスポートファイルを選択してください（ファイル選択画面が開きます）"
        Add-Type -AssemblyName System.Windows.Forms
        $dialog = New-Object System.Windows.Forms.OpenFileDialog
        $dialog.Title = "FC2 エクスポートファイルを選択"
        $dialog.Filter = "テキストファイル (*.txt)|*.txt|すべてのファイル (*.*)|*.*"
        if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
            Write-Host "キャンセルされました。何も変換せずに終了します。"
            $null = Read-Host "終了するには Enter キーを押してください"
            exit 0
        }
        $InputFile = $dialog.FileName
    }
    Write-Host "入力ファイル: $InputFile"
    Write-Host ""

    # --- uv setup ---
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        Write-Host "変換に必要なツール uv が見つかりません。"
        if ($interactive) {
            $answer = Read-Host "uv をインストールしますか？ [Y/n]"
            if ($answer -match '^[nN]') {
                Write-Host "インストールを中止しました。"
                $null = Read-Host "終了するには Enter キーを押してください"
                exit 0
            }
        }
        Write-Host "uv をインストールしています..."
        # Official installer (https://docs.astral.sh/uv/); installs into %USERPROFILE%\.local\bin
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
        $uv = Get-Command uv -ErrorAction SilentlyContinue
        if (-not $uv) {
            throw "uv のインストールに失敗しました。https://docs.astral.sh/uv/ の手順でインストールしてから再実行してください。"
        }
        Write-Host "uv をインストールしました。"
    }

    Write-Host "Python 環境を準備しています（初回は数分かかることがあります）..."
    uv sync
    if ($LASTEXITCODE -ne 0) {
        throw "Python 環境の準備に失敗しました（uv sync）。インターネット接続を確認して再実行してください。"
    }
    Write-Host ""

    # --- interactive questions ---
    if ($interactive) {
        Write-Host "このファイルに含まれるカテゴリ一覧（記事数  カテゴリ名）:"
        uv run fc2md categories $InputFile
        if ($LASTEXITCODE -ne 0) {
            throw "エクスポートファイルを読み込めませんでした。FC2 からエクスポートしたテキストファイルか確認してください。"
        }
        Write-Host ""
        $answer = Read-Host "変換するカテゴリ名をカンマ区切りで入力してください（Enter だけなら全記事）"
        if ($answer.Trim()) {
            $Category = @($answer.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
        }

        $answer = Read-Host "出力先フォルダを入力してください（Enter だけなら output）"
        if ($answer.Trim()) {
            $OutputDir = $answer.Trim()
        }

        Write-Host ""
        Write-Host "※ 画像はブログを閉鎖すると取得できなくなります。閉鎖前に必ずダウンロードしてください。"
        $answer = Read-Host "記事内の画像もダウンロードしますか？ [Y/n]"
        if ($answer -notmatch '^[nN]') {
            $DownloadImages = $true
        }
    }
    if (-not $OutputDir) {
        $OutputDir = "output"
    }

    # --- run conversion ---
    Write-Host ""
    Write-Host "変換を開始します..."
    $uvArgs = @('run', 'fc2md', 'convert', $InputFile, '-o', $OutputDir)
    foreach ($name in $Category) {
        $uvArgs += @('--category', $name)
    }
    if ($DownloadImages) {
        $uvArgs += '--download-images'
    }
    & uv @uvArgs
    if ($LASTEXITCODE -ne 0) {
        throw "変換に失敗しました。上に表示されたメッセージを確認してください。"
    }

    Write-Host ""
    Write-Host "変換が完了しました。出力先: $((Resolve-Path $OutputDir).Path)"
    if ($interactive) {
        Start-Process explorer.exe (Resolve-Path $OutputDir).Path
        # Keep the console open when the script was launched from Explorer
        $null = Read-Host "終了するには Enter キーを押してください"
    }
    exit 0
}
catch {
    Write-Host ""
    Write-Host "エラーが発生しました:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($interactive) {
        $null = Read-Host "終了するには Enter キーを押してください"
    }
    exit 1
}
