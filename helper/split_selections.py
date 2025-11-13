import json
import os
import sys
from pathlib import Path


def validate_json_file(file_path):
    """Kiểm tra file tồn tại và là JSON hợp lệ"""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ Lỗi: File không tồn tại: {file_path}")
        return False
    if not path.is_file():
        print(f"❌ Lỗi: Đường dẫn không phải là file: {file_path}")
        return False
    try:
        with open(path, 'r', encoding='utf-8') as f:
            json.load(f)  # Thử parse
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Lỗi: File JSON không hợp lệ: {e}")
        return False
    except Exception as e:
        print(f"❌ Lỗi khi đọc file: {e}")
        return False


def get_user_input():
    """Thu thập thông tin từ người dùng"""
    print("🚀 CÔNG CỤ CHIA ICONS THÀNH CHUNKS")
    print("=" * 50)

    while True:
        input_file = input("Nhập đường dẫn file input (ví dụ: data/lawnicons/selection-all.json): ").strip()
        if not input_file:
            print("⚠️  Vui lòng không để trống!")
            continue
        if validate_json_file(input_file):
            break

    while True:
        output_dir = input("Nhập thư mục lưu kết quả (ví dụ: data/lawnicons/chunks): ").strip()
        if not output_dir:
            print("⚠️  Vui lòng không để trống!")
            continue
        output_path = Path(output_dir)
        if output_path.exists() and not output_path.is_dir():
            print("❌ Lỗi: Đường dẫn đã tồn tại nhưng không phải thư mục!")
            continue
        break

    while True:
        chunk_input = input("Nhập kích thước mỗi chunk (mặc định 500, nhấn Enter để dùng mặc định): ").strip()
        if not chunk_input:
            chunk_size = 500
            break
        try:
            chunk_size = int(chunk_input)
            if chunk_size <= 0:
                print("⚠️  Kích thước phải lớn hơn 0!")
                continue
            break
        except ValueError:
            print("⚠️  Vui lòng nhập số nguyên hợp lệ!")

    return input_file, output_dir, chunk_size


def split_into_chunks(input_file, output_dir, chunk_size=500):
    """Chia file JSON thành các chunk nhỏ"""
    print(f"\n🔄 Đang đọc file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'icons' not in data:
        print("❌ Lỗi: File JSON phải chứa key 'icons' là một mảng!")
        sys.exit(1)

    icons = data['icons']
    total = len(icons)
    print(f"✅ Tìm thấy {total} icons")

    # Tạo thư mục output
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"📁 Thư mục output: {output_path.resolve()}")

    # Metadata
    metadata = {
        "total_icons": total,
        "chunk_size": chunk_size,
        "prefix": data.get("prefix", "icon-"),
        "chunks": []
    }

    print(f"🔪 Đang chia thành các chunk (kích thước ~{chunk_size} icons/chunk)...")
    chunks_created = 0

    for i in range(0, total, chunk_size):
        chunk_icons = icons[i:i + chunk_size]
        chunk_index = chunks_created
        chunk_file = f"chunk_{chunk_index}.json"

        chunk_data = {
            "icons": chunk_icons,
            "index": chunk_index,
            "start": i,
            "end": min(i + chunk_size - 1, total - 1),
            "count": len(chunk_icons)
        }

        # Lưu chunk
        chunk_path = output_path / chunk_file
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)

        # Cập nhật metadata
        metadata["chunks"].append({
            "file": chunk_file,
            "start": i,
            "end": chunk_data["end"],
            "count": chunk_data["count"]
        })

        chunks_created += 1
        if chunks_created % 10 == 0 or chunks_created == 1:
            print(f"   → Đã tạo: {chunk_file} ({chunk_data['count']} icons)")

    # Lưu metadata
    metadata_path = output_path / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print(f"🎉 HOÀN TẤT!")
    print(f"   • Tổng icons: {total}")
    print(f"   • Số chunk: {chunks_created}")
    print(f"   • Chunk size: {chunk_size}")
    print(f"   • Metadata: {metadata_path.name}")
    print(f"   • Output: {output_path.resolve()}")
    print("=" * 50)


def main():
    try:
        input_file, output_dir, chunk_size = get_user_input()
        split_into_chunks(input_file, output_dir, chunk_size)
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã hủy bởi người dùng.")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Lỗi không xác định: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()