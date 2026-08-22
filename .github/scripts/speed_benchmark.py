import os
import sys
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

async def run_direct_download_benchmark():
    print("\n=== 2. DIRECT HTTP DOWNLOAD SPEED BENCHMARK ===")
    test_url = "https://speed.hetzner.de/100MB.bin"
    chunk_size = 1024 * 1024  # 1MB
    downloaded = 0

    try:
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(test_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    async for chunk in resp.content.iter_chunked(chunk_size):
                        downloaded += len(chunk)
                        if time.time() - start_time >= 5:
                            break
        duration = time.time() - start_time
        mb_downloaded = downloaded / (1024 * 1024)
        speed_mbps = (mb_downloaded * 8) / duration if duration > 0 else 0
        speed_mbs = mb_downloaded / duration if duration > 0 else 0

        print(f"  - Downloaded: {mb_downloaded:.2f} MB in {duration:.2f}s")
        print(f"  - HTTP Download Speed: {speed_mbps:.2f} Mbps ({speed_mbs:.2f} MB/s)")
        return speed_mbps, speed_mbs
    except Exception as e:
        print(f"  - HTTP Download Benchmark Failed: {e}")
        return 0, 0

async def main():
    print("==========================================")
    print("  AZML CODE & NETWORK SPEED BENCHMARK")
    print("==========================================\n")
    
    down_net, up_net, ping = await run_network_speedtest()
    http_mbps, http_mbs = await run_direct_download_benchmark()
    
    bot_token = os.environ.get("BOT_TOKEN")
    api_id = os.environ.get("TELEGRAM_API")
    api_hash = os.environ.get("TELEGRAM_HASH")

    print("\n=== 3. TELEGRAM BOT API STATUS ===")
    if bot_token and api_id and api_hash:
        print("  - Telegram Secrets Configured: YES")
        print("  - Telegram Pyrogram Speed Test Ready.")
    else:
        print("  - Telegram Secrets Configured: NO (Optional secrets BOT_TOKEN, TELEGRAM_API, TELEGRAM_HASH not set)")

    print("\n==========================================")
    print("  BENCHMARK SUMMARY")
    print("==========================================")
    print(f"| Metric | Speed (Mbps) | Speed (MB/s) |")
    print(f"|---|---|---|")
    print(f"| Server Download | {down_net:.2f} Mbps | {down_net/8:.2f} MB/s |")
    print(f"| Server Upload   | {up_net:.2f} Mbps | {up_net/8:.2f} MB/s |")
    print(f"| Direct Download | {http_mbps:.2f} Mbps | {http_mbs:.2f} MB/s |")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(main())
