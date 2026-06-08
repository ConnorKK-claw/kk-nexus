import { spawn } from "child_process";
import * as path from "path";
import * as fs from "fs";
import WebSocket from "ws";
import * as os from "os";

export interface WeChatArticle {
  title: string;
  url: string;
  date: string;
  snippet: string;
  account: string;
}

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const SOGOU_ARTICLE_SEARCH = "https://weixin.sogou.com/weixin?type=2&query=";

class SimpleCdp {
  private ws: WebSocket;
  private msgId = 0;
  private pending = new Map<number, { resolve: Function; reject: Function }>();

  constructor(wsUrl: string) {
    this.ws = new WebSocket(wsUrl);
    this.ws.on("message", (data: Buffer) => this.onMessage(data));
  }

  waitForOpen(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws.readyState === WebSocket.OPEN) { resolve(); return; }
      this.ws.on("open", () => resolve());
      this.ws.on("error", (e) => reject(e));
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
        if (this.pending.has(id)) {
          this.pending.delete(id);
          reject(new Error("CDP timeout: " + method));
        }
      }, 20_000);
    });
  }

  async navigate(url: string): Promise<void> {
    await this.send("Page.enable");
    await this.send("Network.enable");
    await this.send("Page.navigate", { url });
    await new Promise(r => setTimeout(r, 8_000));
  }

  async evaluate(expression: string): Promise<any> {
    const result = await this.send("Runtime.evaluate", {
      expression, returnByValue: true, awaitPromise: true,
    });
    return result.result.value;
  }

  close() { try { this.ws.close(); } catch {} }
}

export async function searchAccountArticles(
  accountName: string,
): Promise<{ articles: WeChatArticle[] }> {
  const port = 0 | (Math.random() * 40000 + 20000);
  const profileDir = path.join(os.tmpdir(), "sogou-" + Date.now());
  fs.mkdirSync(profileDir, { recursive: true });

  const chrome = spawn(CHROME_PATH, [
    "--remote-debugging-port=" + port, "--user-data-dir=" + profileDir,
    "--no-first-run", "--no-default-browser-check", "--disable-popup-blocking", "about:blank",
  ], { stdio: "ignore" });

  // Wait for Chrome to be ready
  await new Promise(r => setTimeout(r, 6_000));

  const resp = await fetch("http://127.0.0.1:" + port + "/json");
  const targets: any[] = await resp.json();
  const page = targets.find((t: any) => t.type === "page");
  if (!page) throw new Error("No page target");

  const cdp = new SimpleCdp(page.webSocketDebuggerUrl);
  await cdp.waitForOpen();

  try {
    const searchUrl = SOGOU_ARTICLE_SEARCH + encodeURIComponent(accountName);
    await cdp.navigate(searchUrl);

    // Extract articles
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
    var accountName = accountEl ? (accountEl.textContent || '').trim() : '';

    var dateEl = li.querySelector('.s2');
    var date = '';
    if (dateEl) {
      var m = (dateEl.textContent || '').match(/(\\d{4}[-\\/]\\d{1,2}[-\\/]\\d{1,2})/);
      if (m) date = m[1];
    }

    var snippetEl = li.querySelector('.txt-info');
    var snippet = snippetEl ? (snippetEl.textContent || '').trim() : '';

    articles.push({
      title: title.replace(/<[^>]+>/g, ''),
      url: href.startsWith('/') ? 'https://weixin.sogou.com' + href : href,
      date: date,
      snippet: snippet.slice(0, 120),
      account: accountName,
    });
  });
  return { articles: articles };
})();
`;
    const result = await cdp.evaluate(extractCode);
    return result;
  } finally {
    cdp.close();
    try { process.kill(chrome.pid); } catch {}
    // Cleanup temp profile
    setTimeout(() => { try { fs.rmSync(profileDir, { recursive: true }); } catch {} }, 1000);
  }
}

async function main() {
  const args = process.argv.slice(2);
  const idx = args.indexOf("--account");
  const name = idx >= 0 ? args[idx + 1] : "";
  if (!name) { console.error('Usage: --account "名称"'); process.exit(1); }

  const result = await searchAccountArticles(name);
  process.stdout.write(JSON.stringify(result, null, 2));
}

if (import.meta.main) { main().catch(e => { console.error("Error:", e.message); process.exit(1); }); }