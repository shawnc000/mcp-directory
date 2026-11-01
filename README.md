# MCP Directory / MCP 目录

中文优先的 MCP 与 AI 代理工具目录。默认页面是中文，英文在 `/en/`。每条记录先给公开安全评估：许可证标识、`pushed_at` 的年龄、是否归档，以及 README 摘录里有没有弃用说法、GitHub 警告块或 CVE 编号。没有安全分。0–100 的热度分仍只来自星标、推送新旧和 SPDX 许可证。描述和 README 摘录引自 GitHub；中文译文只覆盖目录里保存的描述开头，不补写截断的句子。

Chinese-first directory of MCP and AI agent tools. Chinese is the default; English is under `/en/`. Each listing leads with a public security assessment: the license id, the age of `pushed_at`, the archived flag, and whether the README excerpt contains a deprecation phrase, a GitHub warning, or a CVE id. There is no safety score. The 0–100 popularity score still uses only stars, push recency, and the SPDX license. Descriptions and README excerpts are quoted from GitHub. Chinese translations cover the description prefix stored in the catalog and do not finish cut-off sentences.

线上地址 / Live site: <https://shawnc000.github.io/mcp-directory/>

## 分数 / Score

公式第 1 版，满分 100。每个工具页都写出这个仓库自己的算式和抓取时间。

Formula version 1, out of 100. Every tool page prints the arithmetic for that repository and the time the data was fetched.

| 分项 | 规则 |
| --- | --- |
| 星标，最多 50 | `min(50, 20 × log10(stars + 1))`。大约 316 个 star 触及上限。超过之后页面仍显示原始星标数。 |
| 活跃，0 / 15 / 30 | 看 `pushed_at` 到抓取时刻的完整 UTC 天数。小于 30 天得 30，满 30 且小于 180 得 15，否则 0。不用 `updated_at`。 |
| 许可证，0 或 20 | `spdx_id` 有值且不是 `NOASSERTION` 得 20。没有许可证对象，以及 `NOASSERTION`，都是 0，页面会写明是哪一种。 |

总分是三项之和再用 Python 3 的 `round`（正好 .5 时向偶数舍入）。分类是编者标签，不是 GitHub 字段。这个分数不是安全审计，也不是安装建议。

## 本地构建 / Build locally

需要 Python 3.11+，只用标准库。完整构建需要 `GITHUB_TOKEN`，否则公开 API 的速率限制不够覆盖整个目录。

```bash
export GITHUB_TOKEN=ghp_...   # classic 或 fine-grained，能读取公开仓库即可
python -m unittest discover -s tests -v
python build.py
```

生成结果在 `site/`。项目页的链接前缀是 `/mcp-directory`。本地预览：

```bash
mkdir -p /tmp/pages-root
ln -s "$PWD/site" /tmp/pages-root/mcp-directory
python -m http.server 8765 --directory /tmp/pages-root
```

然后打开 <http://127.0.0.1:8765/mcp-directory/>。

`data/catalog.json` 是 v2 名单：440 个公开仓库，来自 `topic:mcp-server`（星标不少于 150）或 `topic:mcp`（星标不少于 300），搜索时未归档，并且有 SPDX 许可证，另加 3 条种子。话题不等于我们做过渗透测试。`ingest.py` 会按同样规则把新的公开搜索结果合并进这个文件。构建时重新请求 GitHub 仓库 API；某个仓库刷新失败且快照里有星标和许可证时，页面会标明使用了快照。没有快照又刷新失败，则整次构建失败，Pages 继续提供上一次成功的部署。

`data/desc_zh.json` 是对描述开头的中文译文。实时描述若不再以那段原文开头，页面不显示译文。

## 提交工具 / Submit a tool

用 GitHub issue 表单：[提交工具](https://github.com/shawnc000/mcp-directory/issues/new?template=submit-tool.yml)。收录免费。维护者把接受的仓库写进 `data/catalog.json`，下一次构建再去抓公开元数据。提交不会自动进目录。

精选位是占位，标记为即将推出。站点上没有标价，也没有付款链接。

## 部署 / Deploy

`.github/workflows/pages.yml` 在推送到 `main`、每天 06:17 UTC，以及手动 `workflow_dispatch` 时运行。它执行测试和 `build.py`，然后用官方的 `actions/upload-pages-artifact` 与 `actions/deploy-pages` 发布 `site/`。定时任务只会在默认分支上跑。

Pages 的构建来源必须是 GitHub Actions。如果仓库设置里还没打开，到 Settings → Pages → Build and deployment → Source，选择 GitHub Actions。

## 许可 / License

这个仓库里的生成器代码使用 MIT，见 `LICENSE`。工具页上的描述和 README 摘录属于各自上游项目，只作引用。
