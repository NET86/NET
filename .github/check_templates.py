"""CI-only checks: read shipping templates; never read private subscriptions."""

import copy
import ipaddress
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "Mihomo/NET_Mihomo.yaml").read_text(encoding="utf-8"))
SURGE = (ROOT / "Surge/NET_Surge.conf").read_text(encoding="utf-8")
REGIONS = {"hk": "香港", "tw": "台湾", "jp": "日本", "sg": "新加坡", "us": "美国", "kr": "韩国"}
COPILOT_CORE_RULES = {
    "DOMAIN,copilot.ai",
    "DOMAIN-SUFFIX,copilot-stg.com",
    "DOMAIN-SUFFIX,copilot.cloud.microsoft",
    "DOMAIN-SUFFIX,copilot.com",
    "DOMAIN-SUFFIX,copilot.microsoft.com",
    "DOMAIN,copilot-proxy.githubusercontent.com",
    "DOMAIN,copilot-workspace.githubnext.com",
    "DOMAIN,copilotprodattachments.blob.core.windows.net",
    "DOMAIN,origin-tracker.githubusercontent.com",
    "DOMAIN-SUFFIX,githubcopilot.com",
}
# Fixed expectations include both clients' original aliases, not generated from regexes.
CASES = {
    "香港": ["HK-01", "hk-01", "香港", "🇭🇰", "Hong", "Hong Kong", "HongKong", "hong", "Hong-01", "HongKong-01"],
    "台湾": ["TW-01", "tw-01", "台湾", "台灣", "🇹🇼", "Taiwan", "Tai", "Taipei", "tai", "Tai-01", "Taiwan-01", "Taipei-01"],
    "日本": ["JP-01", "jp-01", "日本", "🇯🇵", "Japan"],
    "新加坡": ["SG-01", "sg-01", "新加坡", "狮城", "獅城", "🇸🇬", "Singapore"],
    "美国": ["US-01", "us-01", "_US_", "USA-01", "usa-01", "美国", "美國", "🇺🇸", "United States", "States"],
    "韩国": ["KR-01", "kr-01", "韩国", "韓國", "🇰🇷", "Korea"],
    "其他地区": ["AUS-Sydney", "aus-sydney", "RUS-01", "DE-01", "CUS-01", "US01", "XHK-01", "XJP-01", "XSG-01", "XTW-01", "XKR-01", "Thailand", "Thai-Bangkok", "Chongqing", "chongqing-01", "XHong", "HongX", "XHongKong", "HongKongX", "XTai", "TaiX", "XTaiwan", "TaiwanX", "XTaipei", "TaipeiX", "GB-01", "GB-London-01", "London-GB-02"],
}
SURGE_OTHER_NAMES = ["Traffic-Node-01", "Expire-Node-01", "官网线路-01", "套餐专线-01", "更新线路-01"]
MIHOMO_PROVIDER_VALID_NAMES = [
    "Traffic-Node-01", "Expire-Node-01", "Remaining-Pool-HK", "Reset-US-01",
    "官网线路-01", "机场官网线路", "MyTraffic: Fast", "100 GB",
    "Traffic 4 JP", "Traffic: 100 GB Tokyo", "Expire: 2026-12-31 JP",
    "剩余流量：10 Gbps专线", "机场 A-官网: 官网线路", "Traffic100GB", "Remaining 3 JP",
]
MIHOMO_PROVIDER_STATUS_NAMES = [
    "剩余流量：10 GB", "机场 A-剩余流量: 100GB", "套餐到期：2026-12-31",
    "距离下次重置: 3天", "到期时间: 2026-12-31", "机场 B-流量: 100GB",
    "Remaining Traffic: 100 GB", "机场 A-Traffic: 100 GB", "Expire: 2026-12-31",
    "Reset 3 days", "官网", "机场 B-官网", "导航页", "机场公告",
    "Traffic: 10 GiB / 100 GiB", "机场 B-官网: https://example.com",
    "Expire: 2026-12-31 23:59:00Z",
]
# Only explicit status/traffic formats are metadata; tokens inside node names are not.
STATUS_NAMES = [
    "剩余流量：10 GB", "流量: 100GB", "套餐到期：2026-12-31", "距离下次重置: 3天",
    "到期时间: 2026-12-31", "Remaining Traffic: 100 GB", "Traffic: 100 GB",
    "Expire: 2026-12-31", "Reset: 3 days", "100 GB", "12.5GB",
    "导航: https://example.com", "官网: https://example.com", "更新: 请更新订阅", "套餐: 示例",
]


def lines(text):
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def fetch(url):
    with urlopen(url, timeout=60) as response:
        return response.read()


def static_checks():
    assert "skip-server-cert-verify = false" in lines(SURGE)
    assert "skip-server-cert-verify = true" not in lines(SURGE)
    groups = {g["name"]: g for g in CONFIG["proxy-groups"]}
    assert len(groups) == len(CONFIG["proxy-groups"])
    builtins = {"DIRECT", "REJECT", "PASS"}
    for g in groups.values():
        assert set(g.get("proxies", [])) <= groups.keys() | builtins, g["name"]
        assert set(g.get("use", [])) <= CONFIG["proxy-providers"].keys(), g["name"]
        if "use" in g:
            assert g["empty-fallback"] == "REJECT", g["name"]
    for name, default in {"AI": "节点选择", "Apple": "DIRECT", "节点选择": "DIRECT"}.items():
        g = groups[name]
        assert g.get("default-selected", g["proxies"][0]) == default
    assert "广告过滤" not in groups
    resource = groups["资源下载"]
    assert set(resource) == {"name", "type", "use", "empty-fallback", "hidden"}
    assert resource["type"] == "fallback" and resource["hidden"] is True
    for provider in CONFIG["proxy-providers"].values():
        hc = provider["health-check"]
        assert (hc["enable"], hc["interval"], hc["timeout"], hc["lazy"], hc["expected-status"]) == (True, 300, 5000, True, 204)
    provider_filter = CONFIG["x-provider"]["exclude-filter"]
    assert all(not re.search(provider_filter, name) for name in MIHOMO_PROVIDER_VALID_NAMES)
    assert all(re.search(provider_filter, name) for name in MIHOMO_PROVIDER_STATUS_NAMES)
    assert not {"Ads", "Ads-Extra"} & CONFIG["rule-providers"].keys()
    assert not any(",广告过滤" in rule or rule.startswith(("RULE-SET,Ads,", "RULE-SET,Ads-Extra,")) for rule in CONFIG["rules"])
    for provider in CONFIG["proxy-providers"].values():
        assert provider["url"].startswith("https://example.com/REPLACE_")
    assert re.findall(r"policy-path=([^,\s]+)", SURGE) == [
        "https://example.com/airport-A.conf", "https://example.com/airport-B.conf"]
    surge_groups = SURGE.split("[Proxy Group]", 1)[1].split("[Rule]", 1)[0]
    for key, region in REGIONS.items():
        pattern = CONFIG[f"x-{key}"]
        filters = re.findall(rf"^.*{region}·.*policy-regex-filter=(.*)$", surge_groups, re.M)
        assert len(filters) == 3 and all(p == pattern for p in filters), region
        for expected, names in CASES.items():
            for name in names:
                assert bool(re.search(pattern, name)) == (expected == region), (region, name)
    other_filters = re.findall(r"^.*其他·.*policy-regex-filter=(.*)$", surge_groups, re.M)
    assert len(other_filters) == 3
    all_filters = re.findall(r"^🌐 全部节点 = .*policy-regex-filter=(.*)$", surge_groups, re.M)
    assert len(all_filters) == 1
    filter_failures = []
    for region, names in [*CASES.items(), ("其他地区", SURGE_OTHER_NAMES)]:
        for name in names:
            assert bool(re.search(CONFIG["x-known-regions"], name)) == (region != "其他地区"), name
            for prefix in ["", "机场 A-", "机场 B-"]:
                for group, patterns, expected in [
                    ("其他地区", other_filters, region == "其他地区"), ("全部节点", all_filters, True)
                ]:
                    if not all(bool(re.search(p, prefix + name)) == expected for p in patterns):
                        filter_failures.append((group, prefix + name, expected))
    for name in STATUS_NAMES:
        for prefix in ["", "机场 A-", "机场 B-"]:
            for group, patterns in [("其他地区", other_filters), ("全部节点", all_filters)]:
                if any(re.search(p, prefix + name) for p in patterns):
                    filter_failures.append((group, prefix + name, False))
    assert not filter_failures, filter_failures
    print("Surge other/all filters: fixed node and status tables with both airport prefixes passed")
    surge_rules = lines(SURGE.split("[Rule]", 1)[1].split("[MITM]", 1)[0])
    rules = CONFIG["rules"]
    assert rules[0] == "RULE-SET,UploadCN,DIRECT"
    upload_url = CONFIG["rule-providers"]["UploadCN"]["url"]
    assert surge_rules[0] == f"RULE-SET,{upload_url},DIRECT"
    upload = lines((ROOT / "List/UploadCN.list").read_text(encoding="utf-8"))
    assert upload and all(re.fullmatch(r"DOMAIN,[a-z0-9.-]+", r) for r in upload)
    dns = CONFIG["dns"]
    assert dns["nameserver-policy"]["rule-set:UploadCN"] == [
        "https://dns.alidns.com/dns-query#DIRECT", "https://doh.pub/dns-query#DIRECT"]
    assert dns["direct-nameserver-follow-policy"] is False
    assert all(s.endswith("#节点选择") for s in dns["nameserver"])
    policy = dns["nameserver-policy"]
    assert policy["rule-set:AI-Daily"] == [
        "https://1.1.1.1/dns-query#AI", "https://8.8.8.8/dns-query#AI"]
    domestic_key = "rule-set:Direct,SteamCN,China,China-Extra"
    cn_dns = ["https://dns.alidns.com/dns-query#DIRECT", "https://doh.pub/dns-query#DIRECT"]
    assert policy[domestic_key] == dns["direct-nameserver"] == dns["proxy-server-nameserver"] == cn_dns
    # Ordinary foreign services inherit nameserver rather than each pinning an exit.
    for name in ["Apple", "YouTube", "Google", "GitHub", "Microsoft", "Twitter", "Telegram", "BiliIntl", "Global", "Global-Extra"]:
        assert f"rule-set:{name}" not in policy, name
    assert "+.appstore.com" not in policy
    for key in ["rule-set:Private", "*", "localhost", "+.lan", "+.local", "+.home.arpa", "+.localdomain", "+.internal"]:
        assert policy[key] == "system", key
    order = list(policy)
    assert order.index("rule-set:UploadCN") < order.index("rule-set:AI-Daily") < order.index(domestic_key)
    for host in ["copilot-telemetry-service.githubusercontent.com", "copilot-telemetry.githubusercontent.com"]:
        assert policy[host] == policy["rule-set:AI-Daily"]
        assert order.index(host) < order.index(domestic_key)
    dns_groups = groups.keys() | builtins
    for key, resolvers in policy.items():
        if key.startswith("rule-set:"):
            assert set(key.removeprefix("rule-set:").split(",")) <= CONFIG["rule-providers"].keys(), key
        for resolver in [resolvers] if isinstance(resolvers, str) else resolvers:
            if "#" in resolver:
                assert resolver.split("#", 1)[1] in dns_groups, (key, resolver)
    for g in groups.values():
        if g["type"] == "url-test":
            assert (g["interval"], g["timeout"], g["tolerance"], g["lazy"], g["expected-status"], g.get("max-failed-times", 5)) == (300, 5000, 100, True, 204, 5)
    for provider in CONFIG["proxy-providers"].values():
        assert "disable-reuse" not in provider.get("override", {})
        assert not provider.get("override", {}).get("override-expr")
    assert rules[-1] == "MATCH,节点选择"
    # All provider/group references must resolve, in the actual ordered rule array.
    for rule in rules:
        parts = rule.split(",")
        policy = parts[-2] if parts[-1] == "no-resolve" else parts[-1]
        assert policy in groups or policy in builtins, rule
        if parts[0] == "RULE-SET":
            assert parts[1] in CONFIG["rule-providers"], rule
    ai_names = ["AI-Daily"]
    for name in ai_names:
        provider = CONFIG["rule-providers"][name]
        assert provider["behavior"] == "classical" and provider["format"] == "yaml"
        url = provider["url"].replace("/mihomo/", "/surge/").replace(".yaml", ".list")
        ai_rule = f"RULE-SET,{name},AI"
        surge_rule = f"RULE-SET,{url},🧠 AI 服务"
        for target in ["Direct", "GitHub", "Microsoft"]:
            policy = "DIRECT" if target == "Direct" else "Microsoft"
            assert rules.index(ai_rule) < rules.index(f"RULE-SET,{target},{policy}")
        for target in ["Direct/Direct.list", "Advertising/Advertising_All_No_Resolve.list", "GitHub/GitHub.list", "Microsoft/Microsoft.list"]:
            index = next(i for i, rule in enumerate(surge_rules) if target in rule)
            assert surge_rules.index(surge_rule) < index
    for host in ["copilot-telemetry-service.githubusercontent.com", "copilot-telemetry.githubusercontent.com"]:
        assert rules.index(f"DOMAIN,{host},AI") < rules.index("RULE-SET,GitHub,Microsoft")
        assert surge_rules.index(f"DOMAIN,{host},🧠 AI 服务") < next(i for i, r in enumerate(surge_rules) if "Advertising/" in r)
    assert "RULE-SET,GitHub,Microsoft" in rules and "RULE-SET,Microsoft,Microsoft" in rules
    print("Safety defaults, region table, references, upload DNS and rule ordering: passed")


def provider_payload(name, provider, content):
    """Return source entries the declared provider can load without semantic loss."""
    if provider["format"] == "text":
        payload = lines(content.decode())
    elif provider["format"] == "yaml":
        document = yaml.safe_load(content)
        assert isinstance(document, dict) and "payload" in document, provider
        payload = document["payload"]
        assert isinstance(payload, list), provider
    else:
        raise AssertionError(("unsupported provider format", provider["format"]))
    assert payload and all(isinstance(item, str) and item.strip() for item in payload), provider
    if provider["behavior"] != "ipcidr":
        return payload

    compatible, incompatible = [], []
    for item in payload:
        try:
            ipaddress.ip_network(item, strict=False)
            compatible.append(item)
        except ValueError:
            incompatible.append(item)

    if name == "China-IP":
        assert incompatible == ["132203"], ("unexpected China-IP non-CIDR entries", incompatible)
        assert "IP-ASN,132203,DIRECT" in CONFIG["rules"], "China-IP ASN exception lost explicit routing"
    else:
        assert not incompatible, (name, "invalid ipcidr provider entries", incompatible)
    return compatible


def assert_no_rule_provider_warnings(text):
    suspicious = []
    for line in text.splitlines():
        lowered = line.casefold()
        if "invalid ipcidr:[132203]" in lowered:
            assert "IP-ASN,132203,DIRECT" in CONFIG["rules"]
            continue
        if (
            ("warn" in lowered or "warning" in lowered)
            and ("rule" in lowered or "provider" in lowered)
            and any(token in lowered for token in ("invalid", "unsupported", "fail", "error", "skip", "drop"))
        ):
            suspicious.append(line)
    assert not suspicious, {"rule/provider parse warnings": suspicious}


def cache_rules(home):
    """Keep real provider formats/content; only substitute transport for CI."""
    expected_rule_counts = {}
    for name, provider in CONFIG["rule-providers"].items():
        path = home / provider["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (ROOT / "List/UploadCN.list").read_bytes() if name == "UploadCN" else fetch(provider["url"])
        assert content, name
        path.write_bytes(content)
        payload = provider_payload(name, provider, content)
        expected_rule_counts[name] = len(payload)
        if name == "AI-Daily":
            surge_url = provider["url"].replace("/mihomo/", "/surge/").replace(".yaml", ".list")
            surge_payload = lines(fetch(surge_url).decode())
            assert payload and surge_payload, name
            # Engine-specific syntax differs; Copilot's fixed domain rules are shared.
            assert COPILOT_CORE_RULES <= set(payload), "Mihomo daily Copilot coverage"
            assert COPILOT_CORE_RULES <= set(surge_payload), "Surge daily Copilot coverage"
            for host in ["microsoft.com", "github.com", "raw.githubusercontent.com"]:
                for rule in payload:
                    kind, value = rule.split(",", 1)
                    assert not (kind == "DOMAIN" and host == value), (name, host)
                    assert not (kind == "DOMAIN-SUFFIX" and (host == value or host.endswith("." + value))), (name, host)
    print("Actual referenced upstream rules downloaded; AI formats and missing domains: passed")
    return expected_rule_counts

def api(path, base):
    return json.loads(fetch(base + path))


def native_check(binary, home, fixtures, expected_rule_counts):
    config = copy.deepcopy(CONFIG)
    # Use isolated listeners so local verification cannot target a running client.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        controller_port = listener.getsockname()[1]
    base = f"http://127.0.0.1:{controller_port}"
    config["mixed-port"] = 0
    config["dns"]["listen"] = ""
    expected_names = {}
    for index, (key, provider) in enumerate(config["proxy-providers"].items()):
        names = fixtures[index]
        prefix = provider["override"]["additional-prefix"]
        # Fixed accept/reject table is the oracle, not the regex under test.
        expected_names[key] = [
            prefix + name for name in names
            if name not in MIHOMO_PROVIDER_STATUS_NAMES
        ]
        path = home / provider["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        # Documentation-only addresses, no credentials and no real subscription calls.
        path.write_text(yaml.safe_dump({"proxies": [
            {"name": name, "type": "socks5", "server": "192.0.2.1", "port": 1080} for name in names
        ]}, allow_unicode=True))
        provider["type"] = "file"
        provider.pop("url")
        provider["health-check"]["enable"] = False
    for provider in config["rule-providers"].values():
        provider["type"] = "file"
        provider.pop("url")
    config["external-controller"] = f"127.0.0.1:{controller_port}"
    config["profile"]["store-selected"] = False  # each scenario starts from template defaults
    path = home / "config.yaml"
    path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False))
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    parsed = subprocess.run(
        [binary, "-t", "-d", str(home), "-f", str(path)],
        capture_output=True,
        text=True,
        timeout=90,
        creationflags=creationflags,
    )
    if parsed.returncode:
        raise AssertionError(parsed.stdout + parsed.stderr)
    assert_no_rule_provider_warnings(parsed.stdout + parsed.stderr)
    with (home / "core.log").open("w") as log:
        process = subprocess.Popen([binary, "-d", str(home), "-f", str(path)], stdout=log, stderr=log, creationflags=creationflags)
        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise AssertionError("Mihomo exited before controller became ready")
                try:
                    proxies = api("/proxies", base)["proxies"]
                    providers = api("/providers/proxies", base)["providers"]
                    rule_providers = api("/providers/rules", base)["providers"]
                    if (
                        all(len(providers[key]["proxies"]) == len(names) for key, names in expected_names.items())
                        and all(
                            rule_providers[name]["ruleCount"] == expected_rule_counts[name]
                            for name in CONFIG["rule-providers"]
                        )
                    ):
                        break
                except (OSError, KeyError):
                    pass
                time.sleep(0.1)
            else:
                rule_counts = {
                    name: (
                        rule_providers.get(name, {}).get("ruleCount"),
                        expected_rule_counts[name],
                    )
                    for name in CONFIG["rule-providers"]
                }
                raise AssertionError(
                    f"Controller/providers did not become fully ready; rule counts actual/expected={rule_counts}"
                )
            for key, expected in expected_names.items():
                actual_provider_names = [node["name"] for node in providers[key]["proxies"]]
                assert actual_provider_names == expected, (key, actual_provider_names, expected)
            for group in CONFIG["proxy-groups"]:
                actual = proxies[group["name"]]
                if group["name"] == "资源下载":
                    # use-only fallback inherits provider health URL; no group task.
                    inherited = next(CONFIG["proxy-providers"][n]["health-check"]["url"] for n in group["use"])
                    assert actual["testUrl"] == inherited
                if "use" in group:
                    expected = [name for key in group["use"] for name in expected_names[key]]
                    if "filter" in group:
                        expected = [n for n in expected if re.search(group["filter"], n)]
                    if "exclude-filter" in group:
                        expected = [n for n in expected if not re.search(group["exclude-filter"], n)]
                    assert actual["all"] == (expected or ["REJECT"]), (group["name"], actual, expected)
                elif group["type"] == "select":
                    assert actual["all"] == group["proxies"], group["name"]
                    assert actual["now"] == group.get("default-selected", group["proxies"][0]), group["name"]
            actual_rules = api("/rules", base)["rules"]
            assert len(actual_rules) == len(CONFIG["rules"])
            for raw, actual in zip(CONFIG["rules"], actual_rules):
                parts = raw.split(",")
                policy = parts[-2] if parts[-1] == "no-resolve" else parts[-1]
                assert actual["proxy"] == policy, (raw, actual)
                if parts[0] == "RULE-SET":
                    assert actual["type"] == "RuleSet" and actual["payload"] == parts[1], (raw, actual)
                elif parts[0] == "IP-ASN":
                    assert actual["type"] in {"IP-ASN", "IPASN"} and actual["payload"] == parts[1], (raw, actual)
            rule_providers = api("/providers/rules", base)["providers"]
            assert all(
                rule_providers[name]["ruleCount"] == expected_rule_counts[name]
                for name in CONFIG["rule-providers"]
            ), {
                name: (rule_providers[name]["ruleCount"], expected_rule_counts[name])
                for name in CONFIG["rule-providers"]
            }
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            log.flush()
            runtime_log = (home / "core.log").read_text(encoding="utf-8", errors="replace")
            if sys.exc_info()[0]:
                print(runtime_log)
            else:
                assert_no_rule_provider_warnings(runtime_log)


def native_asn_match_check(binary, home):
    """Prove the core actually matches IP-ASN using a pinned MaxMind test DB."""
    asn_home = home / "asn-match"
    asn_home.mkdir()
    asn = fetch(
        "https://raw.githubusercontent.com/maxmind/MaxMind-DB/"
        "276926d23b4109ca5452709bfb5931c338afb34c/test-data/GeoLite2-ASN-Test.mmdb"
    )
    (asn_home / "ASN.mmdb").write_bytes(asn)

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        controller_port = listener.getsockname()[1]
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        mixed_port = listener.getsockname()[1]

    config = {
        "mixed-port": mixed_port,
        "external-controller": f"127.0.0.1:{controller_port}",
        "log-level": "info",
        "ipv6": False,
        "profile": {"store-selected": False, "store-fake-ip": False},
        "rules": [
            "IP-ASN,15169,REJECT",
            "MATCH,DIRECT",
        ],
    }
    path = asn_home / "config.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False))
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with (asn_home / "core.log").open("w") as log:
        process = subprocess.Popen(
            [binary, "-d", str(asn_home), "-f", str(path)],
            stdout=log,
            stderr=log,
            creationflags=creationflags,
        )
        try:
            base = f"http://127.0.0.1:{controller_port}"
            for _ in range(100):
                if process.poll() is not None:
                    raise AssertionError("Mihomo exited before ASN controller became ready")
                try:
                    first = api("/rules", base)["rules"][0]
                    if first["payload"] == "15169":
                        break
                except (OSError, KeyError, IndexError):
                    pass
                time.sleep(0.1)
            else:
                raise AssertionError("ASN test controller did not become ready")

            assert first["type"] in {"IP-ASN", "IPASN"} and first["proxy"] == "REJECT", first
            with socket.create_connection(("127.0.0.1", mixed_port), timeout=5) as client:
                client.sendall(
                    b"CONNECT 1.0.0.1:80 HTTP/1.1\r\n"
                    b"Host: 1.0.0.1:80\r\n\r\n"
                )
                try:
                    client.recv(1024)
                except (ConnectionResetError, TimeoutError):
                    pass

            for _ in range(50):
                first = api("/rules", base)["rules"][0]
                if first.get("extra", {}).get("hitCount", 0) >= 1:
                    break
                time.sleep(0.1)
            else:
                raise AssertionError(f"IP-ASN rule did not record a data-plane hit: {first}")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main():
    static_checks()
    binary = str(Path(sys.argv[1]).resolve())
    all_names = [name for names in CASES.values() for name in names]
    scenarios = {
        "two-airport region table": [all_names[::2], all_names[1::2]],
        "missing regions": [["US-01"], ["DE-01"]],
        "all supported regions empty": [["AUS-Sydney"], ["DE-01"]],
        "metadata-like legitimate node names": [
            MIHOMO_PROVIDER_VALID_NAMES[::2], MIHOMO_PROVIDER_VALID_NAMES[1::2]
        ],
        "provider status filtering": [
            MIHOMO_PROVIDER_VALID_NAMES[::2] + MIHOMO_PROVIDER_STATUS_NAMES[::2],
            MIHOMO_PROVIDER_VALID_NAMES[1::2] + MIHOMO_PROVIDER_STATUS_NAMES[1::2],
        ],
    }
    with tempfile.TemporaryDirectory(prefix="net-template-") as directory:
        home = Path(directory)
        expected_rule_counts = cache_rules(home)
        # MaxMind's official test database, pinned; only verifies native GEOIP loading.
        geoip = fetch("https://raw.githubusercontent.com/maxmind/MaxMind-DB/276926d23b4109ca5452709bfb5931c338afb34c/test-data/GeoIP2-Country-Test.mmdb")
        (home / "Country.mmdb").write_bytes(geoip)
        native_asn_match_check(binary, home)
        print("Mihomo IP-ASN native recognition and data-plane match: passed")
        for title, fixtures in scenarios.items():
            native_check(binary, home, fixtures, expected_rule_counts)
            print(f"Mihomo parse, actual group membership/defaults and loaded rules ({title}): passed")
    print("Surge: static checks only; no native Surge validation available in CI")


if __name__ == "__main__":
    main()
