# 测试pandas
import pandas as pd
import numpy as np


if __name__ == '__main__':
    '''with open('../dataset/实验四_网络入侵样本数据.csv') as f:
        df = pd.read_csv(f)
    print(df.describe(include=np.number).T)
    print(df.select_dtypes(include=np.object).empty)'''
    a = pd.DataFrame({'key': ['dd', 'df', 'ff'],
                      'value': [1, 2, 3]}, index=['a', 'b', 'c'])
    print(a)


