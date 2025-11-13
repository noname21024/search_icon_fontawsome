# merge-selections.py
import os
import json
import sys

def input_path(prompt):
    path = input(prompt).strip().strip('"')
    if not os.path.isdir(path):
        print("❌ Đường dẫn không hợp lệ.")
        sys.exit(1)
    return path

def input_save_path(prompt):
    path = input(prompt).strip().strip('"')
    dir_part = os.path.dirname(path)
    if dir_part and not os.path.isdir(dir_part):
        try:
            os.makedirs(dir_part)
        except:
            print("❌ Không thể tạo thư mục đích.")
            sys.exit(1)
    return path

print("=== 📂 GỘP selection.json TỪ NHIỀU BATCH ===")
root_dir = input_path("📁 Nhập đường dẫn chứa các batch (batch1-v1.0, batch2-v1.0, ...): ")

# Tự động tìm batch theo pattern batch{N}-v1.0
batch_dirs = []
for entry in os.listdir(root_dir):
    full_path = os.path.join(root_dir, entry)
    if os.path.isdir(full_path) and entry.startswith("batch") and "-v1.0" in entry:
        batch_dirs.append(entry)

if not batch_dirs:
    print("❌ Không tìm thấy batch nào có dạng batchX-v1.0")
    sys.exit(1)

batch_dirs.sort(key=lambda x: int(''.join(filter(str.isdigit, x.split('-')[0]))) if any(c.isdigit() for c in x) else 999)
print(f"🔍 Phát hiện {len(batch_dirs)} batch: {', '.join(batch_dirs)}")

# Gộp dữ liệu
merged = {
    "icons": [],
    "height": 1024,
    "metadata": {
        "author": "merged-by-script",
        "homepage": "",
        "name": "lawnicons-all",
        "url": ""
    },
    "preferences": {
        "fontPref": {
            "prefix": "icons-",
            "metadata": "",
            "embed": True
        }
    }
}

seen_names = set()
total_icons = 0

for i, batch in enumerate(batch_dirs, 1):
    sel_path = os.path.join(root_dir, batch, "selection.json")
    if not os.path.isfile(sel_path):
        print(f"⚠️  Batch {i}: thiếu selection.json → bỏ qua")
        continue

    try:
        with open(sel_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Batch {i} ({batch}): lỗi đọc JSON → {e}")
        continue

    icons = data.get("icons", [])
    print(f"✅ Batch {i} ({batch}): {len(icons)} icon")

    for icon in icons:
        # Lấy tên duy nhất để tránh trùng
        name = icon.get("properties", {}).get("name") or icon.get("attrs", [{}])[0].get("name", "")
        if not name:
            continue
        if name in seen_names:
            # Tự động đổi tên nếu trùng: home → home_2, home_3...
            base = name
            counter = 2
            while name in seen_names:
                name = f"{base}_{counter}"
                counter += 1
            # Cập nhật lại tên trong icon
            if "properties" in icon and "name" in icon["properties"]:
                icon["properties"]["name"] = name
            elif "attrs" in icon and icon["attrs"] and "name" in icon["attrs"][0]:
                icon["attrs"][0]["name"] = name

        seen_names.add(name)
        merged["icons"].append(icon)
        total_icons += 1

print(f"\n📊 Tổng cộng: {total_icons} icon sau khi gộp (đã xử lý trùng tên)")

# Hỏi nơi lưu
output_path = input_save_path(
    "💾 Nhập đường dẫn lưu file gộp (ví dụ: D:/icon/data/lawnicons/selection-all.json): "
)

try:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"\n🎉 Thành công! Đã lưu vào:\n   {output_path}")
    print("\n💡 Bạn có thể:")
    print("- Import file này vào Icomoon (Import Icons → JSON)")
    print("- Dùng để sinh lại font/CSS nếu cần")
except Exception as e:
    print(f"❌ Lỗi khi ghi file: {e}")
    sys.exit(1)