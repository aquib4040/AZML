import os
import sys
import re
import time
import asyncio
import aiohttp

async def run_network_speedtest():
    print("=== 1. SERVER NETWORK SPEEDTEST ===")
    try:
        import speedtest
        st = speedtest.Speedtest(secure=True)
        st.get_best_server()
        download_speed = st.download() / (1024 * 1024)  # Mbps
        upload_speed = st.upload() / (1024 * 1024)      # Mbps
        ping = st.results.ping

        print(f"  - Download Speed: {download_speed:.2f} Mbps ({download_speed/8:.2f} MB/s)")
        print(f"  - Upload Speed:   {upload_speed:.2f} Mbps ({upload_speed/8:.2f} MB/s)")
        print(f"  - Latency/Ping:   {ping:.2f} ms")
        return download_speed, upload_speed, ping
    except Exception as e:
        print(f"  - Network Speedtest Skipped/Failed: {e}")
        return 0, 0, 0

async def run_telegram_speedtest(bot_token, api_id, api_hash):
    print("\n=== 2. TELEGRAM FILE UPLOAD & DOWNLOAD SPEEDTEST ===")
    try:
        from pyrogram import Client

        app = Client(
            "tg_speed_session",
            api_id=int(api_id),
            api_hash=api_hash,
            bot_token=bot_token,
            in_memory=True
        )
        await app.start()
        me = await app.get_me()
        print(f"  - Logged into Telegram Bot: @{me.username}")

        # Check if custom file size or custom Telegram message link/ID is provided
        custom_link = os.environ.get("TEST_TELEGRAM_LINK", "")
        file_size_mb = int(os.environ.get("BENCHMARK_FILE_SIZE_MB", "50"))

        tg_down_mbps, tg_up_mbps = 0, 0

        if custom_link:
            print(f"  - Custom Telegram File Link Provided: {custom_link}")
            # Format: https://t.me/c/chat_id/msg_id or https://t.me/channel/msg_id
            parts = custom_link.strip().split("/")
            if len(parts) >= 2:
                chat_id = parts[-2]
                msg_id = int(parts[-1])
                if chat_id.isdigit() or chat_id.startswith("-"):
                    chat_id = int(chat_id)
                    if not str(chat_id).startswith("-100") and not str(chat_id).startswith("-"):
                        chat_id = int(f"-100{chat_id}")

                msg = await app.get_messages(chat_id, msg_id)
                if msg and (msg.document or msg.video or msg.audio):
                    fsize_mb = (msg.document or msg.video or msg.audio).file_size / (1024 * 1024)
                    print(f"  - Downloading Custom Telegram File ({fsize_mb:.2f} MB)...")
                    start_down = time.time()
                    down_path = await app.download_media(msg)
                    down_duration = time.time() - start_down
                    tg_down_mbps = (fsize_mb * 8) / down_duration if down_duration > 0 else 0
                    print(f"  - Telegram Download Speed: {tg_down_mbps:.2f} Mbps ({fsize_mb/down_duration:.2f} MB/s)")
                    if down_path and os.path.exists(down_path):
                        os.remove(down_path)
        else:
            # Auto-generated benchmark file (default 50MB, configurable to 2000MB)
            test_file = f"tg_benchmark_{file_size_mb}mb.dat"
            print(f"  - Generating {file_size_mb} MB test payload...")
            with open(test_file, "wb") as f:
                f.write(os.urandom(file_size_mb * 1024 * 1024))

            # Measure Telegram Upload Speed
            print(f"  - Testing Telegram Upload Speed ({file_size_mb} MB)...")
            start_up = time.time()
            msg = await app.send_document("me", test_file, caption=f"Telegram Speedtest ({file_size_mb}MB)")
            up_duration = time.time() - start_up
            tg_up_mbps = (file_size_mb * 8) / up_duration if up_duration > 0 else 0
            tg_up_mbs = file_size_mb / up_duration if up_duration > 0 else 0
            print(f"  - Telegram Upload Speed: {tg_up_mbps:.2f} Mbps ({tg_up_mbs:.2f} MB/s)")

            # Measure Telegram Download Speed
            print(f"  - Testing Telegram Download Speed ({file_size_mb} MB)...")
            start_down = time.time()
            down_path = await app.download_media(msg)
            down_duration = time.time() - start_down
            tg_down_mbps = (file_size_mb * 8) / down_duration if down_duration > 0 else 0
            tg_down_mbs = file_size_mb / down_duration if down_duration > 0 else 0
            print(f"  - Telegram Download Speed: {tg_down_mbps:.2f} Mbps ({tg_down_mbs:.2f} MB/s)")

            # Cleanup
            await msg.delete()
            if os.path.exists(test_file):
                os.remove(test_file)
            if down_path and os.path.exists(down_path):
                os.remove(down_path)

        await app.stop()
        return tg_down_mbps, tg_up_mbps
    except Exception as e:
        print(f"  - Telegram Speedtest Error: {e}")
        return 0, 0

def update_readme_benchmark(down_net, up_net, tg_down, tg_up):
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        return

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    new_block = f"""<!-- SPEEDTEST_START -->
### ⚡ Automated Speed Benchmark
*Last Run: {timestamp}*

| Benchmark | Speed (Mbps) | Speed (MB/s) |
|---|---|---|
| ⬇️ Telegram Download | {tg_down:.2f} Mbps | {tg_down/8:.2f} MB/s |
| ⬆️ Telegram Upload | {tg_up:.2f} Mbps | {tg_up/8:.2f} MB/s |
| 🌐 Server Download | {down_net:.2f} Mbps | {down_net/8:.2f} MB/s |
| 🌐 Server Upload | {up_net:.2f} Mbps | {up_net/8:.2f} MB/s |
<!-- SPEEDTEST_END -->"""

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r"<!-- SPEEDTEST_START -->.*?<!-- SPEEDTEST_END -->", re.DOTALL)
    if pattern.search(content):
        updated_content = pattern.sub(new_block, content)
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print("\n  - Successfully updated README.md with Telegram benchmark results!")

async def main():
    print("==========================================")
    print("  AZML TELEGRAM & NETWORK SPEED BENCHMARK")
    print("==========================================\n")
    
    down_net, up_net, ping = await run_network_speedtest()
    
    bot_token = os.environ.get("BOT_TOKEN")
    api_id = os.environ.get("TELEGRAM_API")
    api_hash = os.environ.get("TELEGRAM_HASH")

    tg_down, tg_up = 0, 0
    if bot_token and api_id and api_hash:
        tg_down, tg_up = await run_telegram_speedtest(bot_token, api_id, api_hash)
    else:
        print("\n=== 2. TELEGRAM SPEEDTEST SKIPPED ===")
        print("  - Secrets BOT_TOKEN, TELEGRAM_API, or TELEGRAM_HASH not set.")

    update_readme_benchmark(down_net, up_net, tg_down, tg_up)

if __name__ == "__main__":
    asyncio.run(main())
