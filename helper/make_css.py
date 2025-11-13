import os
import json
import sys
import re
from typing import List

def input_path(prompt):
    """
    Yêu cầu người dùng nhập đường dẫn và kiểm tra tính hợp lệ của thư mục.
    """
    path = input(prompt).strip().strip('"')
    if not os.path.isdir(path):
        print("❌ Đường dẫn không hợp lệ. Vui lòng thử lại.")
        sys.exit(1)
    return path

def find_batch_dirs(root_dir: str) -> List[str]:
    """
    Tìm tất cả các thư mục con khớp với mẫu 'batchX...' và sắp xếp chúng theo thứ tự số.
    """
    found_batches = []
    # Mẫu regex linh hoạt hơn:
    # - Bắt đầu bằng 'batch'
    # - Sau đó là một hoặc nhiều chữ số (\d+)
    # - Có thể theo sau bởi bất kỳ ký tự nào (-, _, .)
    batch_pattern = re.compile(r'batch(\d+)[^\d]*.*')
    
    print(f"DEBUG: Đang quét thư mục: {root_dir}")

    for item in os.listdir(root_dir):
        full_path = os.path.join(root_dir, item)
        if os.path.isdir(full_path):
            match = batch_pattern.match(item)
            if match:
                # Lấy số thứ tự (ví dụ: '1' từ 'batch1-v1.0')
                try:
                    batch_number = int(match.group(1))
                    found_batches.append((batch_number, item))
                    print(f"DEBUG: Tìm thấy thư mục batch hợp lệ: {item} (Số thứ tự: {batch_number})")
                except ValueError:
                    print(f"DEBUG: Bỏ qua thư mục: {item} (Không trích xuất được số)")
            else:
                print(f"DEBUG: Bỏ qua thư mục: {item} (Không khớp mẫu)")

    # Sắp xếp theo số thứ tự batch
    found_batches.sort(key=lambda x: x[0])
    
    return [name for num, name in found_batches]


def generate_css():
    print("=== 🎨 GENERATE CSS TỪ SELECTION.JSON ===")
    
    # 1. Hỏi tên Collection
    raw_collection_name = input("🌟 Nhập tên Collection (ví dụ: MyCustomIcons): ").strip()
    if not raw_collection_name:
        print("❌ Tên Collection không được để trống.")
        sys.exit(1)

    # --- BƯỚC SỬA LỖI: LÀM SẠCH TÊN COLLECTION ---
    # Nếu người dùng nhập đường dẫn, chỉ lấy tên file cơ sở (không có đuôi .json)
    if os.path.sep in raw_collection_name or ':' in raw_collection_name:
        collection_base = os.path.basename(raw_collection_name)
        collection_base = os.path.splitext(collection_base)[0]
    else:
        collection_base = raw_collection_name
    
    # Chuẩn hóa tên cho CSS (viết thường, không khoảng trắng, chỉ giữ lại chữ, số, gạch ngang, gạch dưới)
    font_name = re.sub(r'[^\w\d\-\_]', '', collection_base.lower().replace(" ", "").replace("-", ""))
    
    if not font_name:
         print("❌ Tên Collection không hợp lệ sau khi chuẩn hóa. Vui lòng nhập tên đơn giản hơn.")
         sys.exit(1)
         
    # Sử dụng tên gốc đã làm sạch cho tiêu đề (ví dụ: Selections All)
    collection_title = collection_base.replace('_', ' ').replace('-', ' ').title()
    # --------------------------------------------------------
    
    root_dir = input_path("📁 Nhập đường dẫn thư mục chứa các thư mục batch: ")

    # 2. Tự động phát hiện batch (sử dụng logic linh hoạt)
    batch_dirs = find_batch_dirs(root_dir)

    if not batch_dirs:
        print("❌ Không tìm thấy thư mục batch nào theo mẫu 'batchX...' bên trong thư mục này.")
        sys.exit(1)

    print(f"🔍 Phát hiện {len(batch_dirs)} batch: {', '.join(batch_dirs)}")

    # 3. Đọc toàn bộ icon
    all_icons = {}
    total = 0

    for batch_dir in batch_dirs:
        # Giả định file selection.json nằm trong thư mục con của batch
        sel_path = os.path.join(root_dir, batch_dir, "selection.json")
        if not os.path.exists(sel_path):
            # Nếu không tìm thấy, thử tìm file json với tên batch
            json_name = batch_dir.split('-')[0] + '.json'
            sel_path = os.path.join(root_dir, batch_dir, json_name)
            if not os.path.exists(sel_path):
                 print(f"⚠️ Bỏ qua: thiếu selection.json hoặc {json_name} trong {batch_dir}")
                 continue

        try:
            with open(sel_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Lỗi đọc {sel_path}: {e}")
            continue

        # Prefix: thử từ metadata → fallback đến tên font động + "-"
        prefix_fallback = f"{font_name}-"
        prefix = data.get("metadata", {}).get("prefix", prefix_fallback)
        
        # Đảm bảo prefix kết thúc bằng dấu gạch ngang
        if not prefix.endswith('-') and prefix:
            prefix += '-'

        for item in data.get("icons", []):
            # Lấy code & name
            code = item.get("properties", {}).get("code")
            name = item.get("properties", {}).get("name")

            if code is None:
                # Thử cấu trúc cũ
                code = item.get("attrs", [{}])[0].get("code")
            if name is None:
                # Thử cấu trúc cũ
                name = item.get("attrs", [{}])[0].get("name")

            if not name or code is None:
                continue

            # Xây dựng full class (ví dụ: icons-home)
            full_class = f"{prefix}{name}"
            if full_class in all_icons:
                continue

            # CSS \xxxx (hỗ trợ > U+FFFF)
            if isinstance(code, str) and code.startswith('0x'):
                 # Nếu code là chuỗi hex
                 code_int = int(code, 16)
            elif isinstance(code, int):
                 code_int = code
            else:
                 continue

            if code_int > 0xFFFF:
                hex_code = f"{code_int:X}"
                css_code = f"\\{hex_code} "
            else:
                css_code = f"\\{code_int:04X}"

            all_icons[full_class] = css_code
            total += 1

    if not all_icons:
        print("❌ Không tìm thấy icon nào trong các selection.json!")
        sys.exit(1)

    print(f"✅ Đã đọc {total} icon.")

    # 4. Hỏi nơi lưu CSS
    default_css_filename = f"{font_name}-all.css"
    css_path = input(f"💾 Nhập đường dẫn đầy đủ để lưu file CSS (Enter để dùng mặc định: {root_dir}/{default_css_filename}): ").strip().strip('"')
    if not css_path:
        css_path = os.path.join(root_dir, default_css_filename)
        
    os.makedirs(os.path.dirname(css_path) if os.path.dirname(css_path) else ".", exist_ok=True)

    # Tên font file
    font_file_base = f"{font_name}-all"

    # 5. Ghi CSS
    # Lấy prefix cuối cùng được sử dụng
    final_prefix_selector = prefix.rstrip('-') if prefix else font_name
    
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(f"""/* Generated by generate-css.py (Collection: {collection_title}) */
@font-face {{
  font-family: '{font_name}';
  src: url('{font_file_base}.woff2') format('woff2'),
       url('{font_file_base}.woff') format('woff');
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}}

/* Áp dụng font cho mọi class bắt đầu bằng '{final_prefix_selector}-' */
i[class^="{final_prefix_selector}-"],
span[class^="{final_prefix_selector}-"] {{
  font-family: '{font_name}' !important;
  speak: never;
  font-style: normal;
  font-weight: normal;
  font-variant: normal;
  text-transform: none;
  line-height: 1;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}

/* Các icon */
""")
        for cls, content in sorted(all_icons.items()):
            f.write(f".{cls}::before {{ content: \"{content}\"; }}\n")

    print(f"\n🎉 Hoàn tất! Đã lưu CSS vào:\n   {css_path}")
    print("\n📌 Lưu ý:")
    print(f"- Đảm bảo `{font_file_base}.woff2` và `{font_file_base}.woff` nằm cùng thư mục với file CSS.")
    print(f"- Dùng trong HTML: <i class=\"{prefix}xxx\"></i>")

if __name__ == "__main__":
    generate_css()