# NET Mihomo

双机场 Mihomo 配置模板。仓库仅使用“机场 A／机场 B”占位来源，不包含真实机场订阅或节点凭据。

当前模板版本：**v0.8（2026-10-07）**。机场 provider 只过滤完整的“状态字段 + 分隔符 + 流量数值及单位／到期日期／重置时长”，以及明确的官网、导航页、机场公告标签（可带 URL）；数值或日期后仍有节点描述时保留，不因 Traffic、Expire、官网等单词或前缀直接删除。未明确识别的格式（例如单独的 `100 GB`）保守保留。名称若恰好完整等于这些状态格式仍会被排除，需要调整节点名或私人副本过滤规则。资源下载组继续复用机场 provider 的健康状态；日常日志为 info，进程识别为 strict。广告配置继续停用，国外业务共用 DoH，只有 AI / Copilot 保留跟随 AI 组的 DNS 例外；AnyTLS 保留默认连接复用行为。

## 使用

1. 将 `NET_Mihomo.yaml` 复制到私人配置，填写 `AirportA`、`AirportB` 的订阅地址；至少配置一个有效来源。
2. 在 FlClash 中导入私人副本。客户端可能覆写 DNS、TUN 和系统代理设置，导入后以实际生成配置为准。
3. 在 `节点选择` 中选择 DIRECT、地区、机场或全部节点。每个地区均有 AB、机场 A、机场 B 自动组；辅助组隐藏。
4. `资源下载` 是隐藏的 fallback 组，仅供规则集等内部资源下载，不承载普通业务流量。只引用两个机场 provider，省略组级检测字段，使用第一个 provider 的健康检查 URL 及各节点对应的健康状态。两个 provider 保留原有健康检查。旧配置与 provider 使用相同检测 URL 时，核心已去重；此次精简不承诺减少检测次数。

## 分流

服务组保留 Apple、AI、Google、Microsoft、Twitter、Telegram。AI 首次使用默认跟随 `节点选择`；GitHub 规则进入 Microsoft；未命中规则的流量进入 `节点选择`。客户端保存的手动选择优先于模板默认值。

`广告过滤` 分组、`Ads` / `Ads-Extra` 规则源及两条对应规则均已注释。PASS 只表示继续匹配后续规则，不会停止规则源下载和加载；暂不拦截广告时完整停用可减少无用资源占用。恢复广告过滤需同时取消这三处注释；公共模板恢复后首次默认 REJECT，已有客户端选择可能优先。Surge 的广告配置保持原样。

AI 规则使用 [NET86/rules 的 ai-daily](https://raw.githubusercontent.com/NET86/rules/stable/rules/mihomo/ai-daily.yaml)，其中已包含 Microsoft/GitHub Copilot；NET 模板不重复加载两份厂商包，上游独立包仍保留。Copilot 遥测保持显式走 AI。通用规则使用 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) 的官方 Clash 适配格式。两端分类、顺序、策略和格式映射见[公共分流说明](../RULES.md)。规则源及节点服务的可用性由上游提供方决定。

升级模板后，请手动刷新 ai-daily 规则资源并重新加载配置，确认客户端缓存包含新增 Copilot 域名。

## DNS 与 AnyTLS

DNS 按用途收敛：国内域名使用国内直连 DoH，普通国外域名共用 `节点选择` 出口的 Cloudflare / Google DoH；只有 AI / Copilot 通过 `AI` 组查询相同的国外解析器。Apple、Google、Microsoft、Twitter、Telegram 等不再各自绑定 DNS 出口，业务分流规则和各组选择不变。

同类国内规则合并引用，共用列表通过 YAML 锚点复用；国内上传优先于 AI，AI 优先于通用直连规则，Copilot 遥测仍显式跟随 AI。节点域名及实际 DIRECT 出站连接使用国内直连 DNS，`direct-nameserver-follow-policy: false` 防止 DIRECT 出站受代理业务 DNS 策略影响。内网域名的普通 DNS 查询保留 `system`；如果系统 DNS 指向本核心，需要配置真实的内网 DNS，避免回环。DIRECT 出站解析不跟随这些内网策略，需要企业内网解析时应另行配置直连 DNS 或 hosts。

代理业务组选择 DIRECT 时，普通真实 DNS 查询中的海外 DoH 也会直连，可能在当前网络不可达；服务组的 DoH 出口与业务连接分别选择节点，自动组不能保证两者每次使用同一节点。

模板不覆盖 `disable-reuse`，允许 AnyTLS 使用其默认会话复用机制；不强制修改上游节点的证书验证、空闲会话参数等字段。

FlClash 的界面设置可能覆盖模板中的 `log-level: info` 和 `find-process-mode: strict`。核心的 strict 保留按需进程识别；FlClash 0.8.98 的客户端枚举只有 always/off，读取 strict 会退回 always，不能仅修改偏好文件就宣称客户端持久采用了 strict。没有进程规则时可按用户选择关闭进程识别；以后新增进程规则需重新开启。fake-IP 例外按明确兼容需求保留，不能仅凭名单长度删除；局域网、NTP、STUN、Windows 联网检测及游戏机相关例外继续保留。删除本地 AI 补充规则前应核对当前 ai-daily 已实际加载并覆盖相同规则，两条 Copilot 遥测规则继续显式保留。

现有 AB 自动组继续使用 `url-test`，不增加日本主备组。节点及订阅健康检查保持 300 秒、`lazy: true`、5000 毫秒超时，地址为 `https://www.gstatic.com/generate_204`，预期状态码为 204；自动组容差为 100 毫秒，`max-failed-times` 沿用默认 5。检查只能判断检测地址的连通性，不能证明 AI 账号、地区或模型请求可用，也不会迁移已建立的连接。

## 验证

填写有效订阅后，用 Mihomo `-t` 检查配置，并以 FlClash 实际运行配置和连接测试验收。CI 另用固定 MaxMind 测试库验证 `IP-ASN` 的内核识别与真实数据面命中；匹配与兜底都使用本地 `REJECT`，不会因测试失败产生公网出站，也不依赖实时 BGP 数据。模板中的占位订阅不能直接使用。

## 国内上传直连

公共规则文件为 [`List/UploadCN.list`](../List/UploadCN.list)，Surge 与 Mihomo 共用。
Mihomo 使用 `classical/text` 格式，通过 `资源下载` 更新，缓存位于 `./rules/upload-cn.list`，更新周期为 24 小时。

上传规则优先于广告及通用分流；相同规则集用于 `nameserver-policy`，通过 AliDNS / DNSPod 的 DIRECT DoH 解析。
在 FlClash 中关闭 DNS 覆写，或在覆写设置中保留相同策略；以实际生成配置为准。

清单使用精确域名匹配，只维护国内上传服务；新增条目需确认用途，不加入整站后缀或境外服务。
仓库仅保存公共规则和无凭证模板；填写真实订阅后的私人配置不应公开。
