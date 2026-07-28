# GitHub Actions 自动更新方案

## 目标

让普通用户打开公开网址时，尽量看到最新开奖数据；维护者不需要每期手动上传网页。

## 推荐架构

```mermaid
flowchart LR
    A[GitHub Actions 定时任务] --> B[运行 Python 数据同步]
    B --> C[查询官方数据源]
    C --> D[合法性与数据校验]
    D --> E[生成 release/index.html]
    E --> F[自动提交到仓库]
    F --> G[Netlify 自动部署]
    G --> H[用户打开网址]
```

## 工作方式

1. GitHub 仓库保存项目代码和 `release/index.html`。
2. GitHub Actions 每天定时运行，例如每天 22:30 和 23:30。
3. 脚本从中国福彩网/中彩网、中国体彩网查询最新开奖数据。
4. 数据通过校验后，重新生成单文件网页。
5. 如果网页有变化，Actions 自动提交。
6. Netlify 连接 GitHub 仓库后自动重新部署。
7. 用户打开同一个网址即可看到更新后的页面。

## 你需要做什么

1. 创建或提供一个 GitHub 仓库。
2. 把本项目上传到仓库。
3. 在 Netlify 里把站点连接到这个 GitHub 仓库。
4. 关闭 Netlify 的 Password Protection。
5. 确认 Netlify 发布目录设置为 `release`，发布文件为 `index.html`。

## 我需要做什么

1. 增加 `.github/workflows/update-lottery-data.yml`。
2. 调整脚本，让它更新数据后自动复制 `ssq_analyzer.html` 到 `release/index.html`。
3. 增加数据源校验与失败保护。
4. 增加页面上的“数据来源、更新时间、免责声明”。
5. 后续扩展多彩种数据源。

## 为什么不直接让浏览器实时抓数据

普通静态网页直接跨域请求官方站点，容易被浏览器 CORS 限制，也可能对官方站点造成不稳定访问。更稳的方式是让 GitHub Actions 在后台定时抓取并生成静态页面。

## 当前建议

先做双色球自动更新闭环，确认稳定后再扩展大乐透、福彩3D、排列3、排列5、七星彩、七乐彩。
