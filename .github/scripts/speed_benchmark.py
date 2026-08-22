import os
import sys
import re
import time
import asyncio
import logging
import aiohttp
from inspect import signature
from pyrogram import Client

logging.getLogger("pyrogram").setLevel(logging.ERROR)

def azmlTgClient(*args, **kwargs):
    if "max_concurrent_transmissions" in signature(Client.__init__).parameters:
        kwargs["max_concurrent_transmissions"] = 1000
    return Client(*args, **kwargs)

async def get_runner_location():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://ip-api.com/json", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    country = data.get("country", "")
                    city = data.get("city", "")
                    return f"{country} ({city})" if city else country
    except Exception:
        pass
    return "GitHub Runner"

class SpeedTracker:
    def __init__(self, label):
        self.label = label
        self.start_time = None
        self.peak_speed = 0.0

    def callback(self, current, total):
        if self.start_time is None:
            self.start_time = time.time()
            return
        
        elapsed = time.time() - self.start_time
        if elapsed >= 0.5 and total > 0:
            current_speed = (current / (1024 * 1024)) / elapsed
            if current_speed > self.peak_speed:
                self.peak_speed = current_speed
            percent = (current / total) * 100
            print(f"[{self.label}] {percent:.1f}% ({current/(1024*1024):.1f}/{total/(1024*1024):.1f} MB) @ {current_speed:.2f} MB/S (Peak: {self.peak_speed:.2f} MB/S)", end="\r")

async def run_telegram_benchmark(bot_token, api_id, api_hash, owner_id):
    bot_dc = "Unknown"
    owner_dc = "Unknown"
    try:
        owner_str = str(owner_id).strip()
        chat_target = int(owner_str) if (owner_str.isdigit() or owner_str.startswith("-")) else owner_str

        app = azmlTgClient(
            "tg_speed_session",
            api_id=int(api_id),
            api_hash=api_hash,
            bot_token=bot_token,
            in_memory=True
        )
        await app.start()

        # Detect Bot DC
        if getattr(app.me, "dc_id", None):
            bot_dc = f"DC{app.me.dc_id}"

        # Detect Owner DC
        try:
            owner_obj = await app.get_users(chat_target)
            if getattr(owner_obj, "dc_id", None):
                owner_dc = f"DC{owner_obj.dc_id}"
        except Exception:
            pass

        file_mb = float(os.environ.get("BENCHMARK_FILE_SIZE_MB", "1956"))
        test_file = f"tg_benchmark_{int(file_mb)}mb.dat"

        chunk = os.urandom(10 * 1024 * 1024)
        with open(test_file, "wb") as f:
            for _ in range(int(file_mb // 10)):
                f.write(chunk)
            rem = int((file_mb % 10) * 1024 * 1024)
            if rem > 0:
                f.write(os.urandom(rem))

        # Benchmark Upload
        print(f"Measuring Telegram Upload Speed (1.91 GB) [Bot: {bot_dc} | Owner: {owner_dc}]...")
        up_tracker = SpeedTracker("Upload")
        start_up = time.time()
        msg = await app.send_document(
            chat_target,
            test_file,
            caption="Speedtest Payload",
            progress=up_tracker.callback
        )
        print()
        up_duration = time.time() - start_up
        up_avg = file_mb / up_duration if up_duration > 0 else 0
        up_peak = up_tracker.peak_speed

        if os.path.exists(test_file):
            os.remove(test_file)

        # Benchmark Download
        print(f"Measuring Telegram Download Speed (1.91 GB)...")
        down_tracker = SpeedTracker("Download")
        start_down = time.time()
        down_path = await app.download_media(
            msg,
            progress=down_tracker.callback
        )
        print()
        down_duration = time.time() - start_down
        down_avg = file_mb / down_duration if down_duration > 0 else 0
        down_peak = down_tracker.peak_speed

        await msg.delete()
        if down_path and os.path.exists(down_path):
            os.remove(down_path)

        await app.stop()
        return down_avg, down_peak, up_avg, up_peak, bot_dc, owner_dc
    except Exception as e:
        print(f"Telegram Benchmark Error: {e}")
        return 0.0, 0.0, 0.0, 0.0, bot_dc, owner_dc

def update_readme(down_avg, down_peak, up_avg, up_peak, bot_dc, owner_dc, runner_loc):
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        return

    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    block = f"""<!-- SPEEDTEST_START -->
### ⚡ Telegram Speed Benchmark (1.91 GB)
*Bot DC: **{bot_dc}** | Owner DC: **{owner_dc}** | Runner Server: **{runner_loc}** | Updated: {ts}*

| Benchmark | Avg Speed | Peak Speed |
|---|---|---|
| ⬇️ Telegram Download (1.91 GB) | {down_avg:.2f} MB/S | {down_peak:.2f} MB/S |
| ⬆️ Telegram Upload (1.91 GB) | {up_avg:.2f} MB/S | {up_peak:.2f} MB/S |
<!-- SPEEDTEST_END -->"""

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r"<!-- SPEEDTEST_START -->.*?<!-- SPEEDTEST_END -->", re.DOTALL)
    if pattern.search(content):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(pattern.sub(block, content))

async def main():
    runner_loc = await get_runner_location()
    bot_token = os.environ.get("BOT_TOKEN")
    api_id = os.environ.get("TELEGRAM_API")
    api_hash = os.environ.get("TELEGRAM_HASH")
    owner_id = os.environ.get("OWNER_ID")

    down_avg, down_peak, up_avg, up_peak = 0.0, 0.0, 0.0, 0.0
    bot_dc, owner_dc = "Unknown", "Unknown"

    if bot_token and api_id and api_hash and owner_id:
        down_avg, down_peak, up_avg, up_peak, bot_dc, owner_dc = await run_telegram_benchmark(bot_token, api_id, api_hash, owner_id)

    update_readme(down_avg, down_peak, up_avg, up_peak, bot_dc, owner_dc, runner_loc)

if __name__ == "__main__":
    asyncio.run(main())
