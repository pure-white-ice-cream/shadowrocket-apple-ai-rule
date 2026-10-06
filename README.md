# Shadowrocket：Apple Intelligence、Siri 与 ChatGPT

用于 Apple Intelligence、Siri 和 ChatGPT 的完整分流配置，同时包含国内网站、Google、Telegram 等常用服务规则。

## 使用前准备

- 安装 Shadowrocket，并准备可用的代理节点或订阅；本项目仅提供分流配置。
- 备份当前配置，方便需要时切换回来。
- 确认设备、系统版本、语言和地区支持 Apple Intelligence 及 ChatGPT 扩展。

## 扫码导入（推荐）

打开 **Shadowrocket 首页的扫描入口**，扫描下方二维码，按提示添加配置。二维码使用 Shadowrocket 配置导入链接。

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
3. 选择可用的代理节点并开启连接。
4. 打开“设置 → Apple Intelligence 与 Siri → ChatGPT”，按系统提示设置扩展。
5. 使用 Siri 发起一次“询问 ChatGPT”，确认能够得到回复。

配置中的 `PROXY` 使用你在 Shadowrocket 中选择的代理节点。国内网站、局域网和普通 Apple 服务按规则直连；Apple AI / Siri 的指定域名和 ChatGPT 服务优先使用代理。

## 更新配置

在 Shadowrocket 的远程配置列表中，更新或重新下载同一地址的配置，再确认本地使用的是更新后的文件。无需重新扫码。建议先备份自己对配置所作的修改，再下载更新。

## 已有配置只添加 AI 规则

如果希望继续使用自己的配置，复制 [AI 补丁规则](rules/apple-ai-chatgpt.list)，粘贴到已有配置 `[Rule]` 的最顶部，放在 Apple 通用直连、Apple IP 直连、`GEOIP` 和 `FINAL` 规则之前。

补丁不是完整配置，无需新增第二个 `[Rule]` 段，也不要将 `.list` 文件当作完整配置导入。

## 无法使用时

- **配置下载失败：** 先使用当前可用的代理连接，再重试下载链接。
- **ChatGPT 扩展不可用：** 先确认同一节点可以访问 [ChatGPT](https://chatgpt.com)，再查看扩展请求的连接记录与命中策略。网页可用仍需单独验证 Siri 扩展。
- **怀疑分流问题：** 临时将全局路由切换到“代理”做对照。如果全局代理可用而配置模式不可用，请查看失败连接的域名和规则；完成测试后恢复“配置”。
- **两种路由模式都不可用：** 检查节点出口是否受服务支持，以及设备、账号、系统版本、语言和地区是否符合使用要求。
- **语音功能异常：** 确认代理节点支持所需 UDP 转发，再分别测试文本与语音功能。

本配置无需安装 MITM 证书。实际服务可用性取决于设备条件、服务地区支持及代理节点。
