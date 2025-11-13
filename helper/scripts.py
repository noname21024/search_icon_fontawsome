import os
import sys
import subprocess
import re
from fontTools.ttLib import TTFont

def input_path(prompt):
    """
    Yêu cầu người dùng nhập đường dẫn và kiểm tra tính hợp lệ của thư mục.
    """
    path = input(prompt).strip().strip('"')
    if not os.path.isdir(path):
        print("❌ Đường dẫn không hợp lệ. Vui lòng thử lại.")
        sys.exit(1)
    return path

def find_batch_dirs(root_dir):
    """
    Tìm tất cả các thư mục con khớp với mẫu 'batchX-vY.Z' và sắp xếp chúng theo thứ tự số.
    Trả về danh sách các tên thư mục đã được sắp xếp.
    """
    found_batches = []
    # Mẫu regex: batch[số]-v[số].[số]
    batch_pattern = re.compile(r'batch(\d+)-v\d+\.\d+')

    for item in os.listdir(root_dir):
        if os.path.isdir(os.path.join(root_dir, item)):
            match = batch_pattern.match(item)
            if match:
                # Lấy số thứ tự (ví dụ: '1' từ 'batch1-v1.0')
                batch_number = int(match.group(1))
                found_batches.append((batch_number, item))

    # Sắp xếp theo số thứ tự batch
    found_batches.sort(key=lambda x: x[0])
    
    return [name for num, name in found_batches]

def input_font_name():
    """
    Yêu cầu người dùng nhập tên font mong muốn và trả về tên đó.
    """
    # Loại bỏ ký tự không hợp lệ cho tên file
    invalid_chars = r'[\\/:*?"<>|]'
    while True:
        name = input("\n📝 Nhập tên font mới (ví dụ: my-icon-font): ").strip()
        if not name:
            print("❌ Tên font không được để trống.")
        elif re.search(invalid_chars, name):
            print(f"❌ Tên font chứa ký tự không hợp lệ. Vui lòng tránh: {invalid_chars}")
        else:
            return name

print("=== 🛠️ MERGE FONT ICONS (Dynamic Batch) ===")
root_dir = input_path("📁 Nhập đường dẫn thư mục chứa các thư mục batch (ví dụ: D:\\icons\\all_batches): ")

# 1. Tự động tìm kiếm các thư mục batch
batch_dirs = find_batch_dirs(root_dir)

if not batch_dirs:
    print("❌ Không tìm thấy thư mục batch nào theo mẫu 'batchX-vY.Z' bên trong thư mục này.")
    sys.exit(1)
    
print(f"✅ Đã tìm thấy {len(batch_dirs)} thư mục batch. Danh sách: {', '.join(batch_dirs)}")

# *** PHẦN THÊM MỚI/CHỈNH SỬA ***
# 2. Hỏi tên font mong muốn
custom_font_name = input_font_name()
print(f"→ Tên font sẽ là: **{custom_font_name}**")
# *** KẾT THÚC PHẦN THÊM MỚI/CHỈNH SỬA ***

# 3. Xây dựng danh sách đường dẫn font WOFF
woff_paths = []
for b in batch_dirs:
    # Tên font (ví dụ: 'batch1' từ 'batch1-v1.0')
    font_name = b.split('-')[0]
    woff_path = os.path.join(root_dir, b, "fonts", f"{font_name}.woff")
    
    if not os.path.isfile(woff_path):
        print(f"❌ Không tìm thấy font: {woff_path}. Vui lòng kiểm tra cấu trúc thư mục.")
        sys.exit(1)
        
    woff_paths.append(woff_path)

print(f"\n🔧 Đang merge {len(woff_paths)} font bằng pyftmerge...")

# 4. Thực hiện merge font
try:
    # Lệnh pyftmerge yêu cầu danh sách các đường dẫn font
    result = subprocess.run(["pyftmerge"] + woff_paths, cwd=root_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Lỗi khi chạy pyftmerge:")
        print(result.stderr)
        sys.exit(1)
except FileNotFoundError:
    print("❌ 'pyftmerge' không tìm thấy. Vui lòng cài fonttools: pip install fonttools")
    sys.exit(1)

# Tìm merged.ttf (pyftmerge tạo file này trong thư mục làm việc)
merged_ttf = os.path.join(root_dir, "merged.ttf")
if not os.path.exists(merged_ttf):
    print("❌ merged.ttf không được tạo. Có thể do lỗi font hoặc quyền truy cập.")
    sys.exit(1)

# *** PHẦN CHỈNH SỬA: Đổi tên thành tên font người dùng nhập ***
# Đổi tên → custom_font_name.ttf
ttf_path = os.path.join(root_dir, f"{custom_font_name}.ttf")
os.replace(merged_ttf, ttf_path)
print(f"✅ Đã tạo: {ttf_path}")

# 5. Nén → .woff & .woff2
print("🔧 Đang tạo .woff & .woff2...")
try:
    font = TTFont(ttf_path)
    
    # Tạo WOFF
    woff_path = os.path.join(root_dir, f"{custom_font_name}.woff")
    font.flavor = "woff"
    font.save(woff_path)
    print(f"✅ {woff_path}")

    # Tạo WOFF2 (Yêu cầu thư viện brotli)
    woff2_path = os.path.join(root_dir, f"{custom_font_name}.woff2")
    font.flavor = "woff2"
    font.save(woff2_path)
    print(f"✅ {woff2_path}")

    font.close()
except Exception as e:
    print(f"⚠️ Lỗi tạo .woff2 (có thể thiếu brotli): {e}")
    print("→ Đang thử tạo .woff thôi...")
    try:
        font = TTFont(ttf_path)
        # Tạo WOFF (fallback)
        woff_path = os.path.join(root_dir, f"{custom_font_name}.woff") # Cần phải khai báo lại trong khối này nếu nó là khối độc lập
        font.flavor = "woff"
        font.save(woff_path)
        font.close()
        print(f"✅ {woff_path} (chỉ có .woff)")
    except Exception as e_fallback:
        print(f"❌ Không thể tạo font. Dừng. Lỗi: {e_fallback}")
        sys.exit(1)

print("\n🎉 Hoàn tất! Font đã sẵn sàng.")
print("→ Tiếp theo: chạy `generate-css.py`")