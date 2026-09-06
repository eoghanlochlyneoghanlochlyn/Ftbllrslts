import json
import os
from datetime import datetime

import requests


# ============================================================
# تنظیمات
# ============================================================

MATCH_DETAILS_URL = "https://www.fotmob.com/api/data/matchDetails"

MATCHES = {
    "match_5749667": {
        "name": "مسابقه 5749667",
        "id": "5749667",
    },
    "match_588762": {
        "name": "مسابقه 588762",
        "id": "588762",
    },
}

OUTPUT_DIR = "fotmob_raw"


# ============================================================
# هدرهای درخواست
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.fotmob.com/",
    "Origin": "https://www.fotmob.com",
}


# ============================================================
# دریافت اطلاعات مسابقه
# ============================================================

def get_match_details(match_id):
    params = {
        "matchId": match_id
    }

    print(
        f"   ↳ درخواست اطلاعات مسابقه {match_id}"
    )

    try:
        response = requests.get(
            MATCH_DETAILS_URL,
            params=params,
            headers=HEADERS,
            timeout=30,
        )

    except requests.RequestException as error:
        print(
            f"   ❌ خطای اتصال: {error}"
        )
        return None

    print(
        f"   ↳ HTTP {response.status_code}"
    )

    if response.status_code != 200:
        print(
            "   ❌ دریافت اطلاعات ناموفق بود."
        )
        print(
            f"   ↳ پاسخ: {response.text[:1000]}"
        )
        return None

    try:
        data = response.json()

    except ValueError:
        print(
            "   ❌ پاسخ دریافت‌شده JSON معتبر نیست."
        )
        print(
            f"   ↳ پاسخ: {response.text[:1000]}"
        )
        return None

    print(
        "   ✅ پاسخ JSON با موفقیت دریافت شد."
    )

    return data


# ============================================================
# نمایش ساختار JSON
# ============================================================

def print_structure(
    value,
    path="root",
    depth=0,
    max_depth=6,
):
    indent = "  " * depth

    if depth > max_depth:
        print(
            f"{indent}{path}: ..."
        )
        return

    if isinstance(value, dict):

        print(
            f"{indent}{path}: "
            f"OBJECT ({len(value)} کلید)"
        )

        for key, child in value.items():

            child_path = (
                f"{path}.{key}"
            )

            if isinstance(child, dict):

                print_structure(
                    child,
                    child_path,
                    depth + 1,
                    max_depth,
                )

            elif isinstance(child, list):

                print(
                    f"{'  ' * (depth + 1)}"
                    f"{child_path}: "
                    f"ARRAY ({len(child)} آیتم)"
                )

                if len(child) > 0:

                    first_item = child[0]

                    if isinstance(
                        first_item,
                        dict,
                    ):

                        print_structure(
                            first_item,
                            f"{child_path}[0]",
                            depth + 2,
                            max_depth,
                        )

                    elif isinstance(
                        first_item,
                        list,
                    ):

                        print_structure(
                            first_item,
                            f"{child_path}[0]",
                            depth + 2,
                            max_depth,
                        )

                    else:

                        print(
                            f"{'  ' * (depth + 2)}"
                            f"{child_path}[0]: "
                            f"{type(first_item).__name__}"
                        )

            else:

                print(
                    f"{'  ' * (depth + 1)}"
                    f"{child_path}: "
                    f"{type(child).__name__}"
                )

    elif isinstance(value, list):

        print(
            f"{indent}{path}: "
            f"ARRAY ({len(value)} آیتم)"
        )

        if len(value) > 0:

            print_structure(
                value[0],
                f"{path}[0]",
                depth + 1,
                max_depth,
            )

    else:

        print(
            f"{indent}{path}: "
            f"{type(value).__name__}"
        )


# ============================================================
# ذخیره پاسخ خام
# ============================================================

def save_raw_json(
    match_id,
    match_name,
    data,
):
    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    filename = (
        f"fotmob_raw_{match_id}.json"
    )

    filepath = os.path.join(
        OUTPUT_DIR,
        filename,
    )

    output = {
        "saved_at": (
            datetime.utcnow().isoformat()
            + "Z"
        ),
        "match_id": match_id,
        "match_name": match_name,
        "data": data,
    }

    try:

        with open(
            filepath,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                output,
                file,
                ensure_ascii=False,
                indent=2,
            )

    except OSError as error:

        print(
            f"   ❌ خطا در ذخیره فایل: {error}"
        )
        return False

    print(
        f"   💾 فایل ذخیره شد: {filepath}"
    )

    return True


# ============================================================
# بررسی یک مسابقه
# ============================================================

def inspect_match(
    match_id,
    match_name,
):

    print()
    print("=" * 70)
    print(
        f"⚽ {match_name}"
    )
    print(
        f"🆔 شناسه: {match_id}"
    )
    print("=" * 70)

    data = get_match_details(
        match_id
    )

    if data is None:
        print(
            "❌ اطلاعات مسابقه دریافت نشد."
        )
        return False

    print()
    print(
        "🔍 ساختار پاسخ دریافت‌شده:"
    )
    print("-" * 70)

    print_structure(
        data,
        path="data",
    )

    print("-" * 70)

    saved = save_raw_json(
        match_id,
        match_name,
        data,
    )

    if saved:
        print(
            "✅ بررسی مسابقه با موفقیت انجام شد."
        )
    else:
        print(
            "⚠️ دریافت موفق بود ولی ذخیره فایل انجام نشد."
        )

    return saved


# ============================================================
# اجرای اصلی
# ============================================================

def main():

    print("=" * 70)
    print(
        "⚽ آزمایش اطلاعات خام فوت‌موب"
    )
    print("=" * 70)

    print()
    print(
        "تعداد مسابقه‌ها: "
        f"{len(MATCHES)}"
    )

    print()

    for match_info in MATCHES.values():

        print(
            f"  • {match_info['id']}"
        )

    success_count = 0

    for match_info in MATCHES.values():

        success = inspect_match(
            match_info["id"],
            match_info["name"],
        )

        if success:
            success_count += 1

    print()
    print("=" * 70)
    print(
        "🏁 آزمایش به پایان رسید"
    )
    print("=" * 70)

    print(
        f"✅ موفق: {success_count} "
        f"از {len(MATCHES)}"
    )

    print()
    print(
        f"📁 فایل‌ها در پوشه "
        f"'{OUTPUT_DIR}' ذخیره شدند."
    )


# ============================================================
# شروع برنامه
# ============================================================

if __name__ == "__main__":
    main()
