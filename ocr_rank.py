import numpy as np
from paddleocr import PaddleOCR
from PIL import Image
import re
ocr = PaddleOCR(lang="ch", show_log=False)
img1 = r"I:\vxvx\wcbot-wcmain\1245.jpg"
pattern1 = re.compile(r"ber:([A-Z0-9]{15,})")


def process_ocr_result(ocr_result, y_threshold=30):
    # 计算每个文本框的纵向中心点并预处理数据
    processed = []
    for box in ocr_result:
        points = box[0]
        ys = [p[1] for p in points]
        min_y, max_y = min(ys), max(ys)
        center_y = (min_y + max_y) / 2
        x_coords = [p[0] for p in points]
        min_x = min(x_coords)
        processed.append((center_y, min_x, box))

    # 按纵向中心点排序
    processed.sort(key=lambda x: x[0])

    # 分组处理
    groups = []
    current_group = []
    group_min = group_max = None

    for item in processed:
        cy, _, _ = item

        if not current_group:
            current_group.append(item)
            group_min = group_max = cy
        else:
            # 计算扩展后的范围
            new_min = min(group_min, cy)
            new_max = max(group_max, cy)

            if (new_max - new_min) <= y_threshold:
                current_group.append(item)
                group_min = new_min
                group_max = new_max
            else:
                # 新组
                groups.append(current_group)
                current_group = [item]
                group_min = group_max = cy

    if current_group:
        groups.append(current_group)

    # 对每组按横向位置排序并重组结果
    final_result = []
    for group in groups:
        # 按最小X坐标排序
        sorted_group = sorted(group, key=lambda x: x[1])
        # 重组为原始格式
        final_result.append([item[2] for item in sorted_group])
    myline = ''
    for aline in final_result:
        for aword in aline:
            myline += aword[1][0]
        if 'ber' in myline:
            newline = myline.replace(' ',"")
            print(newline)
            match = re.search(pattern1, newline)
            return match.group(1)
        myline = ''
    return 'None'

if __name__ == '__main__':
    ocr = PaddleOCR()
    data = ocr.ocr(img1)
    print(process_ocr_result(data[0]))
