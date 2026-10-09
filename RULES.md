# 公共分流规则

通用规则使用 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)；AI 使用 [NET86/rules](https://github.com/NET86/rules) 的 stable/ai-daily；国内上传例外共用 [List/UploadCN.list](List/UploadCN.list)。Copilot 已由 stable/ai-daily 完整覆盖，优先于通用 Microsoft/GitHub；NET 模板不重复加载两份厂商包，上游独立包仍保留。两条 Copilot 遥测域名保持显式走 AI。

升级模板后，请在 Surge / Mihomo 客户端手动刷新 ai-daily 规则资源并重新加载配置，确认旧缓存已更新。

## 匹配顺序与策略

按表格顺序匹配；同一分类内的具体规则优先于通用集合。

| 顺序 | 分类 | 策略 |
| --- | --- | --- |
| 1 | 已确认的国内上传 | DIRECT |
| 2 | 单标签主机、本地网络、Lan | DIRECT |
| 3 | AI、Copilot | AI 服务，默认跟随节点选择 |
| 4 | Direct、Windows 更新与联网检测 | DIRECT |
| 5 | Advertising | Surge 默认 REJECT；Mihomo 已注释停用 |
| 6 | Apple | 苹果服务，默认 DIRECT |
| 7 | YouTube、Google | 谷歌服务，默认跟随节点选择 |
| 8 | GitHub、Microsoft | 微软服务，默认跟随节点选择 |
| 9 | Twitter | Twitter，默认跟随节点选择 |
| 10 | Telegram | Telegram，默认跟随节点选择 |
| 11 | SteamCN | DIRECT |
| 12 | BiliBiliIntl | 节点选择 |
| 13 | Global | 节点选择 |
| 14 | ChinaMax、CN GeoIP | DIRECT |
| 15 | 未命中 | 节点选择 |

节点选择由用户指定实际出口。客户端保存的手动选择优先于模板默认值。Mihomo v0.5 已一并注释广告分组、对应规则和规则源；恢复后 PASS 表示继续匹配后续规则，但规则源仍下载和加载。Surge 广告配置保持原样。

## 格式映射

Surge 使用上游 `rule/Surge` 的 list；Mihomo 使用 `rule/Clash` 的 YAML。公共上传清单仅使用两端兼容的精确 DOMAIN 规则，Mihomo 以 classical/text 读取。

| 分类 | Surge | Mihomo |
| --- | --- | --- |
| Lan、Direct、YouTube、Google、GitHub、Microsoft、Twitter、Telegram、SteamCN、BiliBiliIntl | 同名 .list | 同名 .yaml，classical |
| Advertising | Advertising_All_No_Resolve.list | Advertising_Domain.yaml（domain）及 Advertising.yaml（classical），已注释 |
| Apple | Apple_All_No_Resolve.list | Apple_Classical.yaml（classical） |
| Global | Global_All_No_Resolve.list | Global_Domain.yaml（domain）及 Global.yaml（classical） |
| ChinaMax | ChinaMax_All_No_Resolve.list | ChinaMax_Domain.yaml（domain）、ChinaMax.yaml（classical）、ChinaMax_IP.yaml（ipcidr） |
| AI | rules/surge/ai-daily.list | rules/mihomo/ai-daily.yaml（classical） |

Mihomo 的 domain/ipcidr 集合承担大批量匹配，classical 集合补充关键词、进程、IP 等规则。除 Mihomo 暂停广告过滤外，两端分类、顺序和策略保持对应；官方适配清单的具体规则随引擎能力不同，Surge 的 USER-AGENT、URL-REGEX 不直接导入 Mihomo。单标签主机在 Surge 由 exclude-simple-hostnames 处理，在 Mihomo 由 DOMAIN-REGEX 处理。

Mihomo 的上传清单同时用于国内 DNS 策略，通过 AliDNS / DNSPod DIRECT DoH 解析。客户端需保留该 DNS 策略，避免上传域名被境外解析结果带到代理出口。Surge 的 DNS 由其 General 设置与系统 DNS 控制。

## 模板检查

两端地区过滤统一忽略大小写，国家代码及 Hong、Hong Kong、HongKong、Tai、Taiwan、Taipei 别名以字母数字边界识别；`US-01` 归美国，`AUS-Sydney`、`Thailand`、`Thai-Bangkok`、`Chongqing` 归其他地区。保留中文、旗帜和 States 等既有别名。名称同时含多个地区仍需人工调整。

Surge 的其他地区及全部节点仅排除明确的状态字段格式（如 `剩余流量：10 GB`、`Expire: 日期`）或纯流量值（如 `100 GB`），支持机场 A/B 的既定名称前缀。名称中的裸 `GB`、Traffic 等不视为状态，`GB-01`、`GB-London-01` 保留为其他地区；未识别的状态格式需按实际订阅调整。此项由固定节点/状态表同时检查两个机场前缀与全部节点过滤。

GitHub Actions 直接读取真实模板，检查安全默认值、固定地区表、引用、规则顺序及上传 DNS 策略；再仅替换订阅与规则下载方式，注入虚拟双机场节点，以固定版本 Mihomo `-t` 和控制器检查实际组成员、空组 REJECT、首次默认策略与已加载规则。公网规则引用在 CI 下载核对；AI 合集与厂商包先绑定同一个 stable 提交，再按不可变地址读取，避免跨发布版本造成误报，不改变客户端订阅地址。DNS 检查覆盖配置与核心加载，不验证真实解析或客户端覆写；虚拟节点不验证实际连接质量。Surge 只有静态检查，尚未原生验证。

Surge smart 空组行为尚未实现与 Mihomo REJECT 一致的封闭失败。受支持方案调查与待执行原生验收见 [Surge 验证记录](Surge/VALIDATION.md)。
