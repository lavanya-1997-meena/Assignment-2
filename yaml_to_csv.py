import os
import yaml
import pandas as pd
import pymysql
from sqlalchemy import create_engine


def create_database(db_name):
    conn=pymysql.connect(
        host="localhost",
        user="root",
        password="password")
    
    cursor=conn.cursor()

    cursor.execute(
        f"Create database IF NOT exists {db_name}")
    
    conn.commit()
    conn.close()
    
    print(f"{db_name} created successfully")





def get_connection():
    
    conn=pymysql.connect(
        host="localhost",
        user="root",
        password="password",
        database="stock_db"
      )
    print('connected successfuly')
    return conn

def load_months(folder):
    
    yaml_files=[f for f in os.listdir(folder)
                if f .endswith('.yaml')]
    
    all_df=[]

    for file in yaml_files:
        file_path=os.path.join(folder,file)
        with open (file_path,'r') as f:
            data=yaml.safe_load(f)
            if data is None:
                continue
            elif isinstance(data,dict):
                all_df.append(data)
            elif isinstance(data,list):
                all_df.extend(data)
            else:
                print(f"invalid yaml format : {file_path}")
                continue

     
    return pd.DataFrame(all_df)

def all_month_df(base_folder,months):

    all_months=[]

    for month in months:

        month_folder=os.path.join(base_folder,month)
        if os.path.exists(month_folder):
         month_df=load_months(month_folder)
         all_months.append(month_df)
        else:
            print(f"folder not found :{month_folder}")
    
    df=pd.concat(all_months,ignore_index=True)
    return df




def df_to_csv(df,folder):

    for ticker,ticker_df in df.groupby('Ticker'):
        file_path=os.path.join(folder,f'{ticker}.csv')
        ticker_df.to_csv(file_path, index=False)

    print('All CSV Files saved in successfully')

base_folder=r'F:\Stock Driven Analysis\data' 
months=['2023-10','2023-11','2023-12','2024-01','2024-02','2024-03','2024-04',
        '2024-05','2024-06','2024-07','2024-08','2024-09','2024-10','2024-11']
df=all_month_df(base_folder,months)
df_to_csv(df,r'F:\Stock Driven Analysis\data1')


def To_load_Sql(base_folder,months):
    try:
     df=all_month_df(base_folder,months)

    # convert date column to datetime & to add new month name column

     df['date']=pd.to_datetime(df['date'], errors='coerce')
     df['date']=df['date'].dt.date
     df['month_name']=pd.to_datetime(df['month'], format='%Y-%m').dt.month_name()
     
    # connect to sql(database)

     engine=create_engine("mysql+pymysql://root:password@localhost/stock_db")
     df.to_sql(
        'stocks',
        con=engine,
        if_exists='replace',
        index=False
     )
     
    except Exception as e:
        print("error:",e) 


base_folder=r'F:\Stock Driven Analysis\data' 
months=['2023-10','2023-11','2023-12','2024-01','2024-02','2024-03','2024-04',
        '2024-05','2024-06','2024-07','2024-08','2024-09','2024-10','2024-11']
To_load_Sql(base_folder, months)


