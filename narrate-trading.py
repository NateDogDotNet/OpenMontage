#!/usr/bin/env python3
"""Generate narration for trading explainer video, then mix with Remotion render."""
import subprocess, os, json

PROJECT = "/app/projects/trading-explainer"
AUDIO = f"{PROJECT}/audio"
RENDERS = f"{PROJECT}/renders"
os.makedirs(AUDIO, exist_ok=True)
os.makedirs(RENDERS, exist_ok=True)

PIPER = "/app/models/en_US-lessac-medium.onnx"

# Narration segments timed to match the Remotion composition
# Each segment covers a range of scenes
segments = [
    ("s01_intro", "Self-hosted algorithmic trading. From idea validation to live execution, here's the complete pipeline."),
    ("s02_problem", "Most algo traders fail. Not because of bad strategies, but because of bad infrastructure. Data quality, execution, and risk management are what separate winners from losers."),
    ("s03_pipeline", "A real trading system has six stages. Market data ingestion. Strategy development. Backtesting. Paper trading. Live execution. And continuous monitoring."),
    ("s04_platforms", "Step one, choose your engine. LEAN from QuantConnect is the industry standard. It supports stocks, futures, options, crypto, and FX. Python or C sharp. Docker friendly. Production grade."),
    ("s05_lean", "LEAN connects to over ten brokers including Interactive Brokers and Alpaca. NautilusTrader offers a modern event-driven architecture with a Rust core for maximum speed."),
    ("s06_choose", "For equities and futures, use LEAN with Interactive Brokers. For crypto, Freqtrade with Binance is the go-to choice. Both are fully self-hosted and open source."),
    ("s07_data", "Step two, get your data right. Without good data, nothing else matters. Polygon and Alpaca cover equities. Binance is free for crypto. Store everything in Parquet files with DuckDB for blazing fast queries."),
    ("s08_storage", "Most professional quants store tick and bar data in columnar format. This makes backtesting orders of magnitude faster than traditional databases."),
    ("s09_strategies", "Step three, pick a strategy family. There are three families that dominate quant trading. Momentum and trend following. Mean reversion. And statistical arbitrage."),
    ("s10_momentum", "Momentum strategies ride existing trends. If the fifty day moving average crosses above the two hundred day, go long. These work best in commodities, FX, and crypto."),
    ("s11_meanrev", "Mean reversion bets that prices return to their average. When price breaks above the upper Bollinger Band, short it. This works best in equities and ETFs."),
    ("s12_backtest", "Step four, backtest ruthlessly. Run at least one year of historical data. Then paper trade for thirty days with fake money but real market conditions. Only then go live, starting small."),
    ("s13_fail", "Ninety percent of retail algo traders fail. The top reasons are bad data, overfitting to historical patterns, ignoring trading costs like spread and commissions, and execution lag."),
    ("s14_infra", "Step five, set up your infrastructure. A realistic home setup costs about three thousand dollars for hardware, plus two to three hundred per month for data feeds and hosting. No colocation needed."),
    ("s15_datasets", "Step six, find your real edge. The five datasets that produce real alpha are order flow data, volume and liquidity patterns, news sentiment via NLP, fundamental and macro data, and alternative data."),
    ("s16_altdata", "Alternative data is the new frontier. Satellite imagery, credit card spending, app downloads, shipping traffic. Sixty-five percent of hedge funds now use it."),
    ("s17_stack", "The recommended stack. Parquet plus DuckDB for data. Python and Jupyter for research. LEAN or NautilusTrader as your engine. Interactive Brokers for execution. Prometheus and Grafana for monitoring."),
    ("s18_truth", "Here's the hidden truth. Strategy ideas are easy. Reliable execution infrastructure is the real moat. Invest in your pipeline, not just your signals."),
    ("s19_cta", "All of these tools are free and open source. Start building your self-hosted trading system today."),
]

print("=== Generating narration segments ===")
all_wavs = []
for name, text in segments:
    out = f"{AUDIO}/{name}.wav"
    # Escape single quotes for shell
    safe_text = text.replace("'", "'\\''")
    subprocess.run(f"echo '{safe_text}' | piper --model {PIPER} --output_file {out}",
                   shell=True, capture_output=True)
    if os.path.exists(out) and os.path.getsize(out) > 100:
        probe = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'json', out],
            capture_output=True, text=True
        )
        dur = float(json.loads(probe.stdout)['format']['duration'])
        print(f"  {name}: {dur:.2f}s")
        all_wavs.append(out)
    else:
        print(f"  {name}: FAILED")

# Concatenate all narration into one track
print("\n=== Concatenating narration ===")
concat_file = f"{AUDIO}/concat.txt"
with open(concat_file, 'w') as f:
    for wav in all_wavs:
        f.write(f"file '{wav}'\n")

narration_path = f"{AUDIO}/narration-full.wav"
subprocess.run([
    'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
    '-c:a', 'pcm_s16le', '-ar', '22050', narration_path
], capture_output=True)

if os.path.exists(narration_path):
    probe = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'json', narration_path],
        capture_output=True, text=True
    )
    nar_dur = float(json.loads(probe.stdout)['format']['duration'])
    print(f"  Full narration: {nar_dur:.1f}s")
else:
    print("  FAILED to concatenate")

print("\n=== Done! Narration ready for mixing. ===")
print(f"  Path: {narration_path}")
