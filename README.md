# Shadowrocket：广告过滤、Apple Intelligence、Siri 与 ChatGPT

基于 [Johnshall 的白名单过滤 + 广告配置](https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/sr_top500_whitelist_ad.conf)，完整保留上游广告过滤、国内外网站分流，并优先代理指定的 Apple Intelligence、Siri 与 ChatGPT 域名。

## 使用前准备

- 安装 Shadowrocket，并准备可用的代理节点或订阅；本项目仅提供分流配置。
- 备份当前配置，方便需要时切换回来。
- 确认设备、系统版本、语言和地区支持 Apple Intelligence 及 ChatGPT 扩展。规则只负责网络分流，不能替你开启系统功能或改变服务资格。

## 扫码导入（推荐）

打开 **Shadowrocket 首页的扫描入口**，扫描下方二维码，按提示添加完整配置。

![使用 Shadowrocket 扫码导入完整配置](assets/shadowrocket-config-qr.png)

如果二维码显示在同一台手机上，可以先保存图片，再通过扫描界面的相册入口识别；如当前版本不支持相册识别，请使用下面的链接导入方式。

## 链接导入

在 Shadowrocket 的 **配置** 页面，选择添加远程配置的入口，粘贴以下地址并下载：

```text
https://raw.githubusercontent.com/pure-white-ice-cream/shadowrocket-apple-ai-rule/main/shadowrocket-apple-ai.conf
```

[查看完整配置](shadowrocket-apple-ai.conf) · [打开配置下载链接](https://raw.githubusercontent.com/pure-white-ice-cream/shadowrocket-apple-ai-rule/main/shadowrocket-apple-ai.conf)

## 启用配置

1. 在“配置”页面选中下载的 `shadowrocket-apple-ai.conf`，确认它成为当前使用的配置（带勾选标记）。
2. 返回首页，将“全局路由”设为 **配置**。
3. 选择可用的代理节点并开启连接。推荐先使用你已经验证可用的 Siri AI Beta 节点。
4. 在系统设置中开启 Apple Intelligence，并进入“设置 → Apple Intelligence 与 Siri → ChatGPT”，按提示设置扩展。
5. 使用 Siri 发起一次“询问 ChatGPT”，确认能够得到回复。

广告域名按上游规则拦截；国内网站和白名单网站直连，其余流量按上游规则和最终代理策略处理。Apple AI / Siri 与 ChatGPT 的本地优先规则放在广告和通用直连规则之前，使用首页选择的 `PROXY` 节点。本配置不含独立 AI 策略组。

## 自动同步与手机更新

本仓库通过 GitHub Actions **每 6 小时检查一次上游**，有变化时自动更新完整配置。同步时会重新加入本项目的 AI 优先规则，并移除 Siri 相关的两项代理绕过设置，避免被上游更新覆盖。若下载失败或内容检查失败，将保留上一份配置。GitHub 定时任务可能延迟。

**仓库自动更新不等于手机自动更新。** 在 Shadowrocket 的远程配置列表中，更新或重新下载同一地址的配置，再确认本地使用的是新版文件。如果你的版本提供远程配置自动更新设置，可在应用中另行开启。下载地址和二维码保持不变，无需重新扫码。

不要直接修改生成的完整配置来保存长期自定义规则；下一次同步会重新生成它。需要持久化 AI 规则时，在仓库中修改 [AI 补丁规则](rules/apple-ai-chatgpt.list)，自动同步会将这些规则重新合并。

仓库维护者也可以在 [Actions](https://github.com/pure-white-ice-cream/shadowrocket-apple-ai-rule/actions/workflows/sync-upstream.yml) 中选择 **Sync upstream Shadowrocket rules → Run workflow** 手动同步。同步失败时可在该页面查看日志。

## 已有配置只添加 AI 规则

复制 [AI 补丁规则](rules/apple-ai-chatgpt.list)，粘贴到已有配置 `[Rule]` 的最顶部，放在广告过滤、Apple 通用直连、Apple IP 直连、`GEOIP` 和 `FINAL` 规则之前。同时从 `[General]` 的 `skip-proxy` 中移除 `*.ls.apple.com` 和 `seed-sequoia.siri.apple.com`（如存在）。

补丁不是完整配置，无需新增第二个 `[Rule]` 段，也不要将 `.list` 文件当作完整配置导入。

## 无法使用时

- **配置下载失败：** 先使用当前可用的代理连接，再重试下载链接。
- **ChatGPT 扩展不可用：** 先确认同一节点可以访问 [ChatGPT](https://chatgpt.com)，再查看扩展请求的连接记录与命中策略。网页可用仍需单独验证 Siri 扩展。
- **怀疑分流问题：** 临时将全局路由切换到“代理”做对照。如果全局代理可用而配置模式不可用，请查看失败连接的域名和规则；完成测试后恢复“配置”。
- **两种路由模式都不可用：** 检查节点出口是否受服务支持，以及设备、账号、系统版本、语言和地区是否符合使用要求。
- **网站或应用被误拦：** 查看连接记录是否命中 `REJECT`，确认具体域名后再调整规则。
- **语音功能异常：** 确认代理节点支持所需 UDP 转发，再分别测试文本与语音功能。

Siri / ChatGPT 代理规则无需解密它们的 HTTPS 流量。DNS、IPv6、URL Rewrite 和 MITM 配置沿用上游设置，实际服务可用性取决于设备条件、服务地区支持及代理节点。

## 上游与许可

上游配置来自 [Johnshall/Shadowrocket-ADBlock-Rules-Forever](https://github.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever)，作者为 Moshel 和 Johnshall。本项目添加 AI 优先规则、调整相关代理绕过设置，并自动同步上游；依据 [CC BY-SA 4.0](LICENSE) 共享。
