# 🛠️ 星哥需操作：GSC + Umami 注册（5分钟搞定）

> 生成时间: 2026-04-20 | 预计用时: 5分钟

## 一、Google Search Console（GSC）

### 步骤
1. 打开 https://search.google.com/search-console
2. 登录你的Google账号
3. 点击「添加资源」→ 选择「网址前缀」
4. 输入 `https://singclaw.xyz`
5. 选择验证方式 → 推荐「HTML标记」
   - 复制Google提供的 `<meta>` 标签
   - 发给我，我加到 singclaw-site 的 index.html 并提交
6. 验证通过后 → 提交 Sitemap：`https://singclaw.xyz/sitemap.xml`

### 备选方案
- 如果用「DNS TXT记录」验证：复制TXT值发给我，你在域名DNS加一条TXT记录

---

## 二、Umami 统计部署

### 方案A：Umami Cloud（免费，最快）
1. 打开 https://umami.is
2. 点击「Get Started」注册
3. 创建第一个网站，填：
   - 网站名称: SingClaw
   - 域名: singclaw.xyz
4. 复制生成的 tracking script（类似 `<script defer src="..."></script>`）
5. 发给我，我加到首页 head 里

### 方案B：自建（免费，需你的服务器）
1. 如果你有VPS/服务器：
   ```bash
   docker run -d \
     --name umami \
     -p 3000:3000 \
     -e DATABASE_URL=postgresql://umami:umami@db:5432/umami \
     -e HASH_SALT=your-random-string \
     ghcr.io/umami-software/umami:postgresql-latest
   ```
2. 访问 http://你的服务器:3000，登录 admin/umami
3. 添加网站 → 复制 tracking script 发给我

### 推荐
先走方案A（Umami Cloud），5分钟搞定，零运维。

---

## 三、完成后我能做的
- ✅ GSC数据 → 自动SEO周报（关键词排名/点击/展示）
- ✅ Umami数据 → 自动流量周报（UV/PV/来源/停留时间）
- ✅ 数据接入 SingClaw Docs 看板
