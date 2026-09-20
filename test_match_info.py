from fotmob import fetch_match_page, extract_next_data

MATCH_ID = "6050065"

TARGET_WORDS = (
"round",
"week",
"matchweek",
"gameweek",
"stage",
)

def looks_relevant(key):
if not isinstance(key, str):
return False

```
key_lower = key.lower()

return any(
    word in key_lower
    for word in TARGET_WORDS
)
```

def walk(node, path=()):
if isinstance(node, dict):
for key, value in node.items():
current_path = path + (str(key),)

```
        if looks_relevant(key):
            print()
            print("=" * 100)
            print("KEY:")
            print(".".join(current_path))
            print("VALUE TYPE:")
            print(type(value).__name__)
            print("VALUE:")

            if isinstance(value, (dict, list)):
                print(repr(value)[:5000])
            else:
                print(repr(value))

        walk(value, current_path)

elif isinstance(node, list):
    for index, item in enumerate(node):
        current_path = path + (f"[{index}]",)
        walk(item, current_path)
```

def main():
print(f"Fetching FotMob page for match {MATCH_ID}...")

```
html = fetch_match_page(MATCH_ID)

if not html:
    print("ERROR: Could not fetch FotMob page.")
    return

print(f"HTML length: {len(html)}")

data = extract_next_data(html)

if not isinstance(data, dict):
    print("ERROR: Could not extract __NEXT_DATA__.")
    return

print("NEXT_DATA extracted successfully.")
print()
print("Searching for round/week/stage related keys...")

walk(data)

print()
print("=" * 100)
print("TEST FINISHED.")
```

if **name** == "**main**":
main()
