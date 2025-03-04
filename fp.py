import os
import re
import fitz

def main():
    root_path = r"D:\wcbot\wcbot" #发票批量下载所在文件夹
    temp_path = os.path.join(root_path, "temp")

    pattern1 = re.compile(r"发票批量下载_\S{1,}")
    pattern2 = re.compile(r"\S{1,}\.pdf") #获取pdf
    pattern3 = re.compile(r"_(\S{1,4})\（")
    dir_list = os.listdir(root_path)
    fppath = None
    for dir_name in dir_list:
        match = re.search(pattern1, dir_name)
        if match:
            fppath = dir_name
            break

    fp_dirlist = os.listdir(fppath)
    fp_path_list = []
    name_list = []
    for fp_dir in fp_dirlist:
        match1 = re.search(pattern2, fp_dir)
        match2 = re.search(pattern3, fp_dir)
        if match1:
            path = os.path.join(fppath, fp_dir)
            fp_path_list.append(path) #fp的pdf路径?文件名？
            name_list.append(match2.group(1)) #用户名

    temp_dirlist = os.listdir(temp_path)
    for i in range(len(name_list)):
        name = name_list[i]
        fp_path = fp_path_list[i]
        flag = 1
        for temp_dir in temp_dirlist:
            if name in temp_dir:
                namedir = os.path.join(temp_path, temp_dir)
                fp = fp_path
                pdf_image(fp,namedir)
                print(temp_dir)
                flag = 2
        if(flag == 1):
            print(name + "没有正确的文件夹")


def pdf_image(pdfPath, imgPath):
    # 打开PDF文件
    doc = fitz.open(pdfPath)

    # 由于每个文件只有一页，直接获取第一页
    page = doc.load_page(0)  # 加载第一页（索引从0开始）
    pix = page.get_pixmap()
    pix.save(os.path.join(imgPath,r"fp.jpg"))


if __name__ == '__main__':
    main()