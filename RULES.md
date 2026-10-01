# 公共分流规则

通用规则使用 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)；AI 使用 [NET86/rules](https://github.com/NET86/rules) 的 stable/ai-daily；国内上传例外共用 [List/UploadCN.list](List/UploadCN.list)。Copilot 使用两端相同的精确域名和服务后缀规则。

## 匹配顺序与策略

按表格顺序匹配；同一分类内的具体规则优先于通用集合。

| 顺序 | 分类 | 策略 |
| --- | --- | --- |
| 1 | 已确认的国内上传 | DIRECT |
| 2 | 单标签主机、本地网络、Lan | DIRECT |
| 3 | AI、Copilot | AI 服务，默认跟随节点选择 |
| 4 | Direct、Windows 更新与联网检测 | DIRECT |
| 5 | Advertising | 默认 REJECT |
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

节点选择由用户指定实际出口。客户端保存的手动选择优先于模板默认值；Mihomo 的广告组支持 PASS，放行后继续匹配后续规则。

## 格式映射

Surge 使用上游 `rule/Surge` 的 list；Mihomo 使用 `rule/Clash` 的 YAML。公共上传清单仅使用两端兼容的精确 DOMAIN 规则，Mihomo 以 classical/text 读取。

| 分类 | Surge | Mihomo |
| --- | --- | --- |
| Lan、Direct、YouTube、Google、GitHub、Microsoft、Twitter、Telegram、SteamCN、BiliBiliIntl | 同名 .list | 同名 .yaml，classical |
| Advertising | Advertising_All_No_Resolve.list | Advertising_Domain.yaml（domain）及 Advertising.yaml（classical） |
| Apple | Apple_All_No_Resolve.list | Apple_Classical.yaml（classical） |
| Global | Global_All_No_Resolve.list | Global_Domain.yaml（domain）及 Global.yaml（classical） |
| ChinaMax | ChinaMax_All_No_Resolve.list | ChinaMax_Domain.yaml（domain）、ChinaMax.yaml（classical）、ChinaMax_IP.yaml（ipcidr） |
| AI | rules/surge/ai-daily.list | rules/mihomo/ai-daily.yaml（classical） |

Mihomo 的 domain/ipcidr 集合承担大批量匹配，classical 集合补充关键词、进程、IP 等规则。两端统一分类、顺序和策略；官方适配清单的具体规则随引擎能力不同，Surge 的 USER-AGENT、URL-REGEX 不直接导入 Mihomo。单标签主机在 Surge 由 exclude-simple-hostnames 处理，在 Mihomo 由 DOMAIN-REGEX 处理。

Mihomo 的上传清单同时用于国内 DNS 策略，通过 AliDNS / DNSPod DIRECT DoH 解析。客户端需保留该 DNS 策略，避免上传域名被境外解析结果带到代理出口。Surge 的 DNS 由其 General 设置与系统 DNS 控制。
