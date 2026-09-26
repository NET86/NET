# NET Mihomo

双机场 Mihomo 配置模板。仓库仅使用“机场 A／机场 B”占位来源，不包含真实机场订阅或节点凭据。

## 使用

1. 将 `NET_Mihomo.yaml` 复制到私人配置，填写 `AirportA`、`AirportB` 的订阅地址；至少配置一个有效来源。
2. 在 FlClash 中导入私人副本。客户端可能覆写 DNS、TUN 和系统代理设置，导入后以实际生成配置为准。
3. 在 `节点选择` 中选择 DIRECT、地区、机场或全部节点。每个地区均有 AB、机场 A、机场 B 自动组；辅助组隐藏。
4. `资源下载` 是隐藏的 fallback 组，仅供规则集等内部资源下载，不承载普通业务流量。

## 分流

服务组保留 Apple、AI、Google、Microsoft、Twitter、Telegram。AI 首次使用默认跟随 `节点选择`；GitHub 规则进入 Microsoft；未命中规则的流量进入 `节点选择`。`广告过滤` 默认 PASS，选择 REJECT 后拦截匹配的广告规则。

AI 规则使用 [NET86/rules 的 ai-daily](https://raw.githubusercontent.com/NET86/rules/stable/rules/mihomo/ai-daily.yaml)。其他规则集由配置中的 rule-provider URL 获取；规则源及节点服务的可用性由上游提供方决定。

## 验证

填写有效订阅后，用 Mihomo `-t` 检查配置，并以 FlClash 实际运行配置和连接测试验收。模板中的占位订阅不能直接使用。
