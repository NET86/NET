# NET_Mihomo v0.2

原生 Mihomo 双机场模板。机场仅提供节点，DNS、策略组和分流由本文件控制。所有可见名称保持“机场 A／机场 B”；不依赖 JavaScript，不含真实机场名称、订阅或节点凭据。

## 与 Surge 的分组对应

完整覆盖 NET_Surge 的服务类别和地区选择，不按主规则行数判断覆盖范围。保留 v0.1 的组名，避免仅为显示文字重置已有选择。

| Surge | 本模板 | 行为 |
|---|---|---|
| ✈️ 节点选择 | 节点选择 | 地区、机场、全部节点、DIRECT；新增默认自动回退 |
| 🍎 苹果服务 | Apple | 默认 DIRECT，可独立切换地区 |
| 🧠 AI 服务 | AI | 指定的 ai-daily；独立 AI 手选组；可选 DIRECT |
| 🔍 谷歌服务 | Google | Google、YouTube、YouTube Music 共用一个出口 |
| 🪟 微软服务 | Microsoft | 微软服务；GitHub 子组默认跟随 Microsoft，可独立改选 |
| 🐦 Twitter | Twitter | Twitter / X |
| 💬 Telegram | Telegram | 域名及 Telegram IP |
| 港／美／日／韩／台／新加坡／其他 | 对应 7 个地区 | 均支持地区内 A／B／AB |
| 机场 A／机场 B／全部节点 | 同名手选组 | 只接收订阅节点 |
| 广告 REJECT / FINAL | 广告过滤 / Final | 增加显式开关；广告默认 PASS，Final 默认跟随节点选择 |

所有 Surge 服务组都保留 DIRECT 与全部 7 个地区选项。默认选择不完全复制 Surge 的 DIRECT-first：除 Apple 外优先代理，AI 优先独立手选。Mihomo 的自动组使用 url-test / fallback，不能等同于 Surge smart。

## 开始使用

1. 将 `NET_Mihomo.yaml` 复制为私人副本，替换 `proxy-providers.AirportA.url` 和 `AirportB.url` 两个占位地址。使用 Clash/Mihomo 订阅，不能直接填写 Surge 配置地址。
2. 在 FlClash 导入为**新的本地配置**，选择规则模式，先保留原配置便于切回。不要绑定原来负责生成整份配置的私人覆写脚本，否则它会替换这个模板。
3. 检查 FlClash 的 **DNS 覆写**：关闭覆写，或将应用 DNS 设置同步为模板内容。端口、TUN 等客户端选项也可能覆盖 YAML；以实际生成配置为准。
4. “节点选择”默认使用自动回退，按 A、B 节点顺序选择第一个健康节点；首次健康检查前并不保证已找出可用节点。在“AI → AI 专用节点”中手选适合目标服务的稳定节点。
5. 模板 TUN 默认关闭；按需要在客户端开启。端口为 7890，DNS 监听为本机 1053，默认不允许局域网接入、不开放控制接口。

**公开模板不是开箱即可联网的订阅**：必须提供至少一个有效机场来源。首次使用需要能下载订阅，并能通过所选节点下载规则。机场订阅默认直连下载；若必须代理下载，应使用已能独立工作的另一个机场出口，避免订阅依赖自己的节点才能更新。

本地配置本身无需每天更新；机场 provider 和规则 provider 各自每 24 小时更新。FlClash 的主配置更新按钮与 provider 更新不是同一件事。模板的结构变化需重新导入私人副本，并复核保存的策略选择。

## 策略结构与默认选择

```text
AI / Google / GitHub / Microsoft / Apple / Twitter / Telegram / Final
  ├─ 节点选择：跟随公共出口
  ├─ 香港 / 台湾 / 日本 / 新加坡 / 美国 / 韩国 / 其他地区
  │   ├─ AB（自动）：本地区两机场一起测速
  │   ├─ 机场 A（自动）：只使用本地区 A 节点
  │   └─ 机场 B（自动）：只使用本地区 B 节点
  └─ 机场 A / 机场 B：手选该机场的具体节点

AI 默认 → AI 专用节点：独立手选，不与“全部节点”共享选择
节点选择默认 → 自动回退：按健康检查结果选择 A / B 节点
GitHub 默认 → Microsoft：保持 Surge 的组合，可单独改选
Apple 默认 → DIRECT
广告过滤默认 → PASS：继续匹配后续规则
其余服务、Final 默认 → 节点选择；所有服务都可手动选择 DIRECT
```

- 共 43 个策略组；21 个地区自动子组设置 `hidden: true`，显示效果取决于客户端支持。
- AI 专用节点筛选日本、美国、新加坡、台湾、韩国名称，**筛选不等于实际落地或服务可用性验证**。没有匹配节点时显示 REJECT，可在 AI 父组改选其他入口。首次需要主动手选；同名节点地址变化、订阅删除节点后也需要复核。
- 自动组选点基于测试 URL，300 秒间隔、100 ms 切换容差；不是 Surge smart，不叠加带宽，不代表账号登录、AI 解锁或业务速度测试。
- 新增“自动回退”按顺序选择健康节点，不按延迟排序，可能跨地区切换，不回退直连。它服务于默认公共出口与规则下载；AI 默认不使用它。恢复依赖健康检查结果，不保证零中断；有节点但全部失败时也不会因此直连。
- 地区内 A/B/AB 选择由引用该地区的服务共享。需要 AI 独立出口时使用 AI 专用节点。
- 空组明确回退 REJECT，避免意外直连；不会自动跨地区。误选空地区会断流，应改选有节点的组。
- 正则按节点名称分类，不能识别真实出口。仅含城市名、命名模糊或同时带中转和落地地区的节点可能漏分或重复归类，需要调整筛选。
- `全部节点` 和单机场手选组保存选择，但不自动容灾；公共默认组使用 fallback，地区自动组使用 url-test。

## AI 与规则来源

主规则共 47 条，引用 17 个远程规则集，数量不是覆盖网站数。规则下载使用独立的“自动回退”组，避免“节点选择”被手动切到空地区后连规则更新也失效。

- AI 主规则：[NET86/rules ai-daily](https://raw.githubusercontent.com/NET86/rules/stable/rules/mihomo/ai-daily.yaml)，使用 `behavior: classical`、`format: yaml`，保留域名、正则和官方语音 IP 规则。
- 2026-09-25 读取的 ai-daily 不包含 Copilot：额外引用 MetaCubeX `github-copilot.mrs`，并保留四条 Microsoft Copilot 域名规则。以后上游扩充后可复核是否仍需补充。
- 通用规则：[MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat)，按域名 / IP 分别使用原生 MRS。
- AI 在 Google、GitHub、Microsoft 之前；GitHub 默认跟随 Microsoft 并允许独立改选；YouTube 和 YouTube Music 跟随 Google。
- 局域网先直连；Windows 更新和 Steam 国内下载采用范围明确的直连规则；海外域名、国内域名、国内 IP 和 Final 依次兜底。
- 广告拦截默认关闭，选择 REJECT 后启用。AI 规则在广告规则之前。模板不保证网页、视频内嵌广告都能通过域名规则过滤。
- 不把共享验证、支付、CDN 域名整体归 AI 或 Microsoft，也不内嵌旧私人兼容层。遇到登录验证问题，应观察实际连接后补充最小例外。

这些上游内容通过 URL 引用，未打包进模板；其内容与许可证由各上游维护。NET86/rules 当前标注 AGPL-3.0-only，第三方声明见其仓库。

## DNS 与本地兼容

节点域名和直连出口采用国内 DoH，普通解析通过“节点选择”访问境外 DoH；国内域名使用国内解析。DNS 的代理出口跟随“节点选择”，不自动跟随每个业务组。

私有域名、单段主机名和内网后缀使用系统 DNS，不返回 Fake-IP；多级子域也覆盖。若系统 DNS 指向 Mihomo 自己，或开启 TUN 后出现回环，应将 `nameserver-policy` 中值为 `system` 的内网条目统一改成真实可达的路由器／内网 DNS；企业 VPN 域名需要配置其自己的解析器。模板不保证所有系统加密 DNS、应用内 DoH 或绕过代理的流量都受控。

只保留基本局域网、时间同步、联网检测、STUN 和游戏例外。它不是旧本机配置的等价迁移：私人域名、音乐兼容、PT、进程分流等没有自动搬入。需要的兼容项应在私人副本中逐项添加并记录原因，不应直接公开旧配置。

嗅探默认不改写目的地址；没有全局禁止 QUIC、没有全局跳过节点证书验证。节点自身携带的证书参数仍会保留，需单独审查。

## 机场 A 暂停订阅时使用本地节点

把该 provider 整段改为以下形式，**不要保留 `<<: *provider` 的 HTTP 参数继承**：

```yaml
proxy-providers:
  AirportA:
    type: file
    path: ./providers/airport-a-local.yaml
    health-check:
      enable: true
      url: https://www.gstatic.com/generate_204
      interval: 300
      timeout: 5000
      lazy: true
      expected-status: 204
    override:
      additional-prefix: '[A] '
  # AirportB 保留主模板中的 HTTP 配置。
```

本地文件必须包含 `proxies:` 和实际节点列表。路径相对核心工作目录，不一定是导入 YAML 所在目录；FlClash 可能重写 provider 路径，须核实实际位置。移动端不方便放置文件时，可使用 `type: inline` 与 `payload` 存放节点并删除 `path`。

本地节点包含凭据，只在私人副本保存；这种方式不会自动取得新节点。服务器地址变化、到期或撤销后必须手动更新。另一机场仍可独立在线更新。

只使用一个机场时，应删除另一个 provider，并从所有 `use` 中移除它；相应的单机场入口也应一起删除，避免留下无用选项。

## 验证与范围

本版验证结果见 `VALIDATION.md`，问题与取舍见 `REVIEW.md`。测试使用合成节点和独立目录，不代表真实机场、账号解锁、全部 UDP 场景已经验证。未替换或重启现有 FlClash。v0.1 用户需要重新确认“节点选择”和 GitHub 的保存选择；客户端可能保留旧选择而不采用新默认值。

## 设计参考

- [Mihomo 代理集合](https://wiki.metacubex.one/config/proxy-providers/)与[规则集合](https://wiki.metacubex.one/config/rule-providers/)：原生配置语义。
- [selfproxy 多订阅配置](https://github.com/yyhhyyyyyy/selfproxy/blob/main/Mihomo/mihomo_multi.yaml)：节点来源与规则分开维护。
- [666OS/YYDS](https://github.com/666OS/YYDS)：共用参数、地区筛选与复杂度控制。
- [NET Surge](https://github.com/NET86/NET/blob/main/Surge/NET_Surge.conf)：服务与地区内 A/B/AB 的操作结构。

此版本按上述结构思路编写，未复制其他项目的整份配置；没有沿用路由器专用监听或路由参数。
