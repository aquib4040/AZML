import os
import sys
import re
import time
import asyncio
import aiohttp
from inspect import signature

def progress_callback(current, total, start_time, action_name):
    elapsed = time.time() - start_time
    if elapsed > 0 and total > 0:
        speed_mbs = (current / (1024 * 1024)) / elapsed
        percent = (current / total) * 100
        print(f"  -> [{action_name}] {percent:.1f}% ({current/(1024*1024):.1f}/{total/(1024*1024):.1f} MB) @ {speed_mbs:.2f} MB/s", end="\r")

async def run_network_speedtest(target_loc="EU"):
    print("=== 1. SERVER NETWORK SPEEDTEST ===")
    try:
        import speedtest
        st = speedtest.Speedtest(secure=True)
        
        target_country = "United States" if target_loc.upper() in ["US", "DC1"] else "Netherlands"
        print(f"  - Searching for Speedtest Servers in: {target_country}...")
        
        selected_server = None
        try:
            servers = st.get_servers()
            matching = []
            for s_list in servers.values():
                for s in s_list:
                    if target_country.lower() in s.get("country", "").lower():
                        matching.append(s["id"])
                        if len(matching) >= 5:
                            break
            if matching:
                selected_server = st.get_best_server(matching)
                print(f"  - Selected Server: {selected_server.get('sponsor')} ({selected_server.get('name')}, {selected_server.get('country')})")
        except Exception as filter_err:
            print(f"  - Server filtering notice: {filter_err}")

        if not selected_server:
            selected_server = st.get_best_server()
            print(f"  - Auto Selected Server: {selected_server.get('sponsor')} ({selected_server.get('name')})")

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

def create_azml_tg_client(*args, **kwargs):
    from pyrogram import Client
    if "max_concurrent_transmissions" in signature(Client.__init__).parameters:
        kwargs["max_concurrent_transmissions"] = 1000
    if "workers" in signature(Client.__init__).parameters:
        kwargs["workers"] = 100
    return Client(*args, **kwargs)

async def run_telegram_speedtest(bot_token, api_id, api_hash):
    print("\n=== 2. TELEGRAM FILE UPLOAD & DOWNLOAD SPEEDTEST ===")
    try:
        app = create_azml_tg_client(
            "tg_speed_session",
            api_id=int(api_id),
            api_hash=api_hash,
            bot_token=bot_token,
            in_memory=True
        )
        await app.start()
        me = await app.get_me()
        print(f"  - Logged into Telegram Bot: @{me.username} (AZML Concurrency: 1000 Max Transmissions)")

        custom_link = os.environ.get("TEST_TELEGRAM_LINK", "")
        file_size_mb = float(os.environ.get("BENCHMARK_FILE_SIZE_MB", "1956"))
        file_size_gb = file_size_mb / 1024

        tg_down_mbps, tg_up_mbps = 0, 0

        if custom_link:
            print(f"  - Custom Telegram File Link Provided: {custom_link}")
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
                    print(f"  - Downloading Custom Telegram File ({fsize_mb/1024:.2f} GB)...")
                    start_down = time.time()
                    down_path = await app.download_media(
                        msg,
                        progress=progress_callback,
                        progress_args=(start_down, "Downloading")
                    )
                    print()
                    down_duration = time.time() - start_down
                    tg_down_mbps = (fsize_mb * 8) / down_duration if down_duration > 0 else 0
                    print(f"  - Telegram Download Speed: {tg_down_mbps:.2f} Mbps ({fsize_mb/down_duration:.2f} MB/s)")
                    if down_path and os.path.exists(down_path):
                        os.remove(down_path)
        else:
            test_file = f"tg_benchmark_{int(file_size_mb)}mb.dat"
            print(f"  - Generating {file_size_gb:.2f} GB ({int(file_size_mb)} MB) test payload...")
            
            chunk_size_mb = 10
            chunk = os.urandom(chunk_size_mb * 1024 * 1024)
            num_chunks = int(file_size_mb // chunk_size_mb)
            rem_bytes = int((file_size_mb % chunk_size_mb) * 1024 * 1024)

            with open(test_file, "wb") as f:
                for _ in range(num_chunks):
                    f.write(chunk)
                if rem_bytes > 0:
                    f.write(os.urandom(rem_bytes))

            # Measure Telegram Upload Speed using AZML Pyrogram engine pattern
            print(f"  - Testing Telegram Upload Speed ({file_size_gb:.2f} GB)...")
            start_up = time.time()
            msg = await app.send_document(
                "me",
                test_file,
                caption=f"Telegram Speedtest ({file_size_gb:.2f} GB)",
                progress=progress_callback,
                progress_args=(start_up, "Uploading")
            )
            print()
            up_duration = time.time() - start_up
            tg_up_mbps = (file_size_mb * 8) / up_duration if up_duration > 0 else 0
            tg_up_mbs = file_size_mb / up_duration if up_duration > 0 else 0
            print(f"  - Telegram Upload Speed: {tg_up_mbps:.2f} Mbps ({tg_up_mbs:.2f} MB/s)")

            # Measure Telegram Download Speed using AZML Pyrogram engine pattern
            print(f"  - Testing Telegram Download Speed ({file_size_gb:.2f} GB)...")
            start_down = time.time()
            down_path = await app.download_media(
                msg,
                progress=progress_callback,
                progress_args=(start_down, "Downloading")
            )
            print()
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
        print(f"\n  - Telegram Speedtest Error: {e}")
        return 0, 0

def update_readme_benchmark(down_net, up_net, tg_down, tg_up, target_loc="EU"):
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        return

    region_label = "Europe (DC4 - Amsterdam)" if target_loc.upper() in ["EU", "DC4"] else "USA (DC1 - Miami)"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    new_block = f"""<!-- SPEEDTEST_START -->
### ⚡ Automated Speed Benchmark (1.91 GB Payload)
*Region Tested: **{region_label}** \| Last Run: {timestamp}*

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
        updated_content = pattern.sub(new_block, content)
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print("\n  - Successfully updated README.md with region-aware benchmark results!")

async def main():
    target_loc = os.environ.get("TG_DC_LOCATION", "EU").upper()
    print("==========================================")
    print(f"  AZML TELEGRAM & NETWORK SPEED BENCHMARK [{target_loc}]")
    print("==========================================\n")
    
    down_net, up_net, ping = await run_network_speedtest(target_loc)
    
    bot_token = os.environ.get("BOT_TOKEN")
    api_id = os.environ.get("TELEGRAM_API")
    api_hash = os.environ.get("TELEGRAM_HASH")

    tg_down, tg_up = 0, 0
    if bot_token and api_id and api_hash:
        tg_down, tg_up = await run_telegram_speedtest(bot_token, api_id, api_hash)
    else:
        print("\n=== 2. TELEGRAM SPEEDTEST SKIPPED ===")
        print("  - Secrets BOT_TOKEN, TELEGRAM_API, or TELEGRAM_HASH not set.")

    update_readme_benchmark(down_net, up_net, tg_down, tg_up, target_loc)

if __name__ == "__main__":
    asyncio.run(main())
