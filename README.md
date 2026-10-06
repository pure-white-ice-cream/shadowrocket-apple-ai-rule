# Shadowrocket：Siri / Apple Intelligence 与 ChatGPT

本仓库提供两种使用方式，不包含代理节点、订阅或凭据。所有 `PROXY` 流量使用 Shadowrocket 中你选择的代理节点。

## 推荐：补丁加入现有配置

复制 `rules/apple-ai-chatgpt.list` 的内容，粘贴到原配置的 `[Rule]` 下一行，位于所有 `IP-CIDR,17.0.0.0/8,DIRECT`、Apple IPv6 直连、Apple 通用域名直连、`GEOIP` 和 `FINAL` 规则之前。不要新增第二个 `[Rule]` 段，不要把 `.list` 当作完整配置导入。原有国内、Google、Telegram 等规则可以继续保留。

Shadowrocket 按顺序匹配，前面的规则优先。补丁将原有 Apple AI / Siri 代理规则去重并前置，补充 `chatgpt.com` 等核心域名。根据用户重新提供的准确域名，原 OCR 的 `Is.apple.com` 应为 `ls.apple.com`，`gspe1-ssl.Is.apple.com` 应为 `gspe1-ssl.ls.apple.com`，`apps.mastic.com` 应为 `apps.mzstatic.com`。已同步修正补丁和完整配置，并明确列出 `gspe1-ssl.ls.apple.com`。`apps.mzstatic.com,PROXY` 位于通用 `mzstatic.com,DIRECT` 之前，避免被直连规则覆盖。未获准确清单支持的 `apple-relay.tasty-edge.com` 已移除；原有 `apple-relay.akamaized.net` 作为额外兼容规则保留，不属于本次用户确认的 17 个域名。

原配置已有 `FINAL,PROXY`，且一部分 Apple relay 规则已经在 Apple IP 直连规则之前。因此不能仅凭缺少 `chatgpt.com` 或规则顺序断言扩展失败原因；补丁是分流修正与诊断起点。

## 独立对照配置

`shadowrocket-apple-ai.conf` 是可导入的精简完整配置，保留源文件的 General 设置，加入上述优先代理规则、Apple 通用直连、局域网直连、中国 GeoIP 直连和最终代理。它不包含原文件其他站点的逐条分流规则；如需保留这些规则，请使用上面的补丁方式。

备份原配置，导入并启用配置，将“全局路由”设为“配置”，选择可用的代理节点。配置文件自身不会提供代理服务器。

## 手机上验证

1. 先确认节点能打开 `https://chatgpt.com`。网页可用只能证明网页访问，不等于 Siri 扩展已经可用。
2. 打开 Shadowrocket 连接记录，再进入“设置 → Apple Intelligence 与 Siri → ChatGPT”，测试设置扩展和一次“询问 ChatGPT”。记录失败时的目标域名、命中规则、策略、时间及错误信息。对外分享日志前删除账号、令牌等敏感信息。
3. 对比同一节点下“配置”与“代理”全局路由模式。若全局代理可用而配置模式失败，优先排查分流遗漏；若两者都失败，继续排查节点出口、服务可用性及设备资格。测试后恢复“配置”模式。
4. 核对系统版本、设备支持情况、语言和地区，以及 Apple Intelligence / ChatGPT 扩展在当前地区的可用性。代理规则不会改变设备、账号或服务的资格限制。
5. 文本扩展先测试 TCP。语音等功能可能使用 UDP，节点需支持相应转发。默认保留 `udp-policy-not-supported-behaviour = REJECT`；不要用 UDP 直连回退来掩盖代理不支持 UDP 的问题，也不要默认开启全局 UDP/443 封锁。

无需安装 MITM 证书或解密 Apple / ChatGPT 的 HTTPS 流量。保留源配置的 DNS 与 IPv6 设置；若日志显示解析或 IPv6 连接失败，再分别做单变量对照测试。

## 参考与验证范围

- 用户提供的源配置和随后更正的 17 个域名。
- 已读取的参考配置：<https://github.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever/blob/release/lazy_group.conf>。其 AI 段包含 `apps.mzstatic.com`、`smoot.apple.com`、`gspe1-ssl.ls.apple.com`、三个 Apple relay 域名、`cp4.cloudflare.com` 和 `guzzoni.apple.com`；这些 AI 规则及 OpenAI RULE-SET 默认均被注释，复制整份配置不会自动启用它们。其 `AI` 是已定义的策略组，本仓库使用 `PROXY`，无需复制分组定义。
- Apple 官方参考：<https://support.apple.com/zh-cn/101555>。

生成时云环境请求 Apple 页面返回 HTTP 403，未能实时核验官方域名清单。Apple AI 条目按用户准确清单更正，并与上述社区配置交叉核对；不能把这里的列表视作已核实的最新官方完整清单。ChatGPT 通用网站域名也不代表 Apple 内置扩展一定会直接连接这些域名。

云端仅进行文件结构、域名规则、去重和代表性规则顺序检查，无法运行 iOS Shadowrocket、验证代理节点，或证明真实设备上的 Siri / ChatGPT 扩展可用。实际失败原因需通过上述设备连接记录确认。
