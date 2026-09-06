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
# دریافت اطلاعات خام
# ============================================================

def get_match_details(match_id):
    """
    دریافت پاسخ خام matchDetails از فوت‌موب.
    """

    params = {
        "matchId": match_id
    }

    print(f"   ↳ درخواست matchDetails برای شناسه {match_id}")

    try:
        response = requests.get(
            MATCH_DETAILS_URL,
            params=params,
            headers=HEADERS,
            timeout=30,
        )

        print(f"   ↳ HTTP {response.status_code}")

        if response.status_code != 200:
            print("   ❌ دریافت اطلاعات ناموفق بود.")
            print(
                f"   ↳ متن پاسخ: "
                f"{response.text[:1000]}"
            )
            return None

        try:
            data = response.json()

        except Exception as e:
            print(
                f"   ❌ پاسخ JSON معتبر نیست: {e}"
            )

            print(
                f"   ↳ متن پاسخ: "
                f"{response.text[:1000]}"
            )

            return None

        print(
            "   ✅ پاسخ JSON با موفقیت دریافت شد."
        )

        return data

    except requests.RequestException as e:

        print(
            f"   ❌ خطای درخواست: {e}"
        )

        return None


# ============================================================
# نمایش ساختار JSON
# ============================================================

def print_structure(
    value,
    path="root",
    depth=0,
    max_depth=5,
):
    """
    فقط ساختار JSON را چاپ می‌کند.
    مقدارهای بزرگ چاپ نمی‌شوند.
    """

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

            child_path = f"{path}.{key}"

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

                if child:

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

        if value:

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
# ذخیره JSON خام
# ============================================================

def save_raw_json(
    match_key,
    match_name,
    match_id,
    data,
):
    """
    ذخیره کامل پاسخ خام فوت‌موب.
    """

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

    wrapper = {
        "saved_at": (
            datetime.utcnow().isoformat()
            + "Z"
        ),
        "match_key": match_key,
        "match_name": match_name,
        "match_id": match_id,
        "data": data,
    }

    try:

        with open(
            filepath,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                wrapper,
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(
            f"   💾 فایل ذخیره شد: "
            f"{filepath}"
        )

        return filepath

    except Exception as e:

        print(
            f"   ❌ خطا در ذخیره فایل: {e}"
        )

        return None


# ============================================================
# بررسی یک مسابقه
# ============================================================

def inspect_match(
    match_key,
    match_info,
):

    match_name = match_info["name"]
    match_id = match_info["id"]

    print()
    print("=" * 70)
    print(f"⚽ {match_name}")
    print(f"🆔 شناسه: {match_id}")
    print("=" * 70)

    data = get_match_details(
        match_id
    )

    if data is None:

        print(
            "❌ اطلاعاتی برای این مسابقه "
            "دریافت نشد."
        )

        return False

    print()
    print(
        "🔍 ساختار پاسخ JSON:"
    )

    print("-" * 70)

    print_structure(
        data,
        path="data",
        depth=0,
        max_depth=5,
    )

    print()
    print("-" * 70)

    filepath = save_raw_json(
        match_key,
        match_name,
        match_id,
        data,
    )

    if
