"""
KK Nexus 统一配置

所有脚本从此处读取路径和密钥，避免散落硬编码。
"""

from pathlib import Path
import os


# === 路径 ===

TEXTAI_INDEX_DIR = Path.home() / ".txtai_index"
CODEX_SKILLS_DIR = Path.home() / ".codex" / "skills"
FA_VAULT_KNOWLEDGE = CODEX_SKILLS_DIR / "financial-analysis" / "vault" / "knowledge"
FA_VAULT_RAW_USER = CODEX_SKILLS_DIR / "financial-analysis" / "vault" / "raw" / "user"


# === API 密钥（从环境变量读取，永不硬编码）===

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "")
