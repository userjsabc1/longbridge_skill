#!/usr/bin/env python3
"""
longbridge CLI 辅助脚本 — 批量查询、数据聚合、格式化输出。

单个命令直接用 `longbridge xxx --format json` 即可，本脚本用于：
1. 批量查询多个代码并聚合结果
2. K线数据导出为 CSV
3. 持仓盈亏快照
4. 快速检查 CLI 是否可用

Usage:
  python3 lb.py check                          # 检查 longbridge CLI 是否安装且已登录
  python3 lb.py quote TSLA.US 700.HK AAPL.US   # 批量行情（聚合表格）
  python3 lb.py kline TSLA.US --period day --count 30 --csv  # K线导出 CSV
  python3 lb.py snapshot                        # 持仓盈亏快照
"""

import argparse
import csv
import io
import json
import subprocess
import sys


def run_lb(args_list):
    """调用 longbridge CLI，返回 JSON 解析结果。"""
    ensure_installed()
    cmd = ["longbridge"] + args_list + ["--format", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        print("❌ longbridge 未安装。请先执行：")
        print("   brew install --cask longbridge/tap/longbridge-terminal")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"❌ 命令超时: {' '.join(cmd)}")
        sys.exit(1)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "auth" in stderr.lower() or "token" in stderr.lower() or "login" in stderr.lower():
            print("❌ 未登录或 Token 过期，请执行: longbridge login")
        else:
            print(f"❌ 命令失败: {stderr}")
        sys.exit(1)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.stdout.strip()


def ensure_installed():
    """确保 longbridge CLI 已安装，未安装则自动下载。"""
    try:
        subprocess.run(
            ["longbridge", "-h"], capture_output=True, timeout=10
        )
        return True
    except FileNotFoundError:
        print("longbridge 未安装，正在自动安装...")
        try:
            result = subprocess.run(
                ["sh", "-c", "curl -sSL https://github.com/longbridge/longbridge-terminal/raw/main/install | sh"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print("✅ 安装成功")
                return True
            else:
                print(f"❌ 安装失败: {result.stderr.strip()}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ 安装失败: {e}")
            sys.exit(1)


def cmd_check():
    """检查 CLI 安装和登录状态。"""
    ensure_installed()
    try:
        result = subprocess.run(
            ["longbridge", "check"], capture_output=True, text=True, timeout=15
        )
        print(result.stdout.strip())
        if result.returncode != 0 and result.stderr.strip():
            print(result.stderr.strip())
    except FileNotFoundError:
        print("❌ longbridge 未安装")
        sys.exit(1)


def cmd_quote(symbols):
    """批量行情查询。"""
    data = run_lb(["quote"] + symbols)
    if not isinstance(data, list):
        data = [data]
    # 简洁表格输出
    header = f"{'Symbol':<12} {'Last':>10} {'Change%':>10} {'Volume':>12} {'Turnover':>16}"
    print(header)
    print("-" * len(header))
    for item in data:
        symbol = item.get("symbol", "?")
        last = item.get("last", item.get("last_done", "N/A"))
        prev = item.get("prev_close", "0")
        try:
            change_pct = (float(last) - float(prev)) / float(prev) * 100
            change_str = f"{change_pct:+.2f}%"
        except (ValueError, ZeroDivisionError):
            change_str = "N/A"
        volume = item.get("volume", "N/A")
        turnover = item.get("turnover", "N/A")
        print(f"{symbol:<12} {str(last):>10} {change_str:>10} {str(volume):>12} {str(turnover):>16}")


def cmd_kline(symbol, period, count, as_csv):
    """K线查询，可选 CSV 输出。"""
    args = ["kline", symbol, "--period", period, "--count", str(count)]
    data = run_lb(args)
    if not isinstance(data, list):
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if as_csv:
        if not data:
            print("无数据")
            return
        writer = csv.DictWriter(sys.stdout, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_snapshot():
    """持仓盈亏快照：拉持仓 + 实时行情，计算浮动盈亏。"""
    positions = run_lb(["positions"])
    if not isinstance(positions, list) or not positions:
        print("无持仓数据")
        return

    symbols = [p["symbol"] for p in positions if p.get("symbol")]
    if not symbols:
        print("无持仓代码")
        return

    quotes = run_lb(["quote"] + symbols)
    if not isinstance(quotes, list):
        quotes = [quotes]

    price_map = {}
    for q in quotes:
        s = q.get("symbol", "")
        price_map[s] = float(q.get("last", q.get("last_done", 0)))

    header = f"{'Symbol':<12} {'Qty':>8} {'Cost':>10} {'Last':>10} {'P&L':>12} {'P&L%':>8}"
    print(header)
    print("-" * len(header))
    total_pnl = 0.0
    for p in positions:
        sym = p.get("symbol", "?")
        qty = float(p.get("quantity", 0))
        cost = float(p.get("cost_price", 0))
        last = price_map.get(sym, 0)
        pnl = (last - cost) * qty if cost > 0 else 0
        pnl_pct = ((last - cost) / cost * 100) if cost > 0 else 0
        total_pnl += pnl
        print(f"{sym:<12} {qty:>8.0f} {cost:>10.3f} {last:>10.3f} {pnl:>+12.2f} {pnl_pct:>+7.2f}%")
    print("-" * len(header))
    print(f"{'Total P&L':>54} {total_pnl:>+12.2f}")


def main():
    parser = argparse.ArgumentParser(description="longbridge CLI 辅助脚本")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="检查 CLI 安装和登录状态")

    p_quote = sub.add_parser("quote", help="批量行情查询")
    p_quote.add_argument("symbols", nargs="+", help="股票代码列表")

    p_kline = sub.add_parser("kline", help="K线查询")
    p_kline.add_argument("symbol", help="股票代码")
    p_kline.add_argument("--period", default="day", help="周期 (1m/5m/15m/30m/1h/day/week/month)")
    p_kline.add_argument("--count", type=int, default=100, help="数量")
    p_kline.add_argument("--csv", action="store_true", help="输出 CSV 格式")

    sub.add_parser("snapshot", help="持仓盈亏快照")

    args = parser.parse_args()

    if args.command == "check":
        cmd_check()
    elif args.command == "quote":
        cmd_quote(args.symbols)
    elif args.command == "kline":
        cmd_kline(args.symbol, args.period, args.count, args.csv)
    elif args.command == "snapshot":
        cmd_snapshot()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
