# Surge 原生验证状态与空组验收

状态：未执行原生 Surge 验证。当前执行环境为 Windows；GitHub Actions 只做 Surge 静态检查，不能证明 smart 空组不会直连。模板保留 smart，未添加 REJECT 成员、未替换为 fallback、未修改客户端。

## 官方约束与方案边界

- [Smart Group 官方说明](https://manual.nssurge.com/policy-groups/smart.html)：smart 接收代理成员，忽略内置策略与嵌套组。因此简单加入 REJECT 或把 REJECT 放进被复制的组，不能作为受支持的空组保护。
- [策略组官方说明](https://manual.nssurge.com/policy-groups/overview.html)：无可用成员时会使用 DIRECT，日志标识 SUBSTITUTE。本次查阅的 smart 与通用参数文档没有提供替换该行为的配置项；没有找到受支持且保留 smart 的封闭失败方案，不等于证明不存在其他方案。
- [Fallback 官方说明](https://manual.nssurge.com/policy-groups/fallback.html)：按成员优先顺序及测试可用性选路；全部测试不合格时回到首成员。切换类型会失去 smart 的实时连接质量与按站点选择体验。fallback 配 REJECT 也必须原生证明成员顺序、REJECT 可用性判定和全不可用时的实际行为，不能仅凭配置语法宣称成功。

## 所需环境与证据

仅在已有 Surge、获准操作的隔离 Mac 测试环境执行。此记录不要求安装 Surge 或自托管 runner，不修改生产配置、系统代理或现有客户端。本次没有建立这样的环境，也没有执行以下步骤。

使用 [官方 Surge Mac CLI](https://manual.nssurge.com/tools/cli.html)，先保存实际版本与对应命令帮助：

```sh
/Applications/Surge.app/Contents/Applications/surge-cli version
/Applications/Surge.app/Contents/Applications/surge-cli --help
/Applications/Surge.app/Contents/Applications/surge-cli help policy-group
/Applications/Surge.app/Contents/Applications/surge-cli help rule explain
/Applications/Surge.app/Contents/Applications/surge-cli --check /absolute/path/to/isolated-fixture.conf
```

命令可用性取决于实际版本；不以文档版本替代机器版本。`--check` 只证明配置可解析。支持 rule explain 的版本可检查决策链，但完整验收仍须受控请求及出站证据。

以真实 NET_Surge.conf 为基础创建隔离夹具，只替换两个机场的来源为本机受控测试代理与固定节点名单；保留生产组类型、前缀、地区过滤、入口及规则。记录夹具完整内容和哈希，不使用真实订阅或凭据。下列每项均需保存组成员、实际选择、决策链、连接日志及受控出口观测：

| 场景 | 要验证的结果 |
| --- | --- |
| 两机场含 GB-01、GB-London-01 与已支持地区节点 | 英国节点进入其他和全部；状态标签被过滤；正常 smart 代理仍可选 |
| 两机场非空，但选中的地区缺失 | 地区 smart 零成员时是否出现 SUBSTITUTE/DIRECT，避免把父 select 显示名称当实际出口 |
| 两机场都无节点，及名单只含状态信息 | AB/A/B 与全部入口的真实空组处理；若夹具无法解析，记录失败而不是替换场景 |
| 节点存在但代理全部不可连接 | 区分零成员与全部成员失效；检查最终连接是否直连 |
| 名单从非空刷新为空，再恢复 | 检查缓存、保存选择及 smart 临时覆写是否影响空组与恢复结果 |
| 候选封闭失败方案 | 在单独夹具验证可解析、正常代理仍工作、所有空/失败场景都无 DIRECT 出站后，才考虑迁入模板 |

验收目标：需封闭失败的入口在缺地区、双机场空、全部节点过滤空及代理全部失效时均拒绝请求；正常节点仍能代理；所有结论对应实际版本和日志。出现 SUBSTITUTE/DIRECT 即不能标为通过。

当前取舍：保留 smart 时空组行为缺口仍在；若考虑更换为 fallback，需先接受选路体验变化，再进行上述原生验证。策略类型替换尚待取舍与原生验收，本次改动仅修复状态信息过滤。