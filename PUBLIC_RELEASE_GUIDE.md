# 公开发布与自动更新说明

## 给别人访问

公开网址由 Netlify 提供。别人只需要浏览器打开网址，不需要下载文件夹，不需要安装 Python。

## GitHub Actions 自动更新

仓库连接 Netlify 后，GitHub Actions 会在双色球开奖日晚间定时运行：

1. 查询官方公开开奖数据。
2. 校验数据格式与号码范围。
3. 重新生成 `double/ssq_analyzer.html`。
4. 同步为 `release/index.html`。
5. 自动提交更新，Netlify 自动重新部署。

## Netlify 设置

Netlify 站点建议这样设置：

- Build command：留空，或填 `echo static site`
- Publish directory：`release`
- Password protection：关闭

## 手动触发更新

进入 GitHub 仓库：

1. 打开 `Actions`。
2. 选择 `Update lottery data`。
3. 点击 `Run workflow`。

## 合法提示

页面只做开奖记录查询、历史统计和中奖核验参考，不预测开奖结果，不构成购彩建议。最终结果以官方公告和销售机构兑奖规则为准。

