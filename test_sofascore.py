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

        # WebSocket
        def websocket_opened(ws):
            print("\n========== WEBSOCKET OPEN ==========")
            print(ws.url)

            ws.on(
                "framereceived",
                lambda payload: print(
                    f"\n[WS RECEIVED]\n{payload}"
                )
            )

            ws.on(
                "framesent",
                lambda payload: print(
                    f"\n[WS SENT]\n{payload}"
                )
            )

            ws.on(
                "close",
                lambda: print(
                    f"\n[WS CLOSED]\n{ws.url}"
                )
            )

        page.on("websocket", websocket_opened)

        # Network requests
        def request_sent(request):
            url = request.url

            if any(x in url.lower() for x in [
                "sofascore",
                "api",
                "event",
                "websocket",
                "ws"
            ]):
                print(f"\n[REQUEST]\n{url}")

        page.on("request", request_sent)

        print(f"Opening: {SOFASCORE_URL}")

        await page.goto(
            SOFASCORE_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        print("Page loaded.")
        print("Monitoring network traffic for 60 seconds...")

        await page.wait_for_timeout(60000)

        await browser.close()

        print("Browser closed.")


if __name__ == "__main__":
    asyncio.run(main())
