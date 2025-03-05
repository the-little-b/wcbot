import datetime
import shutil
import os
import re
import threading
import time
from queue import Empty
from wcferry import Wcf
from paddleocr import PaddleOCR


# ================== 会话管理类 ==================
class SessionManager:
    def __init__(self):
        self.sessions = {}  # {user_id: {"option": int, "data": dict, "timestamp": float}}
        self.lock = threading.Lock()
        self.timeout = 300  # 会话超时时间（秒）

    def create_session(self, user_id, option, data=None):
        with self.lock:
            self.sessions[user_id] = {
                "option": option,
                "data": data if data else {},
                "timestamp": time.time()
            }

    def get_session(self, user_id):
        with self.lock:
            return self.sessions.get(user_id)

    def update_session(self, user_id, **kwargs):
        with self.lock:
            if user_id in self.sessions:
                self.sessions[user_id].update(kwargs)
                self.sessions[user_id]["timestamp"] = time.time()

    def delete_session(self, user_id):
        with self.lock:
            if user_id in self.sessions:
                del self.sessions[user_id]

    def cleanup_expired(self):
        with self.lock:
            current_time = time.time()
            expired = [
                uid for uid, session in self.sessions.items()
                if current_time - session["timestamp"] > self.timeout
            ]
            for uid in expired:
                del self.sessions[uid]


# ================== 全局配置 ==================
#BASE_DIR = os.path.dirname(os.path.abspath(r"I:\vxvx\wcbot-wcmain"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_PATH = os.path.join(BASE_DIR, "temp")
NAME_DATA = os.path.join(TEMP_PATH, "a.txt")
NAME_CARD = os.path.join(TEMP_PATH, "sn码.txt")
SN_PATH = os.path.join(TEMP_PATH, "sn")
SFZ_PATH = os.path.join(TEMP_PATH, "sfz")
SFZ2_PATH = os.path.join(TEMP_PATH, "sfz2")


# ================== 主逻辑 ==================
def main():
    wcf = Wcf()
    wcf.enable_receiving_msg()
    session_manager = SessionManager()
    ocr = PaddleOCR()  # 全局OCR实例减少重复创建

    # 启动会话清理线程
    def _cleanup():
        while True:
            session_manager.cleanup_expired()
            time.sleep(60)

    threading.Thread(target=_cleanup, daemon=True).start()

    while wcf.is_receiving_msg():
        try:
            msg = wcf.get_msg()
            user_id = msg.sender
            receiver = msg.roomid if msg.from_group() else user_id
            session = session_manager.get_session(user_id)

            # 处理通用指令
            if msg.content == "今天要入哪些发票":
                with open(NAME_CARD, 'r', encoding='utf-8') as f:
                    wcf.send_text(f.read(), receiver)
            elif msg.content == ".help":
                help_msg = "指令列表：\n- 身份证：上传身份证\n- aaa：上传三张图\n- 重来：重置当前操作\n- 状态查询：查看当前状态"
                wcf.send_text(help_msg, receiver)
            elif msg.content == "重来":
                session_manager.delete_session(user_id)
                wcf.send_text("已重置当前会话", receiver)
            elif msg.content == "状态查询":
                status = f"会话状态：{session['option'] if session else '无'}"
                wcf.send_text(status, receiver)

            # 核心逻辑
            if not session:
                if msg.content == "身份证":
                    session_manager.create_session(user_id, option=1)
                    wcf.send_text("请上传身份证照片", receiver)
                elif msg.content == "sn处理":
                    session_manager.create_session(user_id, option=32)
                    wcf.send_text("请上传SN码照片", receiver)
                elif msg.content == "aaa":
                    _handle_aaa_command(wcf, receiver, user_id, session_manager)
            else:
                _handle_session(wcf, msg, session, session_manager, receiver, ocr)

        except Empty:
            continue
        except Exception as e:
            session_manager.delete_session(user_id)
            wcf.send_text(f"操作失败：{str(e)}", receiver)
            print(f"Error: {str(e)}")

    wcf.keep_running()


# ================== 辅助函数 ==================
def _handle_aaa_command(wcf, receiver, user_id, session_manager):
    with open(NAME_DATA, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if not lines:
        wcf.send_text("暂无待处理数据", receiver)
        return
    session_manager.create_session(user_id, option=31, data={"lines": lines})
    list_msg = "\n".join([f"{i + 1}. {line.strip()}" for i, line in enumerate(lines)])
    wcf.send_text("请选择序号：\n" + list_msg, receiver)


def _handle_session(wcf, msg, session, session_manager, receiver, ocr):
    user_id = msg.sender
    option = session["option"]
    data = session.setdefault("data", {})

    # 处理文本消息#important
    if msg.type == 1:
        if option == 31:  # 处理aaa选择
            num = int(msg.content)
            lines = data["lines"]
            data.update({
                "num_to_skip": num,
                "namestr": lines[num - 1].strip(),
                "downpath": os.path.join(TEMP_PATH, lines[num - 1].strip())
            })
            session_manager.update_session(user_id, option=32)
            wcf.send_text("请上传SN码照片", receiver)

        elif option == 12:  # 身份证名字处理
            idcard = data["idcard"]
            namestr = msg.content
            os.makedirs(r"temp/"+namestr, exist_ok=True)#创建文件夹
            # with open(NAME_DATA, 'a',encoding='utf-8') as f:
            #     f.write(f"{namestr}\n")
            # # ... 其他处理逻辑
            with open(NAME_DATA, 'a', encoding='utf-8') as write_file:
                write_file.write(namestr + "\n")
                write_file.close()
            pattern = re.compile(r'([0-9]{5})(\S{2,3})')
            re_result = pattern.match(namestr)
            with open(NAME_CARD, 'a', encoding='utf-8') as write_file:
                write_file.write(re_result.group(1) + "\t" + re_result.group(2) + "\t" + idcard + "\n")
                write_file.close()
            data.update({
                "name_idcard": namestr + idcard
            })#增加这个图片名
            session_manager.update_session(user_id, option=11)
            wcf.send_text("请上传身份证和发票组合图：", receiver)

    # 处理图片消息
    elif msg.type == 3:
        if option == 1:  # 身份证识别
            img_path = wcf.download_image(msg.id, msg.extra, SFZ_PATH)
            id_num = _ocr_idcard(img_path, ocr)
            session_manager.update_session(user_id, option=12, data={"idcard": id_num})
            wcf.send_text(f"识别到身份证号：{id_num}\n请输入发票后五位与姓名", receiver)
        elif option == 11:
                tempstr = wcf.download_image(msg.id, msg.extra, TEMP_PATH + r"\temp", 150)
                shutil.move(tempstr, SFZ2_PATH + "\\" + data['name_idcard'] + get_tailname(tempstr))
                wcf.send_text("已经归档", receiver)
                session_manager.delete_session(user_id)
                #之后试试删除

        elif option == 32:  # SN码识别
            img_path = wcf.download_image(msg.id, msg.extra, SN_PATH)
            sn_num = _ocr_sn(img_path, ocr)
            append_txt(NAME_CARD, data["namestr"], sn_num)
            shutil.move(img_path, data["downpath"] + "\\" + "a" + get_tailname(img_path))
            session_manager.update_session(user_id, option=33)
            wcf.send_text(f"SN码已记录：{sn_num}\n请继续上传图片", receiver)
        elif option == 33:
            tempstr = wcf.download_image(msg.id, msg.extra,
                                         TEMP_PATH + "\\temp",
                                         150)
            shutil.move(tempstr, data["downpath"] + "\\" + "1" + get_tailname(tempstr))
            wcf.send_text("请发最后一张图", receiver)
            session_manager.update_session(user_id, option=34)
        elif option == 34:
            tempstr = wcf.download_image(msg.id, msg.extra, TEMP_PATH + "\\temp",
                                         150)
            shutil.move(tempstr, data["downpath"] + "\\" + "2" + get_tailname(tempstr))
            wcf.send_text("归档成功", receiver)
            wcf.send_text("已经收集该用户全部信息", receiver)
            remove_line(NAME_DATA, data["num_to_skip"])
            session_manager.delete_session(user_id)




# ================== OCR函数 ==================
def _ocr_idcard(img_path, ocr)->str:
    # 实现身份证OCR逻辑
    id = None
    pattern = re.compile(
        r"([1-6][1-9]|50)\d{4}(18|19|20)\d{2}((0[1-9])|10|11|12)(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]")
    data = ocr.ocr(img_path)
    for i in data:
        for j in i:
            match = pattern.match(j[1][0])
            if match:
                id = match.group(0)
                print(id)
    return id



def _ocr_sn(img_path, ocr,y_threshold=30) -> str:
    # 实现SN码OCR逻辑
    pattern1 = re.compile(r"ber:([A-Z0-9]{15,})")
    data = ocr.ocr(img_path)
    ocr_result = data[0]
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
    print(final_result)
    myline = ''
    for aline in final_result:
        for aword in aline:
            myline += aword[1][0]
        if 'ber' in myline:
            newline = myline.replace(' ', "")
            print(newline)
            match = re.search(pattern1, newline)
            return match.group(1)
        myline = ''
    return 'None'


# ================== 其他工具函数 ==================
# （保持原有get_tailname、append_txt等函数不变）

def remove_line(txtpath, linenum) -> str:
    res = None  #返回了删除的行的内容
    fileName = txtpath
    with open(fileName, 'r', encoding='utf-8') as read_file:
        lines = read_file.readlines()
    currentLine = 1
    with open(fileName, 'w', encoding='utf-8') as write_file:
        for line in lines:
            if currentLine == linenum:
                res = line
            else:
                write_file.write(line)
            currentLine += 1
    read_file.close()
    write_file.close()
    return res

# 输入sn码的txt,给用户的发票后五位+名字，在后面补充sn码
def append_txt(txtpath, name, snnum):
    fileName = txtpath

    with open(fileName, 'r', encoding='utf-8') as read_file:
        lines = read_file.readlines()
    with open(fileName, 'w', encoding='utf-8') as write_file:
        for line in lines:
            line2 = re.sub('\t', '', line)
            if name in line2:
                line = line.strip() + "\t" + str(snnum) + "\n"

            write_file.write(line)
    read_file.close()
    write_file.close()


#分析获取文件的类型名字
def get_tailname(path) -> str:
    pattern = re.compile(r".[^.]+$")
    match = pattern.search(path)
    return match.group(0)

if __name__ == '__main__':
    main()