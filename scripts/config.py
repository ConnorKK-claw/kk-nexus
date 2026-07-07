"""
KK Nexus 统一配置
所有脚本从此处读取路径和配置项，避免硬编码。

设计思路：
- 路径使用占位符机制，支持跨设备兼容
- API 密钥一律从环境变量读取，永不硬编码
- 支持 config.yaml 覆盖默认路径
"""

import sys, os, yaml, re
from pathlib import Path


# === 默认路径（可被 config.yaml 覆盖） ===

TEXTAI_INDEX_DIR = Path.home() / ".txtai_index"
CODEX_SKILLS_DIR = Path.home() / ".codex" / "skills"

# === API 密钥（从环境变量读取，永不硬编码） ===
# 按需在 .env 或系统环境变量中设置：
#   DEEPSEEK_API_KEY
#   TUSHARE_TOKEN
#   OPENAI_API_KEY
# 等

def _get_env(name: str) -> str:
    return os.environ.get(name, "")

DEEPSEEK_API_KEY = _get_env("DEEPSEEK_API_KEY")
TUSHARE_TOKEN = _get_env("TUSHARE_TOKEN")
IMA_OPENAPI_CLIENTID = _get_env("IMA_OPENAPI_CLIENTID")
IMA_OPENAPI_APIKEY = _get_env("IMA_OPENAPI_APIKEY")

# === Domain → 目标 vault 路径映射表 ===
# 编辑此字典以添加/修改你的员工 vault 路径
# 键为 domain 缩写，值为 vault raw/agent 路径
DOMAIN_VAULT_MAP = {
    # 示例：
    # "my-domain": CODEX_SKILLS_DIR / "my-skill" / "vault" / "raw" / "agent",
}

# === 占位符展开 ===

def _expand_placeholders(value, codex_home=None):
    """统一占位符展开：支持 %USERPROFILE%, %ONEDRIVE%, %CODEX_HOME%, %PYTHON%。

    跨设备兼容设计：
    - %USERPROFILE% 自动展开为用户主目录
    - %ONEDRIVE%    展开为 Windows OneDrive 根路径
    - %CODEX_HOME%  展开为 ~/.codex 或 CODEX_HOME 环境变量
    - %PYTHON%      展开为 PYTHON 环境变量或 sys.executable
    """
    if not isinstance(value, str):
        return value
    userprofile = os.path.expanduser("~")
    onedrive = os.environ.get("ONEDRIVE", "")
    python_exe = os.environ.get("PYTHON", "")
    if not python_exe:
        try:
            python_exe = sys.executable
        except NameError:
            import sys as _sys
            python_exe = _sys.executable
    if codex_home is None:
        codex_home = os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex"))
    value = value.replace("%USERPROFILE%", userprofile)
    if onedrive:
        value = value.replace("%ONEDRIVE%", onedrive)
    value = value.replace("%CODEX_HOME%", codex_home)
    if python_exe:
        value = value.replace("%PYTHON%", python_exe)
    value = os.path.expandvars(value)
    return value


def load_config():
    """从 config.yaml 加载配置，支持可移植占位符。"""
    _config_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.environ.get("CODEX_CONFIG", os.path.join(_config_dir, "..", "config.yaml"))
    if not os.path.exists(cfg_path):
        # 尝试项目根目录
        cfg_path = os.path.join(os.path.dirname(_config_dir), "config.yaml")
    if not os.path.exists(cfg_path):
        print(f"[config] No config.yaml found at {cfg_path}, using defaults.")
        return {}
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if cfg is None:
        return {}
    return cfg


def resolve_target_vault(cwd: str = "", domain_map: dict = None) -> str:
    """根据当前工作目录解析对应的 vault 目标路径。

    通过 Domain → vault 映射表查找最匹配的 vault。
    如果 domain_map 为空，则从 DOMAIN_VAULT_MAP 中按 cwd 关键词匹配。
    """
    if domain_map is None:
        domain_map = DOMAIN_VAULT_MAP
    cwd_lower = cwd.lower()
    for domain, vault_path in domain_map.items():
        if domain.lower() in cwd_lower:
            return str(vault_path)
    return ""
