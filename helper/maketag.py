import json
import os
import re
import sys
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple, Union # Đã thêm Optional để sửa lỗi

# --- Quy tắc làm giàu dữ liệu ---
# Các quy tắc được định nghĩa dưới dạng danh sách, giúp dễ dàng mở rộng.
# Mỗi quy tắc có thể là:
# - 'exact': Áp dụng nếu tên icon khớp chính xác.
# - 'prefix': Áp dụng nếu tên icon bắt đầu bằng từ khóa.
# - 'contains': Áp dụng nếu tên icon chứa từ khóa.
# - 'suffix': Áp dụng nếu tên icon kết thúc bằng từ khóa.

def load_enrichment_rules() -> List[Dict[str, Any]]:
    """
    Tải danh sách các quy tắc làm giàu dữ liệu mở rộng.
    Bạn có thể thêm hàng trăm quy tắc vào đây.
    """
    rules = [
        # --- Existing Vietnamese/General Rules ---
        {'type': 'exact', 'keyword': 'home', 'tags': ['trang chủ', 'nhà', 'bắt đầu', 'main', 'start'], 'description': 'Biểu tượng trang chủ hoặc vị trí ban đầu.'},
        {'type': 'exact', 'keyword': 'user', 'tags': ['người dùng', 'tài khoản', 'hồ sơ', 'person', 'profile'], 'description': 'Biểu tượng đại diện cho người dùng hoặc hồ sơ cá nhân.'},
        {'type': 'contains', 'keyword': 'setting', 'tags': ['cấu hình', 'tùy chỉnh', 'bánh răng', 'gear', 'options'], 'description': 'Biểu tượng liên quan đến thiết lập và cấu hình.'},
        {'type': 'contains', 'keyword': 'folder', 'tags': ['thư mục', 'lưu trữ', 'quản lý file', 'directory', 'storage'], 'description': 'Biểu tượng cho thư mục hoặc quản lý tệp.'},
        {'type': 'contains', 'keyword': 'social', 'tags': ['mạng xã hội', 'kết nối', 'community', 'network'], 'description': 'Biểu tượng liên quan đến các nền tảng xã hội.'},
        {'type': 'contains', 'keyword': 'mail', 'tags': ['email', 'thư điện tử', 'tin nhắn', 'message', 'inbox'], 'description': 'Biểu tượng gửi/nhận thư điện tử.'},
        {'type': 'contains', 'keyword': 'game', 'tags': ['trò chơi', 'giải trí', 'play', 'controller'], 'description': 'Biểu tượng liên quan đến trò chơi hoặc giải trí.'},
        {'type': 'contains', 'keyword': 'phone', 'tags': ['điện thoại', 'gọi điện', 'liên hệ', 'call', 'contact'], 'description': 'Biểu tượng gọi điện thoại hoặc liên hệ.'},
        {'type': 'prefix', 'keyword': 'arrow', 'tags': ['mũi tên', 'chuyển hướng', 'direction', 'move'], 'description': 'Biểu tượng định hướng, chỉ đường.'},
        {'type': 'prefix', 'keyword': 'file', 'tags': ['tệp tin', 'dữ liệu', 'văn bản', 'document', 'data'], 'description': 'Biểu tượng tệp tin chung.'},
        {'type': 'suffix', 'keyword': 'fill', 'tags': ['đặc', 'đã tô', 'solid', 'filled'], 'description': 'Biểu tượng phiên bản đã tô màu (filled).'},
        {'type': 'suffix', 'keyword': 'outline', 'tags': ['viền', 'khung', 'line', 'border'], 'description': 'Biểu tượng phiên bản đường viền (outline).'},
        
        # --- NEW ENGLISH RULES (Expanded Coverage) ---
        
        # E-commerce / Finance
        {'type': 'contains', 'keyword': 'shop', 'tags': ['store', 'ecommerce', 'retail', 'market'], 'description': 'Icon related to shopping and commerce.'},
        {'type': 'contains', 'keyword': 'cart', 'tags': ['basket', 'purchase', 'buy', 'checkout'], 'description': 'Icon representing a shopping cart or checkout process.'},
        {'type': 'contains', 'keyword': 'credit', 'tags': ['card', 'payment', 'transaction', 'visa', 'mastercard'], 'description': 'Icon for credit, debit, or payment methods.'},
        {'type': 'contains', 'keyword': 'money', 'tags': ['dollar', 'cash', 'finance', 'currency', 'bank'], 'description': 'Icon related to money, banking, or finance.'},
        
        # Actions / Status
        {'type': 'contains', 'keyword': 'plus', 'tags': ['add', 'create', 'new', 'insert', 'increase'], 'description': 'Icon for adding or creating a new item.'},
        {'type': 'contains', 'keyword': 'minus', 'tags': ['subtract', 'remove', 'delete', 'decrease'], 'description': 'Icon for removal or subtraction.'},
        {'type': 'contains', 'keyword': 'trash', 'tags': ['delete', 'remove', 'bin', 'junk', 'clear'], 'description': 'Icon for deleting or discarding items.'},
        {'type': 'contains', 'keyword': 'edit', 'tags': ['write', 'modify', 'pen', 'pencil', 'update'], 'description': 'Icon for editing or writing functionality.'},
        {'type': 'contains', 'keyword': 'download', 'tags': ['get', 'receive', 'arrow-down', 'transfer'], 'description': 'Icon for downloading data or files.'},
        {'type': 'contains', 'keyword': 'upload', 'tags': ['send', 'submit', 'arrow-up', 'transfer'], 'description': 'Icon for uploading data or files.'},
        
        # Security / Access
        {'type': 'contains', 'keyword': 'lock', 'tags': ['security', 'secure', 'private', 'password'], 'description': 'Icon related to security, locking, or privacy.'},
        {'type': 'contains', 'keyword': 'shield', 'tags': ['protect', 'safety', 'guard', 'defense'], 'description': 'Icon representing protection or security features.'},
        
        # Media / Display
        {'type': 'contains', 'keyword': 'volume', 'tags': ['sound', 'audio', 'speaker', 'mute'], 'description': 'Icon for controlling sound and volume levels.'},
        {'type': 'contains', 'keyword': 'play', 'tags': ['start', 'go', 'media', 'video', 'movie'], 'description': 'Icon for starting media playback.'},
        {'type': 'contains', 'keyword': 'camera', 'tags': ['photo', 'picture', 'image', 'capture'], 'description': 'Icon related to photography or image capture.'},
        {'type': 'contains', 'keyword': 'display', 'tags': ['screen', 'monitor', 'desktop', 'view'], 'description': 'Icon representing a screen or display device.'},
        
        # Navigation / Location
        {'type': 'contains', 'keyword': 'map', 'tags': ['location', 'gps', 'navigate', 'direction'], 'description': 'Icon for maps, location tracking, or navigation.'},
        {'type': 'contains', 'keyword': 'search', 'tags': ['find', 'magnify', 'discover', 'explore'], 'description': 'Icon for searching or discovering content.'},
        {'type': 'contains', 'keyword': 'pin', 'tags': ['marker', 'location', 'point', 'map'], 'description': 'Icon for marking a location or point.'},
        
        # Data / Development
        {'type': 'contains', 'keyword': 'data', 'tags': ['database', 'storage', 'server', 'information', 'analytics'], 'description': 'Icon related to data, storage, or information.'},
        {'type': 'contains', 'keyword': 'code', 'tags': ['develop', 'program', 'script', 'web', 'html'], 'description': 'Icon representing programming or source code.'},
        {'type': 'contains', 'keyword': 'chart', 'tags': ['graph', 'statistics', 'analysis', 'report'], 'description': 'Icon for data analysis and charting.'},

    ]
    
    # Chuyển đổi tất cả keyword sang lowercase để đảm bảo so sánh không phân biệt chữ hoa/thường
    for rule in rules:
        rule['keyword'] = rule['keyword'].lower()
        
    return rules

def enrich_icon_data(input_file: str, output_file: str, external_mapping_file: Optional[str] = None):
    """
    Đọc file JSON, thêm keywords và description dựa trên bộ quy tắc, lưu file mới.
    Tự động phát hiện cấu trúc JSON và áp dụng logic phù hợp.
    """
    if not os.path.exists(input_file):
        print(f"Lỗi: File không tồn tại: {input_file}")
        return False
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Lỗi khi đọc file JSON: {e}")
        return False
    
    # Phát hiện cấu trúc JSON
    structure_type = detect_json_structure(data)
    print(f"🔍 Phát hiện cấu trúc JSON: {structure_type}")
    
    if structure_type == 'unknown':
        print("❌ Không thể xác định cấu trúc JSON. Vui lòng kiểm tra file đầu vào.")
        return False
    
    # Tải mapping bên ngoài nếu có
    external_mapping = load_external_mapping(external_mapping_file)
    
    # Trích xuất danh sách icon và tên
    if structure_type == 'icomoon':
        icons = data['icons']
        icon_names = [icon['properties']['name'] for icon in icons if 'properties' in icon and 'name' in icon['properties']]
    elif structure_type == 'fontello':
        icons = data['icons']
        icon_names = [icon['name'] for icon in icons if 'name' in icon]
    elif structure_type == 'custom':
        icons = data['icons']
        icon_names = []
        for icon in icons:
            if 'name' in icon:
                icon_names.append(icon['name'])
            elif 'properties' in icon and 'name' in icon['properties']:
                icon_names.append(icon['properties']['name'])
    
    print(f"📊 Phát hiện {len(icons)} icons trong file")
    
    # Tạo mapping mặc định dựa trên tên icon
    default_mapping = generate_default_mapping(icon_names)
    
    # Kết hợp mapping bên ngoài với mapping mặc định
    combined_mapping = {}
    for name in icon_names:
        if name in external_mapping:
            combined_mapping[name] = external_mapping[name]
        elif name in default_mapping:
            combined_mapping[name] = default_mapping[name]
        else:
            combined_mapping[name] = default_mapping['default']
    
    print(f"🔄 Đã tạo mapping cho {len(combined_mapping)} icons")
    
    # Làm giàu dữ liệu cho từng icon
    enriched_count = 0
    for icon in icons:
        name = ''
        if structure_type == 'icomoon':
            if 'properties' in icon and 'name' in icon['properties']:
                name = icon['properties']['name']
        elif structure_type == 'fontello' or structure_type == 'custom':
            if 'name' in icon:
                name = icon['name']
            elif 'properties' in icon and 'name' in icon['properties']:
                name = icon['properties']['name']
        
        if not name:
            continue
        
        # Sử dụng mapping đã kết hợp
        icon_mapping = combined_mapping.get(name, default_mapping['default'])
        
        # Thêm/xử lý tags
        existing_tags = []
        if 'icon' in icon and 'tags' in icon['icon']:
            existing_tags = icon['icon']['tags']
        elif 'tags' in icon:
            existing_tags = icon['tags']
        
        # Kết hợp tags mới và cũ
        new_tags = list(set(existing_tags + icon_mapping['tags']))
        
        # Cập nhật icon với dữ liệu mới
        if 'icon' not in icon:
            icon['icon'] = {}
        
        icon['icon']['tags'] = new_tags
        icon['description'] = icon_mapping['description']
        icon['category'] = icon_mapping['category']
        
        enriched_count += 1
    
    print(f"✅ Đã làm giàu {enriched_count}/{len(icons)} icons")
    
    # Lưu file mới
    try:
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu file kết quả: {output_file}")
        return True
    except Exception as e:
        print(f"Lỗi khi lưu file: {e}")
        return False

def detect_json_structure(data: Dict) -> str:
    """Phát hiện cấu trúc JSON tự động."""
    if 'icons' in data:
        if isinstance(data['icons'], list) and len(data['icons']) > 0:
            first_icon = data['icons'][0]
            if 'properties' in first_icon and 'name' in first_icon['properties']:
                return 'icomoon'  # Cấu trúc IcoMoon tiêu chuẩn
            if 'name' in first_icon and 'content' in first_icon:
                return 'fontello'  # Cấu trúc Fontello
    if 'metadata' in data and 'icons' in data:
        return 'custom'  # Cấu trúc custom
    return 'unknown'

def parse_icon_name(raw_name: str) -> str:
    """
    Xử lý tên icon thông minh, hỗ trợ mọi định dạng:
    - snake_case → chuyển thành từ
    - kebab-case → chuyển thành từ
    - PascalCase/CamelCase → tách thành từ
    - Loại bỏ tiền tố số, ký tự đặc biệt
    """
    # Loại bỏ tiền tố số, gạch dưới thừa
    name = re.sub(r'^[0-9]+[_\-]?', '', raw_name)
    
    # Xử lý PascalCase/CamelCase trước
    name = re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
    
    # Chuyển snake_case và kebab-case thành khoảng trắng
    name = name.replace('_', ' ').replace('-', ' ')
    
    # Loại bỏ ký tự đặc biệt, giữ lại chữ và số
    name = re.sub(r'[^\w\s]', '', name)
    
    # Chuẩn hóa khoảng trắng và viết thường
    return ' '.join(name.lower().split())

def generate_default_mapping(icon_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Tạo mapping mặc định thông minh từ danh sách tên icon.
    Sử dụng heuristic để tạo keywords và description cơ bản.
    """
    mapping = {}
    common_words = defaultdict(int)
    
    # Phân tích các từ thường xuất hiện
    for name in icon_names:
        parsed = parse_icon_name(name)
        words = parsed.split()
        for word in words:
            if len(word) > 2:  # Bỏ qua từ quá ngắn
                common_words[word] += 1
    
    # Xác định danh mục dựa trên từ khóa phổ biến
    categories = {
        'social': ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok', 'reddit', 'pinterest'],
        'finance': ['bank', 'money', 'payment', 'credit', 'wallet', 'coin', 'cash', 'dollar'],
        'tools': ['settings', 'config', 'gear', 'tool', 'wrench', 'hammer', 'screw', 'adjust', 'utility'],
        'communication': ['message', 'chat', 'email', 'call', 'phone', 'sms', 'notification', 'talk'],
        'media': ['music', 'video', 'photo', 'image', 'camera', 'play', 'pause', 'volume', 'film', 'movie'],
        'travel': ['car', 'plane', 'train', 'bus', 'map', 'location', 'gps', 'direction', 'route', 'journey'],
        'health': ['medical', 'heart', 'hospital', 'health', 'doctor', 'medicine', 'fitness', 'pulse', 'care'],
        'business': ['office', 'building', 'chart', 'graph', 'presentation', 'briefcase', 'report', 'analytics'],
        'nature': ['tree', 'leaf', 'flower', 'mountain', 'water', 'sun', 'moon', 'star', 'weather', 'eco'],
        'games': ['game', 'play', 'controller', 'dice', 'puzzle', 'chess', 'cards', 'joystick', 'console'],
        'e-commerce': ['shop', 'cart', 'buy', 'product', 'sale', 'store', 'basket', 'checkout']
    }
    
    # Tạo mapping cho từng icon
    for name in icon_names:
        parsed_name = parse_icon_name(name)
        words = parsed_name.split()
        
        # Tìm danh mục phù hợp
        category = 'general'
        for cat, keywords in categories.items():
            if any(keyword in parsed_name for keyword in keywords):
                category = cat
                break
        
        # Tạo keywords thông minh
        keywords = []
        # Thêm từ khóa từ tên icon
        keywords.extend(words)
        
        # Thêm từ khóa liên quan theo danh mục
        if category == 'social':
            keywords.extend(['social', 'network', 'community', 'connect', 'share'])
        elif category == 'finance':
            keywords.extend(['finance', 'business', 'money', 'transaction', 'banking', 'budget'])
        elif category == 'tools':
            keywords.extend(['tool', 'utility', 'function', 'setting', 'configuration', 'management'])
        elif category == 'communication':
            keywords.extend(['message', 'contact', 'talk', 'communicate', 'inbox'])
        elif category == 'media':
            keywords.extend(['media', 'entertainment', 'content', 'playback', 'visual'])
        elif category == 'travel':
            keywords.extend(['travel', 'transportation', 'navigation', 'journey', 'route'])
        elif category == 'health':
            keywords.extend(['health', 'wellness', 'medical', 'fitness', 'therapy'])
        elif category == 'business':
            keywords.extend(['business', 'office', 'corporate', 'analytics', 'professional'])
        elif category == 'nature':
            keywords.extend(['nature', 'environment', 'outdoor', 'eco', 'natural'])
        elif category == 'games':
            keywords.extend(['game', 'entertainment', 'fun', 'play', 'gaming'])
        elif category == 'e-commerce':
            keywords.extend(['e-commerce', 'shopping', 'store', 'purchase', 'market'])
        
        # Tạo description tự động
        description = f"Icon representing {parsed_name}"
        if category != 'general':
            description += f" in the {category} category"
        
        mapping[name] = {
            'tags': list(set(keywords)),  # Loại bỏ trùng lặp
            'description': description,
            'category': category
        }
    
    # Thêm mapping mặc định
    mapping['default'] = {
        'tags': ['icon', 'symbol', 'graphic', 'element', 'illustration', 'general'],
        'description': 'General icon without specific categorization.',
        'category': 'general'
    }
    
    return mapping

def load_external_mapping(mapping_file: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Tải mapping từ file JSON bên ngoài nếu tồn tại."""
    if mapping_file and os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                # Chú ý: File mapping bên ngoài phải có tên icon làm key, ví dụ: {"home": {"tags": [...], "description": "..."}}
                return json.load(f)
        except Exception as e:
            print(f"Cảnh báo: Không thể tải file mapping bên ngoài ({e})")
    return {}

def main():
    """Hàm chính với giao diện người dùng thân thiện."""
    print("=== 🧠 ICON ENRICHER - Làm giàu dữ liệu icon tự động ===")
    
    # Lấy đường dẫn input
    input_file = input("📁 Đường dẫn file selection JSON đầu vào: ").strip()
    if not os.path.exists(input_file):
        print("❌ File không tồn tại. Vui lòng kiểm tra lại đường dẫn.")
        return
    
    # Lấy đường dẫn output
    default_output = os.path.splitext(input_file)[0] + "-enriched.json"
    output_file = input(f"💾 Đường dẫn file output (Enter để dùng mặc định: {default_output}): ").strip()
    if not output_file:
        output_file = default_output
    
    # Hỏi về file mapping tùy chỉnh
    print("\n❓ Bạn có file mapping tùy chỉnh không? (Nếu có, nhập đường dẫn, nếu không nhấn Enter)")
    external_mapping_file = input("📁 Đường dẫn file mapping (tuỳ chọn): ").strip()
    if external_mapping_file and not os.path.exists(external_mapping_file):
        print("⚠️ File mapping không tồn tại. Sẽ sử dụng mapping tự động.")
        external_mapping_file = None
    
    print("\n🚀 Bắt đầu xử lý...")
    success = enrich_icon_data(input_file, output_file, external_mapping_file)
    
    if success:
        print("\n🎉 Hoàn tất! File đã được làm giàu với dữ liệu từ khóa và mô tả.")
        print("💡 Mẹo: Bạn có thể sử dụng file này để:")
        print("   - Cải thiện tìm kiếm icon trong ứng dụng")
        print("   - Tạo trang demo với mô tả chi tiết")
        print("   - Xuất bản bộ icon với metadata đầy đủ")
    else:
        print("\n❌ Xử lý thất bại. Vui lòng kiểm tra lại đầu vào và thử lại.")

if __name__ == "__main__":
    main()