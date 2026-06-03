# Errors

Command failures and integration errors.

---
## [cninfo] 公告列表API返回0结果

- 尝试的API: cninfo.com.cn/new/hisAnnouncement/query (POST)
- 问题: stock参数格式不明确，多次尝试均返回total:0
- 解决方法: 改用 fulltextSearch/full 接口，通过searchkey参数搜索关键词成功获取数据
- 备选: PDF通过 https://static.cninfo.com.cn/{adjunctUrl} 下载

---


## [2026-05-23] engineering-practices vault 构建 — 反复出现的执行错误

### 1. PowerShell 字符串转义冲突（发生 5+ 次）
- **现象**: Python inline 命令 (`python -c "..."`) 与 PowerShell 引用规则冲突
  - 反斜杠路径被 PowerShell 解释：`Path(r"C:\...")` 报语法错误
  - `@"..."@` here-string 与 Python 三重引号嵌套时，YAML 中的 `"` 关闭了 PowerShell 终止符
  - 长文本在 PowerShell 管道中截断或部分丢失
- **典型报错**:
  - `SyntaxError: invalid syntax` (路径/反斜杠问题)
  - `The string is missing the terminator: "@` (YAML 引号冲突)
  - `SyntaxError: unterminated triple-quoted string literal` (嵌套引号)
- **根因**: PowerShell 和 Python 使用不同的字符串转义规则，嵌套时组合爆炸
- **正确做法**: 始终将 Python 代码写入 `.py` 文件再执行，避免 inline `-c`

### 2. 脚本路径参数混淆（发生 3 次）
- **现象**:
  - `build_index.py` 传入 skill 路径而非 vault 路径 → 返回 0 条目
  - `bootstrap_vault.py` 在目标目录不存在时报错而非自动创建
  - `enhance_skillmd.py` 只支持本地 vault，shared vault 需额外处理
- **根因**: 各脚本对参数路径的期望不一致，使用说明在 --help 但不直观
- **正确做法**: 建立一张"脚本 → 期望的 path 类型"映射表（见 LEARNINGS.md）

### 3. Set-Content 文件写入静默失败（发生 2 次）
- **现象**: 使用 PowerShell `@"..."@` here-string + `Set-Content` 时，部分文件实际未写入磁盘（templates/skill-execution-log-template.md 未创建）
- **根因**: 长文本 here-string 中嵌入特殊字符时，PowerShell 可能不报错但不写入
- **正确做法**: Python 写文件优先；PowerShell 写入后用 `Test-Path` 验证

### 4. 模板注入内容截断（1 次）
- **现象**: shared vault 注入时，只注入了 "配置需求" 部分（模板内容的最后段），前面的大段内容全部丢失
- **根因**: 模板解析逻辑错误 —— 脚本尝试 split("---") 去掉 preamble 但破坏了内容结构
- **正确做法**: 注入前先用 --dry-run 预览，验证完整内容
