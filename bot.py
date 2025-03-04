import datetime
import shutil
import os
from wcferry import Wcf
from queue import Empty
from paddleocr import PaddleOCR
import re

#这个破玩意下图不支持相对路径？
name_and_data = r"D:\wcbot\wcbot\temp\a.txt"
name_and_card = r"D:\wcbot\wcbot\temp\sn码.txt"


def main():
    wcf = Wcf()
    wcf.enable_receiving_msg()
    focus_id = None
    focus_id1 = None  #用于身份证部分
    focus_id2 = None  #用于sn部分
    focus_option = 0  #1收身份证  11身份证全图 12记录身份证名字 31收到几号 32收sn码 33收两个图
    dir_path = "temp"
    namestr = None
    idcard = None
    temp_path = r"D:\wcbot\wcbot\temp"
    sn_path = r"D:\wcbot\wcbot\temp\sn"
    sfz_path = r"D:\wcbot\wcbot\temp\sfz"
    downpath = None
    os.chdir(dir_path)
    num_to_skip = -1

    sn_line_num = 0
    # a = wcf.get_msg_types()
    # print(a)

    while wcf.is_receiving_msg():
        try:
            msg = wcf.get_msg()
            print(msg.content)
            receiver = msg.sender
            if (msg.from_group()):
                receiver = msg.roomid
            if(msg.content == "今天要入哪些发票"):
                with open(name_and_card, 'r', encoding='utf-8') as read_file:
                    lines = read_file.readlines()
                read_file.close()
                name_card_str = ''
                for line in lines:
                    name_card_str = name_card_str + line
                wcf.send_text(name_card_str, receiver)
            elif msg.content == r'.help':
                helpmes = "输入 身份证 上传身份证\n" + "输入 aaa 上传三张图\n" + "遇到bug请输入 重来\n" +"输入 bbb 手动输入sn码(功能还在做）\n"+ "输入 今天要入哪些发票 查看今日发票"
                wcf.send_text(helpmes, receiver)


            elif (msg.content == "重来"):
                focus_option = 0
                focus_id1 = None
                focus_id2 = None
            elif (msg.content == "状态查询"):
                if focus_id1 is not None:
                    wcf.send_text("id1: " + focus_id1, receiver)
                if focus_id2 is not None:
                    wcf.send_text("id2: " + focus_id2, receiver)

                wcf.send_text("option: " + str(focus_option), receiver)
                #31
            if (focus_option == 31) & (msg.type == 1)&(msg.sender == focus_id2):

                    num = msg.content
                    num_to_skip = int(num)
                    num_to_see = num_to_skip - 1
                    with open(name_and_data, 'r', encoding='utf-8') as read_file:
                        lines = read_file.readlines()
                        print(lines[num_to_see])
                        read_file.close()
                    namestr = lines[num_to_see].strip()
                    wcf.send_text("请上传端正的sn图", receiver)
                    downpath = temp_path + "\\" + namestr + "\\"
                    focus_option = 32
            if (focus_option == 311) & (msg.type == 1) & (msg.sender == focus_id2):
                    num = msg.content
                    num_to_skip = int(num)
                    num_to_see = num_to_skip - 1
                    with open(name_and_data, 'r', encoding='utf-8') as read_file:
                        lines = read_file.readlines()
                        print(lines[num_to_see])
                        read_file.close()
                    namestr = lines[num_to_see].strip()
                    wcf.send_text("请先手动给我sn码的图片，然后再手动输入sn码：", receiver)
                    wcf.send_text("请给我sn图片", receiver)
                    downpath = temp_path + "\\" + namestr + "\\"
                    focus_option = 322

            if(focus_option == 3221) & (msg.type == 1) & (msg.sender == focus_id2):
                    sn_num_with_bug = msg.content
                    print(sn_num_with_bug)
                    append_txt(name_and_card, namestr, sn_num_with_bug)
                    wcf.send_text("请发剩下两张图", receiver)
                    focus_option = 33

            if (focus_option == 12) & (msg.type == 1):

                namestr = msg.content  #发票后5位+name
                new_folder = msg.content
                os.mkdir(new_folder)
                wcf.send_text("已经为用户创建文件夹：" + new_folder, receiver)
                wcf.send_text("请上传身份证和发票组合图：", receiver)
                with open(name_and_data, 'a', encoding='utf-8') as write_file:
                    write_file.write(new_folder + "\n")
                    write_file.close()
                pattern = re.compile(r'([0-9]{5})(\S{2,3})')
                re_result = pattern.match(namestr)
                with open(name_and_card, 'a', encoding='utf-8') as write_file:
                    write_file.write(re_result.group(1) + "\t" + re_result.group(2) + "\t"+ idcard + "\n")
                    write_file.close()
                downpath = temp_path + "\\" + r"sfz2" + "\\"
                idcard = namestr + idcard
                focus_option = 11

            if msg.content == "你好123":
                print(msg.sender)
                wcf.send_text("你好啊！",receiver)
            if msg.content == "拍一拍我":
                wcf.send_pat_msg(msg.roomid, msg.sender)
            if msg.content == "发个图":
                wcf.send_text("暂无", receiver)
            if msg.content == "我要发图":
                wcf.send_text("准备收图", receiver)
                focus_id = msg.sender

            if msg.type == 3:  #sn的图片ocr
                if msg.sender == focus_id2:
                    wcf.send_text("我收到了id2的一张图", receiver)
                    if focus_option == 322:
                        sn_path_with_bug = wcf.download_image(msg.id, msg.extra, sn_path, 150)

                        shutil.move(sn_path_with_bug, downpath + "a" + get_tailname(sn_path_with_bug))
                        wcf.send_text("请手动输入sn码", receiver)

                        focus_option = 3221  # 初始化
                    elif focus_option == 32:  #ocrsn
                        tempstr = wcf.download_image(msg.id, msg.extra, sn_path, 150)
                        wcf.send_text("这好像是个sn码，码号是：", receiver)  #ocr
                        snnum = botsnocr(tempstr)
                        wcf.send_text(snnum, receiver)
                        #sn 写入b.TXT
                        append_txt(name_and_card,namestr,snnum)
                        shutil.move(tempstr, downpath + "a" + get_tailname(tempstr))
                        wcf.send_text("归档成功", receiver)
                        wcf.send_text("请发剩下的两张图", receiver)
                        #focus_id2 = None
                        focus_option = 33  # 初始化
                    elif focus_option == 33:
                        #下载并保存
                        tempstr = wcf.download_image(msg.id, msg.extra,
                                                     temp_path + "\\temp",
                                                     150)
                        shutil.move(tempstr, downpath + "1" + get_tailname(tempstr))
                        wcf.send_text("归档成功", receiver)
                        wcf.send_text("请发最后一张图", receiver)
                        focus_option = 34

                    elif focus_option == 34:
                        #下载并保存
                        tempstr = wcf.download_image(msg.id, msg.extra, temp_path + "\\temp",
                                                     150)
                        shutil.move(tempstr, downpath + "2" + get_tailname(tempstr))
                        wcf.send_text("归档成功", receiver)
                        wcf.send_text("已经收集该用户全部信息", receiver)
                        remove_line(name_and_data, num_to_skip)
                        focus_option = 0
                        focus_id2 = None
                        num_to_skip = -1
                        namestr = None
                        idcard = None
                        downpath = None
                    else:
                        print("收到不正确的图并初始化")
                        focus_id2 = None
                        focus_option = 0  # 初始化

            if msg.type == 3:  #身份证和sn的图片ocr
                if msg.sender == focus_id1:
                    wcf.send_text("我收到了id1的一张图", receiver)
                    if focus_option == 1:  #识别身份证
                        str1 = wcf.download_image(msg.id, msg.extra,
                                                  sfz_path, 150)
                        idcard = botidocr(str1)
                        wcf.send_text("这好像是个身份证，身份证号是：", receiver)  #ocr
                        wcf.send_text(idcard, receiver)
                        wcf.send_text("请给我Ta的名字", receiver)
                        focus_option = 12  # 等名字


                    elif focus_option == 11:
                        print(msg.sender)
                        tempstr = wcf.download_image(msg.id, msg.extra, temp_path + r"\temp", 150)
                        shutil.move(tempstr, downpath + idcard + get_tailname(tempstr))
                        wcf.send_text("已经归档", receiver)
                        downpath = None
                        focus_option = 0
                        focus_id1 = None
                        idcard = None
                        namestr = None
                    elif focus_option == 100:
                        wcf.download_image(msg.id, msg.extra, sfz_path, 150)
                        wcf.send_text("已经归档", receiver)

                    else:
                        focus_id1 = None
                        focus_option = 0  # 初始化

            if msg.content == "路径检查":
                wcf.send_text("准备收图", msg.sender)
                focus_id1 = msg.sender
                focus_option = 100
            if msg.content == "身份证":
                wcf.send_text("准备接收身份证", receiver)
                if focus_id1 is None:
                    focus_id1 = msg.sender
                else:
                    wcf.send_text("有人在用，你等一下", receiver)
                    continue
                focus_option = 1
            if msg.content == "sn处理":
                wcf.send_text("准备接收sn码", receiver)
                if focus_id2 is None:
                    focus_id2 = msg.sender
                else:
                    wcf.send_text("有人在用，你等一下", receiver)
                    continue
                focus_option = 32
            if msg.content == "aaa":
                wcf.send_text("请选择要传入两张图的目标", receiver)
                with open(name_and_data, 'r', encoding='utf-8') as read_file:
                    lines = read_file.readlines()
                    i = 1
                    mylist = chr(126) + chr(126) + chr(126) + chr(126) + "\n"
                    for line in lines:
                        mylist = mylist + str(i) + "." + line
                        i += 1
                    wcf.send_text(mylist, receiver)
                wcf.send_text("请回复我选择几号，如3", receiver)
                if focus_id2 is None:
                    focus_id2 = msg.sender
                else:
                    wcf.send_text("有人在用，你等一下", receiver)
                    continue
                focus_option = 31

            if msg.content == "bbb":
                wcf.send_text("请选择要修正sn码的目标", receiver)
                with open(name_and_data, 'r', encoding='utf-8') as read_file:
                    lines = read_file.readlines()
                    i = 1
                    mylist = chr(126) + chr(126) + chr(126) + chr(126) + "\n"
                    for line in lines:
                        mylist = mylist + str(i) + "." + line
                        i += 1
                    wcf.send_text(mylist, receiver)
                wcf.send_text("请回复我选择几号，如3", receiver)
                if focus_id2 is None:
                    focus_id2 = msg.sender
                else:
                    wcf.send_text("有人在用，你等一下", receiver)
                    continue
                focus_option = 311
        except Empty:
            continue
        except TypeError as e:
            wcf.send_text("自动识别不出这张图，请尝试截图。如果这是sn码问题，请输入bbb按照提示输入",receiver)
            focus_id2 = None
            print(e)
        except Exception as e:
            wcf.send_text("发生了严重的bug，请重试或自行上传相关内容", receiver)
            focus_option = 0
            focus_id1 = None
            focus_id2 = None
            print(e)

    wcf.keep_running()


def get_tailname(path) -> str:
    pattern = re.compile(r".[^.]+$")
    match = pattern.search(path)
    return match.group(0)


def botidocr(img_name) -> str:
    id = None
    pattern = re.compile(
        r"([1-6][1-9]|50)\d{4}(18|19|20)\d{2}((0[1-9])|10|11|12)(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]")
    ocr = PaddleOCR()
    data = ocr.ocr(img_name)
    for i in data:
        for j in i:
            match = pattern.match(j[1][0])
            if match:
                id = match.group(0)
                print(id)
    return id


def getdata():
    strdata = datetime.datetime.now().strftime("%Y%m%d")
    return strdata


def botsnocr(img_name) -> str:
    id = None
    pattern = re.compile(r"[A-Z0-9]{15,}")
    ocr = PaddleOCR()
    data = ocr.ocr(img_name)
    for i in data:
        for j in i:
            print(j[1][0])
            match = pattern.search(j[1][0])
            if match:
                id = match.group(0)
                print(id)
    return id


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


if __name__ == '__main__':
    main()
