# 每日国际新闻推送

每天早上8:00通过微信推送国际新闻。

## 使用前准备

1. **注册 Server酱**（免费）
   - 打开 https://sct.ftqq.com/
   - 用 GitHub 账号登录
   - 关注二维码绑定微信
   - 复制你的 SendKey

2. **创建 GitHub 仓库**
   - 在 GitHub 上新建一个仓库（public/private 均可）
   - 把本项目的文件全部 push 到仓库

3. **配置 GitHub Secrets**
   - 仓库 → Settings → Secrets and variables → Actions
   - New repository secret
   - Name: `SENDKEY`
   - Value: 粘贴你的 SendKey

4. **启用 Actions**
   - 仓库 → Actions → 找到 "每日国际新闻推送" 工作流
   - 默认北京时间每天 08:00 自动运行
   - 也可手动点击 "Run workflow" 测试

## 本地测试

```bash
pip install -r requirements.txt
SENDKEY=你的SendKey python fetch_news.py
```
