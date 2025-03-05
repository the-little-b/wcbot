# 改用 pandas.read_csv 读取并保存为 Excel
import pandas as pd
path1 = r"C:\Users\Administrator\Desktop\销售明细表.xls"
# 读取 CSV（根据文件实际分隔符调整 sep）
try:
    df = pd.read_csv(path1, sep=",", encoding="utf-8-sig")  # 处理 UTF-8 BOM
except FileNotFoundError:
    print("请关闭此程序，把销售明细表.xls下载到桌面 并正确命名后重试")
# 保存为 Excel
df.to_excel("temp/123.xlsx", index=False)