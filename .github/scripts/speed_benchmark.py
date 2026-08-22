import os
import sys
import re
import time
import asyncio
from inspect import signature
from pyrogram import Client

def azmlTgClient(*args, **kwargs):
    if "max_concurrent_transmissions" in signature(Client.__init__).parameters:
        kwargs["max_concurrent_transmissions"] = 1000
    return Client(*args, **kwargs)

def progress_callback(current, total, start_time, label):
    elapsed = time.time() - start_time
    if elapsed > 0 and total > 0:
        speed_mbs = (current / (1024 * 1024)) / elapsed
        percent = (current / total) * 100
        print(f"[{label}] {percent:.1f}% ({current/(1024*1024):.1f}/{total/(1024*1024):.1f} MB) @ {speed_mbs:.2f} MB/S", end="\r")

async def run_telegram_download_benchmark(bot_token, api_id, api_hash):
    try:
        app = azmlTgClient(
            "tg_speed_session",
            api_id=int(api_id),
            api_hash=api_hash,
            bot_token=bot_token,
            in_memory=True
        )
        await app.start()

        file_mb = float(os.environ.get("BENCHMARK_FILE_SIZE_MB", "1956"))
        test_file = f"tg_benchmark_{int(file_mb)}mb.dat"

        # Create 1.91 GB test payload
        chunk = os.urandom(10 * 1024 * 1024)
        with open(test_file, "wb") as f:
            for _ in range(int(file_mb // 10)):
                f.write(chunk)
            rem = int((file_mb % 10) * 1024 * 1024)
            if rem > 0:
                f.write(os.urandom(rem))

        # Upload temporary test payload to Telegram
        msg = await app.send_document("me", test_file, caption="Speedtest Payload")
        if os.path.exists(test_file):
            os.remove(test_file)

        # Benchmark ONLY Telegram Download Speed
        print("Measuring Telegram Download Speed (1.91 GB)...")
        start_down = time.time()
        down_path = await app.download_media(
            msg,
            progress=progress_callback,
            progress_args=(start_down, "Downloading")
        )
        print()
        down_duration = time.time() - start_down
        tg_down_mbs = file_mb / down_duration if down_duration > 0 else 0

        # Cleanup
        await msg.delete()
        if down_path and os.path.exists(down_path):
            os.remove(down_path)

        await app.stop()
        return tg_down_mbs
    except Exception as e:
        print(f"Telegram Download Benchmark Error: {e}")
        return 0.0

def update_readme(tg_down_mbs, loc):
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        return

    region = "Europe (DC4)" if loc in ["EU", "DC4"] else "USA (DC1)"
    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    block = f"""<!-- SPEEDTEST_START -->
### ⚡ Telegram Download Speed (1.91 GB)
*Region: **{region}** | Updated: {ts}*

| Benchmark | Speed |
|---|---|
| ⬇️ Telegram Download (1.91 GB) | {tg_down_mbs:.2f} MB/S |
<!-- SPEEDTEST_END -->"""

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r"<!-- SPEEDTEST_START -->.*?<!-- SPEEDTEST_END -->", re.DOTALL)
    if pattern.search(content):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(pattern.sub(block, content))

async def main():
    loc = os.environ.get("TG_DC_LOCATION", "EU").upper()
    bot_token = os.environ.get("BOT_TOKEN")
    api_id = os.environ.get("TELEGRAM_API")
    api_hash = os.environ.get("TELEGRAM_HASH")

    tg_down_mbs = 0.0
    if bot_token and api_id and api_hash:
        tg_down_mbs = await run_telegram_download_benchmark(bot_token, api_id, api_hash)

    update_readme(tg_down_mbs, loc)

if __name__ == "__main__":
    asyncio.run(main())
