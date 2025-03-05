import numpy as np
import pandas as pd
df1 = pd.read_csv(r"temp/sn码.txt",delimiter="\t",dtype=str)
df1.to_excel(r"temp/b.xlsx",index=False)
df12 = df1.drop_duplicates(subset='身份证',keep='first',inplace=False)
data1 = pd.DataFrame(df12)
print(data1[["销售号","客户","SN码","身份证"]])
df2 = pd.read_excel(r"temp/123.xlsx",dtype={'电话':str,'单价':int,'商品编号':str})
data2 = pd.DataFrame(df2)
#print(data2[["客户"]])
d1 = data1[['客户','身份证']]
d2 = data2[['客户','地址','电话','规格型号','商品名称','单位','数量','单价','备注','销售金额','商品编号']]
d2.loc[d2['备注'] == '一级能效','销售金额'] = d2['单价'] * 0.2
d2.loc[d2['备注'] == '二级能效','销售金额'] = d2['单价'] * 0.15
d2.loc[d2['销售金额'] > 2000,'销售金额'] = 2000
result = pd.merge(d1,d2,how='outer',on='客户')
result['身份证'] = result['身份证'].replace("", np.nan)
result_cleaned = result.dropna(subset=['身份证'])
print(result_cleaned)
result_cleaned.to_excel(r"temp/456.xlsx",index=False)