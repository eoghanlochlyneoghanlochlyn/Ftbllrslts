import { SofascoreRepository } from "@devneonix/sofascore-api";

const EVENT_ID = "15655701";

async function main() {
    console.log("🔎 تست پروژه DevNeonix");
    console.log("🆔 Event ID:", EVENT_ID);
    console.log();

    try {
        console.log("📦 دریافت اطلاعات کامل مسابقه...");
        console.log("=" .repeat(80));

        const fullData =
            await SofascoreRepository.getEventFullData(
                "football",
                EVENT_ID
            );

        console.log(
            JSON.stringify(
                fullData,
                null,
                2
            )
        );

        console.log();
        console.log("=" .repeat(80));
        console.log("👥 دریافت ترکیب...");
        console.log("=" .repeat(80));

        const lineups =
            await SofascoreRepository.getLineups(
                EVENT_ID
            );

        console.log(
            JSON.stringify(
                lineups,
                null,
                2
            )
        );

    } catch (error) {

        console.error();
        console.error("❌ خطا:");

        if (error.response) {
            console.error(
                "HTTP:",
                error.response.status
            );

            console.error(
                JSON.stringify(
                    error.response.data,
                    null,
                    2
                )
            );
        } else {
            console.error(
                error.message
            );
        }

        process.exit(1);
    }
}

main();
