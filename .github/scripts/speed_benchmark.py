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
        print(f"[{label}] {percent:.1f}% ({current/(1024*1024):.1f}/{total/(1024*1024):.1f} MB) @ {speed_mbs:.2f} MB/s", end="\r")

async def run_network_speedtest(loc="EU"):
    try:
        import speedtest
        st = speedtest.Speedtest(secure=True)
        country = "United States" if loc in ["US", "DC1"] else "Netherlands"
        try:
            servers = st.get_servers()
            ids = [s["id"] for slist in servers.values() for s in slist if country.lower() in s.get("country", "").lower()]
            server = st.get_best_server(ids[:5]) if ids else st.get_best_server()
        except Exception:
            server = st.get_best_server()

        down = st.download() / (1024 * 1024)
        up = st.upload() / (1024 * 1024)
        return down, up
    except Exception:
        return 0, 0

async def run_telegram_speedtest(bot_token, api_id, api_hash):
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

        chunk = os.urandom(10 * 1024 * 1024)
        with open(test_file, "wb") as f:
            for _ in range(int(file_mb // 10)):
                f.write(chunk)
            rem = int((file_mb % 10) * 1024 * 1024)
            if rem > 0:
                f.write(os.urandom(rem))

        start_up = time.time()
        msg = await app.send_document(
            "me",
            test_file,
            caption="Speedtest",
            progress=progress_callback,
            progress_args=(start_up, "Upload")
        )
        up_duration = time.time() - start_up
        up_mbps = (file_mb * 8) / up_duration if up_duration > 0 else 0
        print()

        start_down = time.time()
        down_path = await app.download_media(
            msg,
            progress=progress_callback,
            progress_args=(start_down, "Download")
        )
        down_duration = time.time() - start_down
        down_mbps = (file_mb * 8) / down_duration if down_duration > 0 else 0
        print()

        await msg.delete()
        if os.path.exists(test_file):
            os.remove(test_file)
        if down_path and os.path.exists(down_path):
            os.remove(down_path)

        await app.stop()
        return down_mbps, up_mbps
    except Exception as e:
        print(f"Telegram Speedtest Error: {e}")
        return 0, 0

def update_readme(down_net, up_net, tg_down, tg_up, loc):
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        return

    region = "Europe (DC4)" if loc in ["EU", "DC4"] else "USA (DC1)"
    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    block = f"""<!-- SPEEDTEST_START -->
### ⚡ Speed Benchmark (1.91 GB)
*Region: **{region}** | Updated: {ts}*

| Benchmark | Speed (Mbps) | Speed (MB/s) |
|---|---|---|
| ⬇️ Telegram Download (1.91 GB) | {tg_down:.2f} Mbps | {tg_down/8:.2f} MB/s |
| ⬆️ Telegram Upload (1.91 GB) | {tg_up:.2f} Mbps | {tg_up/8:.2f} MB/s |
| 🌐 Server Download | {down_net:.2f} Mbps | {down_net/8:.2f} MB/s |
| 🌐 Server Upload | {up_net:.2f} Mbps | {up_net/8:.2f} MB/s |
<!-- SPEEDTEST_END -->"""

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r"<!-- SPEEDTEST_START -->.*?<!-- SPEEDTEST_END -->", re.DOTALL)
    if pattern.search(content):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(pattern.sub(block, content))

async def main():
    loc = os.environ.get("TG_DC_LOCATION", "EU").upper()
    down_net, up_net = await run_network_speedtest(loc)

    bot_token = os.environ.get("BOT_TOKEN")
    api_id = os.environ.get("TELEGRAM_API")
    api_hash = os.environ.get("TELEGRAM_HASH")

    tg_down, tg_up = 0, 0
    if bot_token and api_id and api_hash:
        tg_down, tg_up = await run_telegram_speedtest(bot_token, api_id, api_hash)

    update_readme(down_net, up_net, tg_down, tg_up, loc)

if __name__ == "__main__":
    asyncio.run(main())
