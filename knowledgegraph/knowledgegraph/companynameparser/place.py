import os

pwd_path = os.path.abspath(os.path.dirname(__file__))
pca_path = os.path.join(pwd_path, 'data/pca.csv')
def get_places():
    place_map = {}
    with open(pca_path, 'r', encoding='utf-8') as f:
        import csv
        pca_csv = csv.DictReader(f)
        for record_dict in pca_csv:
            _fill_place_map(place_map, record_dict)
    return place_map

def _fill_place_map(place_map, record_dict):
    sheng = record_dict['sheng']
    if sheng not in place_map:
        place_map[sheng] = sheng
        if sheng.endswith('省') or sheng.endswith('市'):
            place_map[sheng[:-1]] = sheng
        # 自治区
        elif sheng == '新疆维吾尔自治区':
            place_map['新疆'] = sheng
        elif sheng == '内蒙古自治区':
            place_map['内蒙古'] = sheng
        elif sheng == '广西壮族自治区':
            place_map['广西'] = sheng
            place_map['广西省'] = sheng
        elif sheng == '西藏自治区':
            place_map['西藏'] = sheng
        elif sheng == '宁夏回族自治区':
            place_map['宁夏'] = sheng
        # 特别行政区
        elif sheng == '香港特别行政区':
            place_map['香港'] = sheng
        elif sheng == '澳门特别行政区':
            place_map['澳门'] = sheng
    city_name = record_dict['shi']
    if city_name not in place_map:
        place_map[city_name] = city_name
        # 处理简写情况
        if city_name.endswith('市'):
            place_map[city_name[:-1]] = city_name
        # 特别行政区
        elif city_name == '香港特别行政区':
            place_map['香港'] = city_name
        elif city_name == '澳门特别行政区':
            place_map['澳门'] = city_name
        # 自治区下的二级区划，eg喀什地区
        elif len(city_name) > 3 and city_name.endswith('地区'):
            place_map[city_name[:-2]] = city_name

    area_name = record_dict['qu']
    if area_name not in place_map:
        place_map[area_name] = area_name
        # 处理简写情况
        # 4字区划简称
        if len(area_name) > 3 and (area_name.endswith('新区') or area_name.endswith('城区') or area_name.endswith('林区')):
            place_map[area_name[:-2]] = area_name
        # 3字区划简称，'XX区'不简写
        elif len(area_name) > 2 and (area_name.endswith('市') or area_name.endswith('县') or area_name.endswith('区')):
            place_map[area_name[:-1]] = area_name

if __name__ == '__main__':
    maps = get_places()
    with open('place.txt', 'w', encoding='utf-8') as f:
        for k, v in maps.items():
            f.write(k + '\n')
