# NET Mihomo

双机场 Mihomo 配置模板。仓库仅使用“机场 A／机场 B”占位来源，不包含真实机场订阅或节点凭据。

当前模板版本：**v0.3（2026-10-04）**。业务 DoH 跟随对应服务策略组，AnyTLS 保留节点默认的连接复用行为。

## 使用

1. 将 `NET_Mihomo.yaml` 复制到私人配置，填写 `AirportA`、`AirportB` 的订阅地址；至少配置一个有效来源。
2. 在 FlClash 中导入私人副本。客户端可能覆写 DNS、TUN 和系统代理设置，导入后以实际生成配置为准。
3. 在 `节点选择` 中选择 DIRECT、地区、机场或全部节点。每个地区均有 AB、机场 A、机场 B 自动组；辅助组隐藏。
4. `资源下载` 是隐藏的 fallback 组，仅供规则集等内部资源下载，不承载普通业务流量。

## 分流

服务组保留 Apple、AI、Google、Microsoft、Twitter、Telegram。AI 首次使用默认跟随 `节点选择`；GitHub 规则进入 Microsoft；未命中规则的流量进入 `节点选择`。`广告过滤` 首次使用默认 REJECT；选择 PASS 后继续匹配后续规则。客户端保存的手动选择优先于模板默认值。

AI 规则使用 [NET86/rules 的 ai-daily](https://raw.githubusercontent.com/NET86/rules/stable/rules/mihomo/ai-daily.yaml)，其中已包含 Microsoft/GitHub Copilot；NET 模板不重复加载两份厂商包，上游独立包仍保留。Copilot 遥测保持显式走 AI。通用规则使用 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) 的官方 Clash 适配格式。两端分类、顺序、策略和格式映射见[公共分流说明](../RULES.md)。规则源及节点服务的可用性由上游提供方决定。

升级模板后，请手动刷新 ai-daily 规则资源并重新加载配置，确认客户端缓存包含新增 Copilot 域名。

## DNS 与 AnyTLS

DNS 策略沿用域名分流顺序：AI → AI，Google / YouTube → Google，GitHub / Microsoft → Microsoft，Twitter、Telegram、Apple 各自使用对应策略组。未分类域名仍通过 `节点选择` 解析。

AI 等代理业务使用 Cloudflare / Google DoH；Apple 使用国内 AliDNS / DNSPod DoH 并跟随 Apple 策略组。节点域名及实际 DIRECT 出站连接使用国内直连 DNS，`direct-nameserver-follow-policy: false` 防止 DIRECT 出站受代理业务 DNS 策略影响。内网域名的普通 DNS 查询保留 `system`；如果系统 DNS 指向本核心，需要配置真实的内网 DNS，避免回环。DIRECT 出站解析不跟随这些内网策略，需要企业内网解析时应另行配置直连 DNS 或 hosts。

代理业务组选择 DIRECT 时，普通真实 DNS 查询中的海外 DoH 也会直连，可能在当前网络不可达；服务组的 DoH 出口与业务连接分别选择节点，自动组不能保证两者每次使用同一节点。

模板不覆盖 `disable-reuse`，允许 AnyTLS 使用其默认会话复用机制；不强制修改上游节点的证书验证、空闲会话参数等字段。

## 验证

填写有效订阅后，用 Mihomo `-t` 检查配置，并以 FlClash 实际运行配置和连接测试验收。模板中的占位订阅不能直接使用。

## 国内上传直连

公共规则文件为 [`List/UploadCN.list`](../List/UploadCN.list)，Surge 与 Mihomo 共用。
Mihomo 使用 `classical/text` 格式，通过 `资源下载` 更新，缓存位于 `./rules/upload-cn.list`，更新周期为 24 小时。

上传规则优先于广告及通用分流；相同规则集用于 `nameserver-policy`，通过 AliDNS / DNSPod 的 DIRECT DoH 解析。
在 FlClash 中关闭 DNS 覆写，或在覆写设置中保留相同策略；以实际生成配置为准。

清单使用精确域名匹配，只维护国内上传服务；新增条目需确认用途，不加入整站后缀或境外服务。
仓库仅保存公共规则和无凭证模板；填写真实订阅后的私人配置不应公开。
