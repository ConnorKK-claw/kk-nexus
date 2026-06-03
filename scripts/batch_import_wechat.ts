import { searchAccountArticles, WeChatArticle } from "./sogou_wechat_search.ts";
import { execSync } from "child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync } from "fs";
import * as path from "path";
import readline from "readline";

interface Args { vault: string; domain: string; account: string; wechatId?: string; since?: string; until?: string; }

function parseArgs(): Args {
  const argv = process.argv.slice(2);
  const a: any = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--vault") a.vault = argv[++i];
    else if (argv[i] === "--domain") a.domain = argv[++i];
    else if (argv[i] === "--account") a.account = argv[++i];
    else if (argv[i] === "--wechat-id") a.wechatId = argv[++i];
    else if (argv[i] === "--since") a.since = argv[++i];
    else if (argv[i] === "--until") a.until = argv[++i];
  }
  if (!a.vault || !a.domain || !a.account) {
    console.error("Usage: bun run batch_import_wechat.ts --vault <path> --domain <prefix> --account <name> [--since YYYY-MM-DD] [--until YYYY-MM-DD]");
    process.exit(1);
  }
  return a;
}

function resolveVault(v: string): string {
  if (path.isAbsolute(v)) return v;
  const home = process.env.USERPROFILE || "";
  const p = path.join(home, ".codex", "skills", v);
  if (existsSync(p)) return p;
  return path.resolve(v);
}

function slug(t: string): string {
  return t.toLowerCase().replace(/[^\w\u4e00-\u9fff-]/g, "").replace(/\s+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "").slice(0, 60);
}

function dateFromStr(s: string): string {
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
  if (/^\d{4}-\d{1,2}-\d{1,2}$/.test(s)) {
    const p = s.split("-");
    return p[0] + "-" + p[1].padStart(2, "0") + "-" + p[2].padStart(2, "0");
  }
  return "";
}

function isDup(vaultPath: string, url: string): boolean {
  const dir = path.join(vaultPath, "raw", "user");
  if (!existsSync(dir)) return false;
  try {
    for (const f of readdirSync(dir).filter((x: string) => x.endsWith(".md"))) {
      if (readFileSync(path.join(dir, f), "utf-8").includes(url)) return true;
    }
  } catch {}
  return false;
}

function ask(q: string): Promise<string> {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise(r => rl.question(q, a => { rl.close(); r(a); }));
}

async function main() {
  const args = parseArgs();
  const vaultPath = resolveVault(args.vault);
  const rawDir = path.join(vaultPath, "raw", "user");

  console.log("==========================================");
  console.log("  公众号批量采集工具");
  console.log("==========================================");
  console.log("  公众号:", args.account);
  console.log("  vault:", vaultPath);
  console.log("  domain:", args.domain);
  if (args.since) console.log("  起始:", args.since);
  if (args.until) console.log("  截止:", args.until);
  console.log("");

  // Step 1: Search
  console.log("正在搜索公众号文章...");
  const result = await searchAccountArticles(args.account);

  if (!result.articles || result.articles.length === 0) {
    console.error("未找到文章。搜狗可能触发了验证，请手动打开 https://weixin.sogou.com/ 搜索后重试。");
    process.exit(1);
  }

  // Step 2: Filter by account name
  let articles = result.articles.filter((a: WeChatArticle) =>
    a.account && a.account.includes(args.account)
  );

  if (articles.length === 0) {
    // Fallback: use all results
    articles = result.articles;
  }

  // Step 3: Filter by date
  if (args.since || args.until) {
    articles = articles.filter((a: WeChatArticle) => {
      const d = dateFromStr(a.date);
      if (!d) return true;
      if (args.since && d < args.since) return false;
      if (args.until && d > args.until) return false;
      return true;
    });
  }

  // Step 4: Dedup
  const before = articles.length;
  articles = articles.filter((a: WeChatArticle) => !isDup(vaultPath, a.url));
  const skipped = before - articles.length;
  if (skipped > 0) console.log("去重跳过:", skipped, "篇（已存在）");

  if (articles.length === 0) {
    console.log("没有需要导入的新文章。");
    process.exit(0);
  }

  // Step 5: Show and confirm
  console.log("\n待导入文章列表：");
  for (let i = 0; i < Math.min(articles.length, 20); i++) {
    const a = articles[i];
    console.log(`  ${i+1}. [${a.date}] ${a.title.slice(0, 50)}`);
  }
  if (articles.length > 20) console.log(`  ... 还有 ${articles.length - 20} 篇`);

  const confirm = await ask(`\n共 ${articles.length} 篇，是否开始导入？(Y/n): `);
  if (confirm.toLowerCase() === "n") { console.log("已取消。"); process.exit(0); }

  // Step 6: Batch fetch
  if (!existsSync(rawDir)) mkdirSync(rawDir, { recursive: true });

  const baoyuScript = "C:/Users/hexk/.cc-switch/skills/llm-wiki/baoyu-url-to-markdown/scripts/main.ts";
  let success = 0;
  const failed: any[] = [];

  console.log("\n开始批量抓取...");
  for (let i = 0; i < articles.length; i++) {
    const a = articles[i];
    const d = dateFromStr(a.date) || new Date().toISOString().slice(0, 10);
    let fn = `${d}-${slug(a.title)}-wechat.md`;
    let fp = path.join(rawDir, fn);
    let c = 1;
    while (existsSync(fp)) { fn = `${c}-${d}-${slug(a.title)}-wechat.md`; fp = path.join(rawDir, fn); c++; }

    process.stdout.write(`  [${i+1}/${articles.length}] ${a.title.slice(0, 40)}... `);

    try {
      execSync(`bun run "${baoyuScript}" "${a.url}" -o "${fp}"`, {
        timeout: 60_000, stdio: ["ignore", "pipe", "pipe"], encoding: "utf-8",
      });
      process.stdout.write("OK\n");
      success++;
    } catch (err: any) {
      process.stdout.write("FAILED\n");
      failed.push({ title: a.title, error: err.message?.slice(0, 100) });
    }
  }

  console.log("\n==========================================");
  console.log("  导入完成");
  console.log(`  成功: ${success} / ${articles.length}`);
  if (failed.length > 0) {
    console.log("  失败:", failed.length);
    for (const f of failed) console.log(`    - ${f.title}: ${f.error}`);
  }
  console.log(`  保存位置: ${rawDir}`);
  console.log("\n下一步：运行蒸馏流程转换到 knowledge/");
}

if (import.meta.main) { main().catch(e => { console.error("Error:", e.message); process.exit(1); }); }