# Cloudflare Pages Deployment

项目已配置 GitHub Actions CI 与 Cloudflare Pages 自动部署。

## GitHub Secrets

需要在 GitHub 仓库的 `Settings -> Secrets and variables -> Actions` 中配置：

- `CLOUDFLARE_API_TOKEN`
  - Cloudflare API Token
  - 需要 `Cloudflare Pages: Edit` 权限
- `CF_ACCOUNT_ID`
  - Cloudflare Account ID

## 手动触发

在 GitHub 仓库的 `Actions` 页面，选择 `CI / Build & Deploy` workflow，使用 `workflow_dispatch` 手动触发。

## 部署地址

https://1449b451.tenet-openclaw-arena.pages.dev
