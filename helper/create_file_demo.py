import re
import os
import argparse
import sys
import json

def extract_icons_from_json(json_file_path):
    """
    Đọc và trích xuất danh sách icons từ file JSON selections.json (hoặc tương tự)
    """
    try:
        if not os.path.exists(json_file_path):
            print(f"Lỗi: Không tìm thấy file JSON: {json_file_path}")
            return None
            
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
    except json.JSONDecodeError:
        print(f"Lỗi: File {json_file_path} không phải là JSON hợp lệ.")
        return None
    except Exception as e:
        print(f"Lỗi khi đọc file JSON: {str(e)}")
        return None
    
    icons = []
    
    # Kiểm tra cấu trúc JSON (giả định có mảng 'icons' hoặc chính nó là mảng)
    if 'icons' in data and isinstance(data['icons'], list):
        icon_list = data['icons']
    elif isinstance(data, list):
        # Trường hợp file JSON chỉ chứa mảng icons
        icon_list = data
    else:
        print("Lỗi: Không tìm thấy mảng 'icons' hoặc cấu trúc JSON không khớp.")
        return []

    print(f"Đã tìm thấy {len(icon_list)} mục trong file JSON.")
    
    for item in icon_list:
        try:
            # Trích xuất tên và mã code (theo cấu trúc selections.json bạn cung cấp)
            name = item['properties']['name']
            code_int = item['properties']['code']
            
            # Chuyển đổi mã code (integer) sang unicode hex string
            unicode = f"{code_int:x}" 
            
            # Tạo label đẹp từ tên icon
            label = name.replace('_', ' ').replace('-', ' ')
            label = ' '.join(word.capitalize() for word in label.split())
            
            icons.append({
                'name': name,
                'label': label,
                'unicode': unicode,
                'class': f'icons-{name}' # Giả định tiền tố class vẫn là 'icons-'
            })
        except KeyError as e:
            print(f"Cảnh báo: Bỏ qua một icon do thiếu key: {e} trong mục JSON.")
            continue
            
    return icons

def generate_icon_demo(input_css_file, input_json_file, output_html_file, collection_title="Icon Collection"):
    """
    Tạo file HTML demo hiển thị tất cả các icon từ file JSON.
    """
    
    # 1. Đọc và trích xuất icons từ JSON (Ưu tiên nguồn dữ liệu chính xác)
    icons = extract_icons_from_json(input_json_file)
    if not icons:
        print("Lỗi: Không thể trích xuất icon từ file JSON. Hủy tạo file demo.")
        return False

    print(f"✅ Đã trích xuất {len(icons)} icons duy nhất từ JSON.")
    
    # 2. Kiểm tra file CSS (Chỉ để lấy tên file cho HTML link)
    if not os.path.exists(input_css_file):
        print(f"Cảnh báo: Không tìm thấy file CSS: {input_css_file}. File HTML demo sẽ không hiển thị icon đúng cách.")

    # --- TẠO CHUỖI ICON HTML ---
    icon_cards_html = []
    for icon in icons:
        # Xác định category (Ứng dụng/Công cụ)
        category = 'apps' if 'app' in icon['name'].lower() or 'app' in icon['label'].lower() else 'tools'
        
        # Tạo HTML cho thẻ icon
        card_html = f"""
        <div class="icon-card" data-name="{icon['name']}" data-label="{icon['label']}" data-category="{category}">
            <i class="{icon['class']}"></i>
            <div class="icon-name">{icon['name']}</div>
            <div class="icon-label">{icon['label']}</div>
            <div class="tooltip">Nhấp để sao chép mã</div>
        </div>
        """
        icon_cards_html.append(card_html)
    
    # Ghép tất cả các thẻ icon lại thành một chuỗi duy nhất
    icon_grid_content = ''.join(icon_cards_html)
    # --------------------------------------------------------
    
    # Lấy tên file CSS cơ sở để nhúng vào HTML
    css_file_name = os.path.basename(input_css_file)

    # Tạo nội dung HTML chính
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Collection Demo - {collection_title}</title>
    <link rel="stylesheet" href="{css_file_name}">
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .search-container {{
            max-width: 800px;
            margin: 0 auto 30px;
            position: relative;
        }}
        
        .search-container input {{
            width: 100%;
            padding: 15px 20px;
            border: none;
            border-radius: 50px;
            font-size: 16px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }}
        
        .search-container input:focus {{
            outline: none;
            box-shadow: 0 2px 15px rgba(102, 126, 234, 0.4);
        }}
        
        .stats {{
            text-align: center;
            margin: 20px 0;
            font-size: 1.2rem;
            color: #555;
        }}
        
        .icon-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .icon-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }}
        
        .icon-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .icon-card i {{
            font-size: 2.5rem;
            margin-bottom: 15px;
            color: #4a6cf7;
            display: block;
        }}
        
        .icon-name {{
            font-weight: 600;
            font-size: 0.9rem;
            color: #1e293b;
            margin-bottom: 5px;
            word-wrap: break-word;
        }}
        
        .icon-label {{
            font-size: 0.85rem;
            color: #64748b;
            font-style: italic;
            min-height: 1.5em;
        }}
        
        .tooltip {{
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%) translateY(10px);
            background: #333;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s;
            white-space: nowrap;
            z-index: 1000;
        }}
        
        .icon-card:hover .tooltip {{
            opacity: 1;
            visibility: visible;
            transform: translateX(-50%) translateY(0);
        }}
        
        .copied {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateX(200%);
            transition: transform 0.3s ease;
            z-index: 1000;
        }}
        
        .copied.show {{
            transform: translateX(0);
        }}
        
        .filter-container {{
            display: flex;
            justify-content: center;
            margin: 20px 0;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            background: #e2e8f0;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .filter-btn:hover, .filter-btn.active {{
            background: #4a6cf7;
            color: white;
        }}
        
        @media (max-width: 768px) {{
            .icon-grid {{
                grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Collection - {collection_title}</h1>
        <p>Thư viện đầy đủ {len(icons)} icon - Nhấp vào icon để sao chép mã HTML</p>
    </div>
    
    <div class="search-container">
        <input type="text" id="searchInput" placeholder="Tìm kiếm icon theo tên hoặc nhãn...">
    </div>
    
    <div class="stats">
        <span id="totalIcons">{len(icons)}</span> icons được hiển thị
    </div>
    
    <div class="filter-container">
        <button class="filter-btn active" data-filter="all">Tất cả</button>
        <button class="filter-btn" data-filter="apps">Ứng dụng</button>
        <button class="filter-btn" data-filter="tools">Công cụ</button>
        <button class="filter-btn" data-filter="games">Trò chơi</button>
        <button class="filter-btn" data-filter="social">Mạng xã hội</button>
    </div>
    
    <div class="icon-grid" id="iconGrid">
        {icon_grid_content}
    </div>
    
    <div class="copied" id="copiedNotification">Đã sao chép mã HTML</div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const iconCards = document.querySelectorAll('.icon-card');
            const searchInput = document.getElementById('searchInput');
            const copiedNotification = document.getElementById('copiedNotification');
            const totalIconsElement = document.getElementById('totalIcons');
            const filterButtons = document.querySelectorAll('.filter-btn');
            let currentFilter = 'all';
            
            // Xử lý sự kiện click trên từng icon
            iconCards.forEach(card => {{
                card.addEventListener('click', function() {{
                    const iconName = this.getAttribute('data-name');
                    // Sử dụng document.execCommand('copy') làm fallback nếu navigator.clipboard không hoạt động
                    const htmlCode = `<i class="icons-${{iconName}}"></i>`;
                    
                    if (navigator.clipboard) {{
                        navigator.clipboard.writeText(htmlCode).then(() => {{
                            // Hiển thị thông báo
                            copiedNotification.classList.add('show');
                            setTimeout(() => {{
                                copiedNotification.classList.remove('show');
                            }}, 2000);
                        }});
                    }} else {{
                        // Fallback cho môi trường không hỗ trợ navigator.clipboard
                        const textArea = document.createElement("textarea");
                        textArea.value = htmlCode;
                        textArea.style.position = "fixed";
                        textArea.style.opacity = "0";
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        try {{
                            document.execCommand('copy');
                            // Hiển thị thông báo
                            copiedNotification.classList.add('show');
                            setTimeout(() => {{
                                copiedNotification.classList.remove('show');
                            }}, 2000);
                        }} catch (err) {{
                            console.error('Không thể sao chép văn bản: ', err);
                        }}
                        document.body.removeChild(textArea);
                    }}
                }});
            }});
            
            // Xử lý tìm kiếm
            searchInput.addEventListener('input', function() {{
                const searchTerm = this.value.toLowerCase();
                let visibleCount = 0;
                
                iconCards.forEach(card => {{
                    const name = card.getAttribute('data-name').toLowerCase();
                    const label = card.getAttribute('data-label').toLowerCase();
                    
                    if ((name.includes(searchTerm) || label.includes(searchTerm)) && 
                        (currentFilter === 'all' || card.getAttribute('data-category') === currentFilter)) {{
                        card.style.display = 'block';
                        visibleCount++;
                    }} else {{
                        card.style.display = 'none';
                    }}
                }});
                
                totalIconsElement.textContent = visibleCount;
            }});
            
            // Xử lý lọc theo danh mục
            filterButtons.forEach(btn => {{
                btn.addEventListener('click', function() {{
                    // Cập nhật active button
                    filterButtons.forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    
                    currentFilter = this.getAttribute('data-filter');
                    const searchTerm = searchInput.value.toLowerCase();
                    let visibleCount = 0;
                    
                    iconCards.forEach(card => {{
                        const name = card.getAttribute('data-name').toLowerCase();
                        const label = card.getAttribute('data-label').toLowerCase();
                        const category = card.getAttribute('data-category');
                        
                        const matchesSearch = name.includes(searchTerm) || label.includes(searchTerm);
                        const matchesFilter = currentFilter === 'all' || category === currentFilter;
                        
                        if (matchesSearch && matchesFilter) {{
                            card.style.display = 'block';
                            visibleCount++;
                        }} else {{
                            card.style.display = 'none';
                        }}
                    }});
                    
                    totalIconsElement.textContent = visibleCount;
                }});
            }});
            
            // Thêm chức năng cuộn mượt khi nhấn nút filter
            filterButtons.forEach(btn => {{
                btn.addEventListener('click', function(e) {{
                    e.preventDefault();
                    const iconGrid = document.getElementById('iconGrid');
                    iconGrid.scrollIntoView({{ behavior: 'smooth' }});
                }});
            }});
        }});
    </script>
</body>
</html>
"""

    # Tạo thư mục nếu chưa tồn tại
    output_dir = os.path.dirname(output_html_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Đã tạo thư mục: {output_dir}")
        except Exception as e:
            print(f"Lỗi khi tạo thư mục {output_dir}: {str(e)}")
            return False
    
    # Ghi file HTML
    try:
        with open(output_html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Đã tạo file demo tại: {output_html_file}")
        print(f"💡 Để sử dụng: Mở file trong trình duyệt và đảm bảo file CSS nguồn ({css_file_name}) nằm cùng thư mục với file HTML demo.")
        print(f"📊 Tổng số icons được hiển thị: {len(icons)}")
        return True
    except Exception as e:
        print(f"Lỗi khi ghi file HTML: {str(e)}")
        return False


def get_file_path(prompt, file_type="file"):
    """
    Yêu cầu người dùng nhập đường dẫn file và kiểm tra tính hợp lệ
    """
    while True:
        path = input(prompt).strip().strip('"').strip("'")
        
        if file_type == "file" and not os.path.isfile(path):
            print(f"❌ Lỗi: File không tồn tại tại đường dẫn: {path}")
            continue
        
        # Nếu đang lấy đường dẫn output, chỉ cần kiểm tra thư mục cha tồn tại
        if file_type == "dir":
            output_dir = os.path.dirname(path)
            if output_dir and not os.path.isdir(output_dir):
                print(f"❌ Lỗi: Thư mục chứa file đầu ra không tồn tại: {output_dir}")
                continue
        
        return path


def main():
    parser = argparse.ArgumentParser(description='Tạo file demo HTML cho Lawnicons')
    parser.add_argument('--css', help='Đường dẫn đến file CSS icon')
    parser.add_argument('--json', help='Đường dẫn đến file JSON chứa icon data (ví dụ: selections.json)')
    parser.add_argument('--output', help='Đường dẫn file HTML đầu ra')
    parser.add_argument('--title', help='Tiêu đề của bộ sưu tập icon (cho header HTML)')
    parser.add_argument('--auto', action='store_true', help='Chế độ tự động với đường dẫn mặc định')
    
    args = parser.parse_args()
    
    # Định nghĩa giá trị mặc định
    default_css_path = "data/icons/style.css"
    default_json_path = "data/icons/selections.json"
    default_html_path = "data/icons/demo.html"
    default_title = "My Icon Set"
    
    # Xử lý chế độ tự động
    if args.auto:
        css_file_path = default_css_path
        json_file_path = default_json_path
        html_output_path = default_html_path
        collection_title = default_title
        
        print("Chế độ tự động được kích hoạt:")
        print(f"- File JSON: {json_file_path}")
        print(f"- File CSS: {css_file_path}")
        print(f"- File HTML đầu ra: {html_output_path}")
        print(f"- Tiêu đề: Collection - {collection_title}")
        
        # Tạo file demo
        generate_icon_demo(css_file_path, json_file_path, html_output_path, collection_title)
        return
    
    # Xử lý tham số dòng lệnh
    if args.css and args.json and args.output:
        css_file_path = args.css
        json_file_path = args.json
        html_output_path = args.output
        collection_title = args.title if args.title else os.path.basename(args.json).replace(".json", "").title()
        
        print(f"Sử dụng đường dẫn từ tham số:")
        print(f"- File JSON: {json_file_path}")
        print(f"- File CSS: {css_file_path}")
        print(f"- File HTML đầu ra: {html_output_path}")
        print(f"- Tiêu đề: Collection - {collection_title}")
        
        # Tạo file demo
        generate_icon_demo(css_file_path, json_file_path, html_output_path, collection_title)
        return
    
    # Chế độ tương tác - yêu cầu người dùng nhập đường dẫn
    print("=== TẠO FILE DEMO ICON TỪ JSON ===")
    print("Bạn có thể kéo và thả file vào cửa sổ terminal để điền đường dẫn tự động")
    
    # Yêu cầu tiêu đề (header)
    collection_title = input(
        "\n⭐ Nhập tiêu đề cho bộ sưu tập icon (ví dụ: My Custom Collection): "
    ).strip()
    if not collection_title:
        collection_title = "Untitled Collection" # Tiêu đề mặc định nếu người dùng không nhập

    # Yêu cầu đường dẫn file JSON
    json_file_path = get_file_path(
        "\n📝 Nhập đường dẫn đến file JSON icon (ví dụ: selections.json): "
    )

    # Yêu cầu đường dẫn file CSS
    css_file_path = get_file_path(
        "\n📝 Nhập đường dẫn đến file CSS icon tương ứng (ví dụ: style.css): "
    )
    
    # Yêu cầu đường dẫn file HTML đầu ra
    html_output_path = get_file_path(
        "\n📁 Nhập đường dẫn file HTML đầu ra (ví dụ: data/icons/demo.html): ",
        file_type="dir"
    )
    
    # Xác nhận thông tin
    print("\n" + "="*50)
    print("THÔNG TIN CẤU HÌNH:")
    print(f"- Tiêu đề: Collection - {collection_title}")
    print(f"- File JSON nguồn: {json_file_path}")
    print(f"- File CSS tương ứng: {css_file_path}")
    print(f"- File HTML đầu ra: {html_output_path}")
    print("="*50)
    
    confirm = input("\nXác nhận tạo file demo? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Hủy bỏ quá trình tạo file demo.")
        return
    
    # Tạo file demo
    generate_icon_demo(css_file_path, json_file_path, html_output_path, collection_title)


if __name__ == "__main__":
    main()