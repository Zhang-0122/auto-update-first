# 公开发布与自动更新说明

## 给别人访问

公开网址由 Netlify 提供。别人只需要浏览器打开网址，不需要下载文件夹，不需要安装 Python。

## GitHub Actions 自动更新

仓库连接 Netlify 后，GitHub Actions 会在双色球开奖日晚间定时运行：

1. 查询官方最新期号和开奖日期。
2. 如果当前页面已经同步到这个日期，则跳过更新。
3. 如果官方日期或号码有变化，再校验并更新数据。
4. 重新生成 `double/ssq_analyzer.html` 并同步为 `release/index.html`。
5. 自动提交更新，Netlify 自动重新部署。

## Netlify 设置

Netlify 站点建议这样设置：

- Build command：留空，或填 `echo static site`
- Publish directory：`release`
- Password protection：关闭

## 自动健康检查

仓库包含 `Check live site` 工作流，每天会自动检查公开网址：

1. 网址能否返回 HTTP 200。
2. 是否被 Netlify 密码保护拦住。
3. 页面是否包含“已同步到”。
4. 页面是否包含官方来源。
5. 页面是否包含免责声明。

如果检查失败，GitHub Actions 会显示红色失败，并可通过 GitHub 邮件提醒维护者。

## 免费使用说明

当前方案使用 Netlify 静态网站托管和 GitHub Actions 定时任务。对于单个静态 HTML 页面、小流量访问、普通个人使用，通常可以长期使用免费额度。

但免费不是我能绝对保证的永久承诺，因为 Netlify 和 GitHub 的套餐政策、流量限制、账号规则可能变化。建议不要开启付费插件、团队商业套餐、付费构建加速或额外域名服务。

你不需要一直打开 GitHub，也不需要一直开着自己的电脑。自动更新和健康检查都在 GitHub/Netlify 云端运行。

## 手动触发更新

进入 GitHub 仓库：

1. 打开 `Actions`。
2. 选择 `Update lottery data`。
3. 点击 `Run workflow`。

## 合法提示

页面只做开奖记录查询、历史统计和中奖核验参考，不预测开奖结果，不构成购彩建议。最终结果以官方公告和销售机构兑奖规则为准。
