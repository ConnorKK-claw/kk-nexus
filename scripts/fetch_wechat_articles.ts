import { spawn } from "child_process";
import * as path from "path";
import * as fs from "fs";
import WebSocket from "ws";
import * as os from "os";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

class CdpSession {
  private ws: WebSocket;
  private msgId = 0;
  private pending = new Map<number, { resolve: Function; reject: Function }>();

  constructor(wsUrl: string) {
    this.ws = new WebSocket(wsUrl);
    this.ws.on("message", (data: Buffer) => this.onMessage(data));
  }

  waitOpen(): Promise<void> {
    return new Promise((r, j) => {
      if (this.ws.readyState === WebSocket.OPEN) { r(); return; }
      this.ws.on("open", () => r());
      this.ws.on("error", (e) => j(e));
    });
  }

  private onMessage(data: Buffer) {
    try {
      const msg = JSON.parse(data.toString());
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id)!;
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(msg.error.message));
        else resolve(msg.result);
      }
    } catch {}
  }

  async send(method: string, params: any = {}): Promise<any> {
    return new Promise((resolve, reject) => {
      const id = ++this.msgId;
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
      setTimeout(() => {
        if (this.pending.has(id)) { this.pending.delete(id); reject(new Error("timeout")); }
      }, 30_000);
    });
  }

  async eval(expression: string): Promise<any> {
    const r = await this.send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    return r.result.value;
  }

  async navigate(url: string): Promise<void> {
    await this.send("Page.enable");
    await this.send("Network.enable");
    await this.send("Page.navigate", { url });
    await new Promise(r => setTimeout(r, 10_000));
  }

  async getPageContent(): Promise<string> {
    const expr = `
      (function() {
        // Try Defuddle-like extraction: get article content
        var article = document.querySelector('article, .rich_media_content, #js_content, [class*="content"]');
        if (article) return article.innerText.slice(0, 10000);
        return document.body.innerText.slice(0, 10000);
      })()
    `;
    return await this.eval(expr);
  }

  close() { try { this.ws.close(); } catch {} }
}

async function getSogouArticles(accountName: string, cdp: CdpSession): Promise<any[]> {
  const url = "https://weixin.sogou.com/weixin?type=2&query=" + encodeURIComponent(accountName);
  await cdp.navigate(url);
  await new Promise(r => setTimeout(r, 3_000));

  // Extract article list
  const extractCode = `
    (function() {
      var articles = [];
      var seen = {};
      var items = document.querySelectorAll('.news-list > li');
      items.forEach(function(li) {
        var titleEl = li.querySelector('.txt-box h3 a[id*="title"]');
        if (!titleEl) return;
        var href = titleEl.getAttribute('href') || '';
        var title = (titleEl.textContent || '').trim().replace(/\\s+/g, ' ');
        if (!title || title.length < 3 || seen[href]) return;
        seen[href] = true;
        var accountEl = li.querySelector('.all-time-y2');
        var dateEl = li.querySelector('.s2');
        var date = '';
        if (dateEl) {
          var m = (dateEl.textContent || '').match(/(\\d{4}[-\\/]\\d{1,2}[-\\/]\\d{1,2})/);
          if (m) date = m[1];
        }
        articles.push({
          title: title.replace(/<[^>]+>/g, ''),
          url: href.startsWith('/') ? 'https://weixin.sogou.com' + href : href,
          date: date,
          account: (accountEl ? (accountEl.textContent || '').trim() : ''),
        });
      });
      return articles;
    })()
  `;
  return await cdp.eval(extractCode);
}

async function fetchArticle(url: string, cdp: CdpSession): Promise<string> {
  await cdp.navigate(url);
  await new Promise(r => setTimeout(r, 3_000));

  // Try to get WeChat article content
  const content = await cdp.eval(`
    (function() {
      // WeChat article page
      var title = document.querySelector('#activity-name, .rich_media_title, h1')?.textContent?.trim() || document.title;
      var author = document.querySelector('#js_name, .rich_media_meta_nickname, .profile_nickname')?.textContent?.trim() || '';
      var body = document.querySelector('#js_content')?.innerText || document.querySelector('.rich_media_content')?.innerText || document.body.innerText;
      return JSON.stringify({ title: title, author: author, body: body.slice(0, 15000), url: window.location.href });
    })()
  `);
  return content;
}

function makeSlug(t: string): string {
  return t.toLowerCase().replace(/[^\w\u4e00-\u9fff]/g, "").replace(/\s+/g, "-").slice(0, 50);
}

async function main() {
  const args = process.argv.slice(2);
  const accountIdx = args.indexOf("--account");
  const accountName = accountIdx >= 0 ? args[accountIdx + 1] : "";
  const vaultIdx = args.indexOf("--vault");
  const vaultPath = vaultIdx >= 0 ? args[vaultIdx + 1] : "";
  const sinceIdx = args.indexOf("--since");
  const since = sinceIdx >= 0 ? args[sinceIdx + 1] : "";
  const untilIdx = args.indexOf("--until");
  const until = untilIdx >= 0 ? args[untilIdx + 1] : "";

  if (!accountName || !vaultPath) {
    console.error('Usage: --account "名称" --vault <path> [--since YYYY-MM-DD] [--until YYYY-MM-DD]');
    process.exit(1);
  }

  const rawDir = path.join(vaultPath, "raw", "user");
  if (!fs.existsSync(rawDir)) fs.mkdirSync(rawDir, { recursive: true });

  // Start Chrome
  const port = 0 | (Math.random() * 40000 + 20000);
  const profileDir = path.join(os.tmpdir(), "sg-" + Date.now());
  fs.mkdirSync(profileDir, { recursive: true });
  const chrome = spawn(CHROME_PATH, [
    "--remote-debugging-port=" + port, "--user-data-dir=" + profileDir,
    "--no-first-run", "--no-default-browser-check", "--disable-popup-blocking", "about:blank",
  ], { stdio: "ignore" });
  await new Promise(r => setTimeout(r, 6_000));

  const resp = await fetch("http://127.0.0.1:" + port + "/json");
  const targets: any = await resp.json();
  const page = targets.find((t: any) => t.type === "page");
  if (!page) throw new Error("No page target");

  const cdp = new CdpSession(page.webSocketDebuggerUrl);
  await cdp.waitOpen();

  try {
    // Step 1: Search for articles
    console.error("搜索:", accountName);
    let articles = await getSogouArticles(accountName, cdp);

    console.error('Raw articles:', JSON.stringify(articles.map(function(a: any) { return {t:a.title, acc:a.account}; })));
    // Filter by account
    articles = articles.filter((a: any) => a.account && a.account.includes(accountName));

    // Filter by date
    if (since || until) {
      articles = articles.filter((a: any) => {
        if (!a.date) return true;
        if (since && a.date < since) return false;
        if (until && a.date > until) return false;
        return true;
      });
    }

    console.error("找到", articles.length, "篇");

    // Check for duplicates
    const before = articles.length;
    articles = articles.filter((a: any) => {
      const slug = makeSlug(a.title);
      const fn = `${a.date}-${slug}-wechat.md`;
      return !fs.existsSync(path.join(rawDir, fn));
    });
    const skipped = before - articles.length;
    if (skipped > 0) console.error("去重跳过:", skipped);

    if (articles.length === 0) { console.error("没有新文章"); process.exit(0); }

    console.log(JSON.stringify(articles)); // Output for user confirmation

    // Step 2: Fetch each article
    let success = 0;
    for (let i = 0; i < articles.length; i++) {
      const a = articles[i];
      const slug = makeSlug(a.title);
      const fn = `${a.date}-${slug}-wechat.md`;
      const fp = path.join(rawDir, fn);

      process.stdout.write(`[${i+1}/${articles.length}] ${(a.title || "").slice(0, 40)}... `);

      try {
        // Follow Sogou redirect in the same session
        const content = await fetchArticle(a.url, cdp);
        const parsed = JSON.parse(content);

        // Write markdown file
        const md = `---\nurl: ${a.url}\ntitle: "${(parsed.title || a.title).replace(/"/g, '\\"')}"\nauthor: "${(parsed.author || "").replace(/"/g, '\\"')}"\ncaptured_at: "${new Date().toISOString()}"\n---\n\n# ${parsed.title || a.title}\n\n${parsed.body}`;
        fs.writeFileSync(fp, md, "utf-8");
        process.stdout.write("OK\n");
        success++;
      } catch (err: any) {
        process.stdout.write("FAIL: " + err.message.slice(0, 60) + "\n");
      }
    }

    console.error(`\n完成: ${success}/${articles.length} 篇`);
    console.error("保存位置:", rawDir);
  } finally {
    cdp.close();
    try { process.kill(chrome.pid); } catch {}
    setTimeout(() => { try { fs.rmSync(profileDir, { recursive: true }); } catch {} }, 1000);
  }
}

if (import.meta.main) { main().catch(e => { console.error("Error:", e.message); process.exit(1); }); }