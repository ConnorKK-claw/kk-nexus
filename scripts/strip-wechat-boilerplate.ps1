<#
.SYNOPSIS
    微信公众号文章后处理：剥离模板 + 修复tags编码
.DESCRIPTION
    1. 用 [System.IO.File]::ReadAllText() UTF8 安全读取（避免 GBK 隐式转码）
    2. 剥离尾部模板（分析师承诺/免责声明/投资者适当性说明/继续滑动看下一个）
    3. 同步 author → tags：分割"、"，补全所有作者为独立tag
    4. 标准化 tags 格式：[公众号, 川阅全球宏观, 作者1, 作者2, ...]
    5. 输出 UTF-8 without BOM
.PARAMETER FilePath
    目标 .md 文件路径（支持通配符）
.PARAMETER DryRun
    仅预览变更，不写入
.EXAMPLE
    .\scripts\strip-wechat-boilerplate.ps1 -FilePath "vault/raw/user/xxx.md"
    Get-ChildItem vault/raw/user/*.md | ForEach-Object { .\scripts\strip-wechat-boilerplate.ps1 -FilePath $_.FullName }
#>

param(
    [Parameter(Mandatory, ValueFromPipeline)]
    [string]$FilePath,
    [switch]$DryRun
)

begin {
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    $changedCount = 0
    $tagFixCount = 0
    $stripCount = 0
}

process {
    $resolvedPath = Resolve-Path $FilePath -ErrorAction SilentlyContinue
    if (-not $resolvedPath) { Write-Warning "文件不存在: $FilePath"; return }
    
    # 1. 安全读取（关键：不能用 Get-Content，会被 GBK 隐式转码）
    $bytes = [System.IO.File]::ReadAllBytes($resolvedPath)
    $bytesLen = $bytes.Length
    
    # 检查 BOM，如果文件以 UTF-8 BOM (EF BB BF) 开头则跳过
    $bomOffset = 0
    if ($bytesLen -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        $bomOffset = 3
    }
    
    $content = [System.Text.Encoding]::UTF8.GetString($bytes, $bomOffset, $bytesLen - $bomOffset)
    $original = $content
    $modified = $false
    
    # 2. 提取 YAML frontmatter
    $fmMatch = [regex]::Match($content, '(?s)^---\s*\n(.*?)\n---\s*\n')
    if (-not $fmMatch.Success) {
        Write-Warning "未找到 YAML frontmatter: $resolvedPath"
        return
    }
    
    $frontmatter = $fmMatch.Groups[1].Value
    $bodyStart = $fmMatch.Index + $fmMatch.Length
    $body = $content.Substring($bodyStart)
    
    # 3. 剥离尾部模板
    $boilerplateMarkers = @(
        '**分析师承诺',
        '**免责声明',
        '**投资者适当性说明',
        '继续滑动看下一个'
    )
    $stripped = $false
    foreach ($marker in $boilerplateMarkers) {
        $idx = $body.IndexOf($marker, [System.StringComparison]::Ordinal)
        if ($idx -ge 0) {
            $body = $body.Substring(0, $idx).TrimEnd()
            $stripped = $true
            break
        }
    }
    
    # 4. 修复 tags
    $tagsLineMatch = [regex]::Match($frontmatter, '(?m)^tags:\s*\[([^\]]*)\]')
    $authorMatch = [regex]::Match($frontmatter, '(?m)^author:\s*"([^"]+)"')
    if (-not $authorMatch.Success) {
        $authorMatch = [regex]::Match($frontmatter, '(?m)^author:\s*([^\s].*)')
    }
    
    if ($authorMatch.Success) {
        $authorStr = $authorMatch.Groups[1].Value.Trim()
        # 分割多作者（支持 "、" 和 "、" 两种分隔符）
        $authors = $authorStr -split '[、]' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' -and $_ -notmatch '^团队$' }
        
        # 当前 tags
        $currentTagsStr = if ($tagsLineMatch.Success) { $tagsLineMatch.Groups[1].Value } else { '' }
        $currentTags = $currentTagsStr -split ',' | ForEach-Object { $_.Trim().Trim('"'' ') } | Where-Object { $_ -ne '' }
        
        # 构建新 tags（保持 '公众号', '川阅全球宏观' + 所有作者）
        $newTags = @()
        # 如果已有 公众号/川阅全球宏观 则保留
        if ($currentTags -contains '公众号' -or $currentTags -contains '"公众号"') {
            $newTags += '公众号'
        }
        if ($currentTags -match '川阅全球宏观') {
            $newTags += '川阅全球宏观'
        }
        # 追加所有作者（去重）
        foreach ($a in $authors) {
            if ($newTags -notcontains $a -and $a -ne '') {
                $newTags += $a
            }
        }
        # 如果没有任何自定义tag，至少保证有公众号
        if ($newTags.Count -eq 0) {
            $newTags = @('公众号', '川阅全球宏观')
        }
        
        # 检查 tags 是否已经正确
        $expectedTagsStr = ($newTags | ForEach-Object { $_ }) -join ', '
        
        if (-not $tagsLineMatch.Success -or $currentTagsStr -ne $expectedTagsStr) {
            if ($tagsLineMatch.Success) {
                $oldTagsLine = $tagsLineMatch.Groups[0].Value
                $newTagsLine = "tags: [$expectedTagsStr]"
                $frontmatter = $frontmatter.Replace($oldTagsLine, $newTagsLine)
            } else {
                # 没有 tags 行，追加
                $frontmatter += "`ntags: [$expectedTagsStr]"
            }
            $tagFixCount++
            $modified = $true
        }
    }
    
    # 5. 重组内容
    $newContent = "---`n$frontmatter`n---`n$body"
    if ($body -ne '') {
        $newContent = $newContent.TrimEnd() + "`n"
    }
    
    # 6. 如果修改了，写入
    if ($modified -or $stripped) {
        $newBytes = $utf8NoBom.GetBytes($newContent)
        
        if ($DryRun) {
            $fileName = Split-Path $resolvedPath -Leaf
            if ($stripped) { Write-Host "[DRY-RUN] $fileName → 剥离模板" }
            if ($modified) { Write-Host "[DRY-RUN] $fileName → 修复tags" }
        } else {
            [System.IO.File]::WriteAllBytes($resolvedPath, $newBytes)
            $changedCount++
            if ($stripped) { $stripCount++ }
        }
    }
}

end {
    if (-not $DryRun) {
        Write-Host "完成：处理 $changedCount 个文件（剥离模板 $stripCount / 修复tags $tagFixCount）"
    }
}
