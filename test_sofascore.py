import asyncio
from playwright.async_api import async_playwright


SOFASCORE_URL = "https://www.sofascore.com/"


async def main():
    async with async_playwright() as p:
        print("Starting browser...")

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        def websocket_opened(ws):
            print(f"\n[WebSocket OPEN]")
            print(ws.url)

            ws.on(
                "framereceived",
                lambda payload: print(
                    f"\n[WebSocket RECEIVED]\n{payload}"
                )
            )

            ws.on(
                "framesent",
                lambda payload: print(
                    f"\n[WebSocket SENT]\n{payload}"
                )
            )

            ws.on(
                "close",
                lambda: print(
                    f"\n[WebSocket CLOSED]\n{ws.url}"
                )
            )

        page.on("websocket", websocket_opened)

        print(f"Opening: {SOFASCORE_URL}")

        await page.goto(
            SOFASCORE_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        print("Page loaded.")
        print("Waiting for WebSocket traffic...")

        await page.wait_for_timeout(30000)

        await browser.close()

        print("Browser closed.")


if __name__ == "__main__":
    asyncio.run(main())
