import asyncio
from playwright.async_api import async_playwright


SOFASCORE_URL = (
    "https://www.sofascore.com/football/match/"
    "neom-sc-al-khaleej/DUqbsGmme#id:16629472"
)


async def main():
    async with async_playwright() as p:
        print("Starting browser...")

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        # اتصال مستقیم به Chrome DevTools Protocol
        cdp = await page.context.new_cdp_session(page)

        # فعال کردن شنود شبکه
        await cdp.send("Network.enable")

        # WebSocket ساخته شد
        def websocket_created(params):
            print("\n========== WEBSOCKET CREATED ==========")
            print("URL:", params.get("url"))
            print("Request ID:", params.get("requestId"))

        cdp.on(
            "Network.webSocketCreated",
            websocket_created
        )

        # اتصال WebSocket برقرار شد
        def handshake(params):
            print("\n========== WEBSOCKET HANDSHAKE ==========")
            print("Status:", params["response"].get("status"))
            print("Status text:", params["response"].get("statusText"))

        cdp.on(
            "Network.webSocketHandshakeResponseReceived",
            handshake
        )

        # پیام دریافتی از WebSocket
        def websocket_received(params):
            response = params.get("response", {})
            payload = response.get("payloadData", "")

            print("\n========== WEBSOCKET RECEIVED ==========")
            print(payload)

        cdp.on(
            "Network.webSocketFrameReceived",
            websocket_received
        )

        # پیام ارسالی به WebSocket
        def websocket_sent(params):
            response = params.get("response", {})
            payload = response.get("payloadData", "")

            print("\n========== WEBSOCKET SENT ==========")
            print(payload)

        cdp.on(
            "Network.webSocketFrameSent",
            websocket_sent
        )

        # خطای WebSocket
        def websocket_error(params):
            print("\n========== WEBSOCKET ERROR ==========")
            print(params)

        cdp.on(
            "Network.webSocketFrameError",
            websocket_error
        )

        # WebSocket بسته شد
        def websocket_closed(params):
            print("\n========== WEBSOCKET CLOSED ==========")
            print(params.get("requestId"))

        cdp.on(
            "Network.webSocketClosed",
            websocket_closed
        )

        print(f"Opening: {SOFASCORE_URL}")

        await page.goto(
            SOFASCORE_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        print("Page loaded.")
        print("Monitoring Chrome network events for 60 seconds...")

        await page.wait_for_timeout(60000)

        await browser.close()

        print("Browser closed.")


if __name__ == "__main__":
    asyncio.run(main())
