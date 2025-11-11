import json
import os

version = '6.7.2' 

base_path = f'data/fontawesome-free-{version}-web/metadata'
input_file_path = os.path.join(base_path, 'icons.json')
output_file_path = os.path.join(base_path, 'icons-optimized.json')

try:
    with open(input_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    optimized_data = {}
    icon_count = 0

    for name, icon_data in data.items():
        if 'free' in icon_data and len(icon_data['free']) > 0:
            
            search_terms = []
            if 'search' in icon_data and 'terms' in icon_data['search']:
                search_terms = icon_data['search']['terms']

            optimized_data[name] = {
                'l': icon_data.get('label', ''),
                'f': icon_data['free'],         
                't': search_terms               
            }
            icon_count += 1

    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(optimized_data, f, separators=(',', ':')) 

    print(f"THÀNH CÔNG!")
    print(f"Đã xử lý {len(data)} icons.")
    print(f"Đã lưu {icon_count} icon 'free' vào file:")
    print(f"{output_file_path}")

except FileNotFoundError:
    print(f"LỖI: Không tìm thấy file '{input_file_path}'")
    print("Hãy đảm bảo bạn đã đặt đúng đường dẫn và phiên bản.")
except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")