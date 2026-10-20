# Shadowrocket：广告过滤、Apple Intelligence、Siri 与 ChatGPT

基于 [Johnshall 的白名单过滤 + 广告配置](https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/sr_top500_whitelist_ad.conf)，保留上游广告过滤与国内外网站分流，增加 Apple AI、ChatGPT、苹果服务、微软服务四个独立服务策略组。四组默认跟随首页当前节点，各配一个“自选节点”辅助组，用于单独固定节点；也可分别改为直连。

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
3. 选择可用的代理节点并开启连接；四个服务分组默认选择 `PROXY`，跟随首页当前节点。平时只需在首页换节点；需要让某组单独固定节点时，按下节操作。Apple AI 推荐先选择你已验证可用的 Siri AI Beta 节点。
4. 在系统设置中开启 Apple Intelligence，并进入“设置 → Apple Intelligence 与 Siri → ChatGPT”，按提示设置扩展。
5. 使用 Siri 发起一次“询问 ChatGPT”，确认能够得到回复。

## 在 Shadowrocket 中切换分组节点

进入 **配置 → 当前配置右侧的 ⓘ → 代理分组**。部分版本也可从首页下拉进入分组面板；入口以应用版本为准。

| 分组 | 负责的流量 | 默认选择 |
| --- | --- | --- |
| `Apple AI` | 本地优先规则中的 Apple Intelligence、Siri 与中继端点 | `PROXY` |
| `ChatGPT` | ChatGPT、OpenAI 及补丁中的登录、语音端点 | `PROXY` |
| `苹果服务` | Apple、iCloud、App Store、下载、地图及指定 Apple CDN/IP | `PROXY` |
| `微软服务` | Microsoft、账户登录、Microsoft 365、Outlook、OneDrive、Bing/Copilot 等 | `PROXY` |

四个服务组使用明确的策略列表，默认项为 `PROXY`，不在同一组内混用节点正则：

- **统一跟随首页：** 保持四个服务组为 `PROXY`，之后只在首页换节点。
- **某组固定节点：** 例如先在 `Apple AI 自选节点` 中选美国节点，再把 `Apple AI` 从 `PROXY` 切为 `Apple AI 自选节点`。微软服务也可在自己的辅助组中选日本节点，互不影响。
- **某组直连：** 在该服务组选择 `DIRECT`。
- **恢复跟随：** 把服务组切回 `PROXY`。

只有四个“自选节点”辅助组使用 `policy-regex-filter=.*` 匹配本机已导入的节点，不依赖订阅名称或地区命名。辅助组可能显示节点列表中的第一个节点，但只有服务组明确选择对应辅助组时才会使用它；服务组为 `PROXY` 时，辅助组的选择不会改变出口。

旧版将 `PROXY`、`DIRECT` 与节点正则写在同一个组内，用户反馈其默认落到第一个节点。新版把两种选择方式分开，规避这一组合。此结构参照 [Shadowrocket 懒人配置的静态服务组与正则节点组](https://github.com/LOWERTOP/Shadowrocket/blob/main/lazy_group.conf)；仓库检查可验证配置结构与规则优先级，实际首页跟随行为仍需在 Shadowrocket 中验证。

分流顺序为：**AI 优先规则 → 上游广告拦截 → 苹果/微软服务规则 → 上游其余规则**。苹果与微软的本地服务规则覆盖下方旧的直连规则，默认走代理；Apple AI 和 ChatGPT 独立于普通苹果服务组，普通苹果服务改为直连时，两组仍按各自选择处理。国内网站和其他白名单仍按上游规则直连，其余流量按上游及最终代理策略处理。

服务分组覆盖 [服务规则文件](rules/service-groups.list) 中列出的域名与 IP，并非所有 Apple/Microsoft 旗下服务的完整清单。未收录域名仍使用上游规则；需要扩展时可在该文件中补充。

## 自动同步与手机更新

本仓库通过 GitHub Actions **每 6 小时检查一次上游**，有变化时自动更新完整配置。同步时会重新加入四个服务策略组、四个自选节点辅助组、AI 优先规则与苹果/微软服务规则，并移除 Siri 相关的两项代理绕过设置，避免被上游更新覆盖。局域网、`captive.apple.com` 与 `sequoia.apple.com` 的上游代理绕过设置保留。若下载失败或内容检查失败，将保留上一份配置。GitHub 定时任务可能延迟。

**仓库自动更新不等于手机自动更新。** 在 Shadowrocket 的远程配置列表中，更新或重新下载同一地址的配置，再确认本地使用的是新版文件。如果你的版本提供远程配置自动更新设置，可在应用中另行开启。下载地址和二维码保持不变，无需重新扫码。

不要直接修改生成的完整配置来保存长期自定义规则；下一次同步会重新生成它。需要持久化规则时，在仓库中修改 [AI 补丁规则](rules/apple-ai-chatgpt.list) 或 [服务分组规则](rules/service-groups.list)；分组定义由 [生成脚本](scripts/sync_upstream.py) 管理。手机重新下载完整配置后，请检查各组当前选项；应用可能保留旧选择，文件中的默认值不保证覆盖手机已保存的选择。

若从旧版升级后，服务组仍显示“香港01”等具体节点，请检查当前配置的服务组定义中是否还含 `policy-regex-filter`。新版服务组应只有 `PROXY`、`DIRECT`、对应“自选节点”三个选项。若本地仍沿用旧分组选项，可将新版保存为一份新的本地配置后启用，保留旧文件备用。验证时在首页切换两个节点并分别发起新请求，查看连接记录的实际出口；四个服务组均为 `PROXY` 时应跟随首页变化。

仓库维护者也可以在 [Actions](https://github.com/pure-white-ice-cream/shadowrocket-apple-ai-rule/actions/workflows/sync-upstream.yml) 中选择 **Sync upstream Shadowrocket rules → Run workflow** 手动同步。同步失败时可在该页面查看日志。

## 已有配置只添加 AI 规则

先在已有配置的 `[Proxy Group]` 中添加以下两个服务组及其自选节点辅助组（没有该段时，在 `[Rule]` 前创建）：

```ini
[Proxy Group]
Apple AI = select,PROXY,DIRECT,Apple AI 自选节点,policy-select-name=PROXY
ChatGPT = select,PROXY,DIRECT,ChatGPT 自选节点,policy-select-name=PROXY
Apple AI 自选节点 = select,policy-regex-filter=.*
ChatGPT 自选节点 = select,policy-regex-filter=.*
```

再复制 [AI 补丁规则](rules/apple-ai-chatgpt.list)，粘贴到已有配置 `[Rule]` 的最顶部，放在广告过滤、Apple 通用直连、Apple IP 直连、`GEOIP` 和 `FINAL` 规则之前。同时从 `[General]` 的 `skip-proxy` 中移除 `*.ls.apple.com` 和 `seed-sequoia.siri.apple.com`（如存在）。若只想沿用首页节点而不创建分组，可先把补丁中的 `,Apple AI` 和 `,ChatGPT` 替换为 `,PROXY`。

补丁不是完整配置，不要重复创建 `[Proxy Group]` 或 `[Rule]` 段，也不要将 `.list` 文件当作完整配置导入。

## 无法使用时

- **配置下载失败：** 先使用当前可用的代理连接，再重试下载链接。
- **ChatGPT 扩展不可用：** 先确认同一节点可以访问 [ChatGPT](https://chatgpt.com)，再查看扩展请求的连接记录与命中策略。网页可用仍需单独验证 Siri 扩展。
- **怀疑分流问题：** 临时将全局路由切换到“代理”做对照。如果全局代理可用而配置模式不可用，请查看失败连接的域名和规则；完成测试后恢复“配置”。
- **两种路由模式都不可用：** 检查节点出口是否受服务支持，以及设备、账号、系统版本、语言和地区是否符合使用要求。
- **网站或应用被误拦：** 查看连接记录是否命中 `REJECT`，确认具体域名后再调整规则。
- **语音功能异常：** 确认代理节点支持所需 UDP 转发，再分别测试文本与语音功能。

Siri / ChatGPT 代理规则无需解密它们的 HTTPS 流量。DNS、IPv6、URL Rewrite 和 MITM 配置沿用上游设置，实际服务可用性取决于设备条件、服务地区支持及代理节点。

## 上游与许可

上游配置来自 [Johnshall/Shadowrocket-ADBlock-Rules-Forever](https://github.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever)，作者为 Moshel 和 Johnshall。本项目添加 AI 优先规则、服务策略组及代理默认值，调整相关代理绕过设置，并自动同步上游；依据 [CC BY-SA 4.0](LICENSE) 共享。
