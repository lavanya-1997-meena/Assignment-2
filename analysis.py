from sqlalchemy import create_engine
import pandas as pd
from yaml_to_csv import all_month_df
import seaborn as sns
import matplotlib.pyplot as plt




class stockdata:
  
  def __init__(self,base_folder,months):
    self.base_folder=base_folder
    self.months=months

  def connect_sql(self):
     
    self.engine= create_engine("mysql+pymysql://root:password@localhost/stock_db")



# loading the data's and convert to Dataframe

  def load_data(self):
    self.df=all_month_df(self.base_folder,self.months)
    self.df['date']=pd.to_datetime(self.df['date'], errors='coerce')
    self.df['date']=self.df['date'].dt.date
    return self.df
  
# calculating yearly return and create a new column  which name was stock type 
  def calculate_top_loss(self):
    
      self.df = self.df.sort_values('date')
      self.open_close=self.df.groupby('Ticker').agg(
       previous_close_price=('close','first'),
       current_close_price=('close','last')
       ).reset_index()

      self.open_close['yearly_return']=(self.open_close['current_close_price']-self.open_close['previous_close_price'])/self.open_close['previous_close_price']*100

      def stock_type(yearly_return):
          try:
             if yearly_return>0:
                return "Green"
             else:
                return "Red"
          except:
                return "no value"
   
      self.open_close['stock_type']=self.open_close['yearly_return'].apply(stock_type)
      Top_10=self.open_close.sort_values('yearly_return',ascending=False).head(10).reset_index(drop=True)
      Loss_10=self.open_close[self.open_close["stock_type"]=="Red"].sort_values(['yearly_return'],ascending=True).head(10).reset_index(drop=True)
      return Top_10, Loss_10

  # calculate average price & volume
  
  def average_price_volume(self):
   
      self.price_df=self.df.groupby('Ticker')['close'].mean().reset_index(name='avg_price')

      self.volume_df=self.df.groupby('Ticker')['volume'].mean().reset_index(name='avg_volume')

      self.open_close = self.open_close.merge(self.price_df, on='Ticker', how='left')
      self.open_close = self.open_close.merge(self.volume_df, on='Ticker', how='left')
      stock_count=self.open_close['stock_type'].value_counts()
      avg_price=self.open_close['avg_price'].mean()
      avg_volume=self.open_close['avg_volume'].mean()

      print(self.open_close.head())
      print(self.open_close.columns.tolist())

      return self.open_close, stock_count, avg_price, avg_volume
  
#save to sql
  def save_open_close_sql(self):

        print("Before SQL Save")
        print(self.open_close.head())
        print(self.open_close.columns)
    

        self.open_close.to_sql(
           'open_close',
           con=self.engine,
           if_exists='replace',
           index=False
           )
        



                                                ##volacity analysis 

#volatility calculation
  
  def volatility(self):
      self.df=self.df.sort_values(['Ticker','date'])
      self.df['previous_close']=self.df.groupby('Ticker')['close'].shift(1)
      self.df['daily_return']=(self.df['close']-self.df['previous_close'])/self.df['previous_close']
      self.df['previous_close']=self.df['previous_close'].fillna(0)
      self.df['daily_return']=self.df['daily_return'].fillna(0)
      self.volatility_df=self.df.groupby('Ticker')['daily_return'].std().reset_index()
      self.volatility_df.columns=['Ticker','volatility']
      return self.volatility_df

# to save sql
  def save_volatility_sql(self):
      self.volatility_df.to_sql(
         'volatility',
         con=self.engine,
         if_exists='replace',
         index=False
         )
      

#plotting volatility

  def plot_volatility(self):

      Top10_volatility=self.volatility_df.sort_values(['volatility'],ascending=False).head(10)

      plt.figure(figsize=(12,6))
      sns.barplot(
         data=Top10_volatility,
         x='Ticker',
         y='volatility'
          )
      plt.title('Top 10 Stock Volatility')
      plt.xlabel('Ticker')
      plt.ylabel('Volatility')
      plt.show()


               #cumulative return
  def cumulative_return(self):
      self.df=self.df.sort_values(['Ticker','date']).reset_index(drop=True)
      
      self.cum_df=self.df[['Ticker','date','month','daily_return']]
      self.cum_df['cumulative_return']=self.df.groupby('Ticker')['daily_return'].cumsum()
      print(self.df[['Ticker', 'date', 'daily_return']].head(10))
      print(self.df.groupby('Ticker')['daily_return'].cumsum().head(10))

      print(self.cum_df)
      return self.cum_df
  # to save sql
  def save_cumulative_sql(self):
      self.cum_df.to_sql(
               'cumulative',
               con=self.engine,
               if_exists='replace',
               index=False
               )
      

  def line_plot_cumulative(self):

      top5=self.cum_df.groupby('Ticker')['cumulative_return'].last().sort_values(ascending=False).head(5)

      top5_data = self.cum_df[self.cum_df['Ticker'].isin(top5.index)]

      plt.figure(figsize=(15,8))

      sns.lineplot(
              x='month',
              y='cumulative_return',
              hue='Ticker',
              data=top5_data,
              )

      plt.xlabel("Month")
      plt.ylabel("Cumulative Return")
      plt.title("Top 5 Performing Stocks - Cumulative Return Over Time")
      plt.legend()
      plt.show()

# mapping ticker to which is the correct sector and calculate average return for each sector

  def sector(self):
      sector_df=pd.read_csv('F:/Stock Driven Analysis/Sector_data - Sheet1.csv')
      sector_df['COMPANY']=sector_df['COMPANY'].str.upper().str.replace('[^A-Z]','', regex=True)
      self.open_close['Ticker']=self.open_close['Ticker'].str.upper().str.replace('[^A-Z]','',regex=True)
      mapp={
            'ADANIENT':'ADANIENTERPRISES',
            'ADANIPORTS':'ADANIPORTSSEZ',
            'APOLLOHOSP':'APOLLOHOSPITALS',
            'ASIANPAINT':'ASIANPAINTS',
            'AXISBANK':'AXISBANK',
            'BAJAJAUTO':'BAJAJAUTO',
            'BAJAJFINSV':'BAJAJFINSERV',
            'BAJFINANCE':'BAJAJFINANCE',
            'BEL':'BHARATELECTRONICS',
            'BHARTIARTL':'BHARTIAIRTEL',
            'BPCL':'BPCL',
            'BRITANNIA':'',
            'CIPLA':'CIPLA',
            'COALINDIA':'COALINDIA',
            'DRREDDY':'DRREDDYSLAB',
            'EICHERMOT':'EICHERMOTORS',
            'GRASIM':'GRASIM',
            'HCLTECH':'HCLTECHNOLOGIES',
            'HDFCBANK':'HDFCBANK',
            'HDFCLIFE':'HDFCLIFEINSURANCE',
            'HEROMOTOCO':'HEROMOTOCORP',
            'HINDALCO':'HINDALCO',
            'HINDUNILVR':'HINDUSTANUNILEVER',
            'ICICIBANK':'ICICIBANK',
            'INDUSINDBK':'INDUSINDBANK',
            'INFY':'INFOSYS',
            'ITC':'ITC',
            'JSWSTEEL':'JSWSTEEL',
            'KOTAKBANK':'KOTAKMAHINDRABANK',
            'LT':'LT',
            'MM':'MM',
            'MARUTI':'MARUTISUZUKI',
            'NESTLEIND':'NESTLE',
            'NTPC':'NTPC',
            'ONGC':'ONGC',
            'POWERGRID':'POWERGRID',
            'RELIANCE':'RELIANCEIND',
            'SBILIFE':'SBILIFEINSURANCE',
            'SBIN':'SBI',
            'SHRIRAMFIN':'SHRIRAMFINANCE',
            'SUNPHARMA':'SUNPHARMA',
            'TATACONSUM':'TATACONSUMER',
            'TATAMOTORS':'TATAMOTORS',
            'TATASTEEL':'TATASTEEL',
            'TCS':'TCS',
            'TECHM':'TECHMAHINDRA',
            'TITAN':'TITAN',
            'TRENT':'TRENT',
            'ULTRACEMCO':'ULTRATECHCEMENT',
            'WIPRO':'WIPRO'
            }

      self.open_close['company_name']=self.open_close['Ticker'].map(mapp)
      mapping=dict(zip(sector_df['COMPANY'],sector_df['sector']))
      def sec_tic(x):
          for key in mapping:
              if key in x:
               return mapping[key]
          return 'Unknown'
      self.open_close['sector']=self.open_close['company_name'].apply(sec_tic)   
      self.sect_df=self.open_close.groupby('sector')['yearly_return'].mean().reset_index()
      self.sect_df.columns=['sector','avg_return']
      print(self.sect_df)
      return self.sect_df
      
      # to save sql

  def save_sector_sql(self):
      self.sect_df.to_sql(
               'sector',
               con=self.engine,
               if_exists='replace',
               index=False
               )
      
  def sector_plot(self):

      plt.figure(figsize=(10,10))
      sns.barplot(data=self.sect_df,x='sector',y='avg_return',
                  hue='sector')
      plt.title("Average Return by Sector")
      plt.xlabel('Sector')
      plt.ylabel('Average Return')
      plt.xticks(rotation=45)
      plt.show()


# Stock Price Correlation
  def calculate_correlation(self):
    self.new_df=pd.pivot_table(self.df,index='date',columns='Ticker',values='close',aggfunc='mean')
    self.corr_matrix=self.new_df.corr()
    return self.corr_matrix
    

    # to save sql
  def save_corr_sql(self):

    self.corr_matrix.to_sql(
             'correlation',
             con=self.engine,
             if_exists='replace',
             index=False
             )
    
# plotting correlation
  def plot_correlation(self): 
    plt.figure(figsize=(10,10))
    sns.heatmap(
        self.corr_matrix,
        cmap='coolwarm',
        linewidths=0.5
    )
    plt.xticks(rotation=90, fontsize=10)
    plt.yticks(rotation=0, fontsize=10)
    plt.title("Stock Price Correlation Heatmap")
    plt.show()

# Top 5 Gainers and Losers (Month-wise)

  def calculate_loss_gain(self):
    self.df = self.df.sort_values('date')
    loss_gain=self.df.groupby(['Ticker','month']).agg(
        month_first_price=('close','first'),
        current_month_price=('close','last')
    ).reset_index()

    loss_gain['monthly_return']=(loss_gain['current_month_price']-loss_gain['month_first_price'])/loss_gain['month_first_price']*100
    l_g=loss_gain.pivot_table(index='Ticker',columns='month',values='monthly_return')
    result=[]
    for month in l_g.columns.unique():
        month_data =l_g[month]

        Top_gainers=month_data.nlargest(5)
        Top_losers=month_data.nsmallest(5)

        
        self.combine_l_g=pd.concat([Top_gainers,Top_losers])
        self.combine_l_g=self.combine_l_g.reset_index()
        self.combine_l_g.columns=['Ticker','Monthly_return']
        self.combine_l_g['month']=month
        result.append(self.combine_l_g)
    self.combine_l_g=pd.concat(result,ignore_index=True)
    return self.combine_l_g
    
    # to save sql
  def save_loss_gain_sql(self):
      self.combine_l_g.to_sql(
             'loss_gain',
             con=self.engine,
             if_exists='replace',
             index=False
             ) 

    
# plotting loss & gainers in bar chart

  def plot_loss_gain(self):
    for month in self.combine_l_g['month'].unique():
       month_data=self.combine_l_g[self.combine_l_g['month']==month]
       plt.figure(figsize=(10,5))

       sns.barplot(data=month_data,
                        x='Ticker',
                        y='Monthly_return',
                        hue='Ticker')
       plt.title(f"Top 5 Gainers & Losers - {month}")
       plt.xticks(rotation=45)
       plt.show()

base_folder=r'F:\Stock Driven Analysis\data' 
months=['2023-10','2023-11','2023-12','2024-01','2024-02','2024-03','2024-04',
        '2024-05','2024-06','2024-07','2024-08','2024-09','2024-10','2024-11']

stock=stockdata(base_folder,months)
stock.connect_sql()
stock.load_data()
stock.calculate_top_loss()
stock.average_price_volume()
stock.save_open_close_sql()
stock.volatility()
stock.save_volatility_sql()
stock.plot_volatility()
stock.cumulative_return()
stock.save_cumulative_sql()
stock.line_plot_cumulative()
stock.sector()
stock.save_sector_sql()
stock.sector_plot()
stock.calculate_correlation()
stock.save_corr_sql()
stock.plot_correlation()
stock.calculate_loss_gain()
stock.save_loss_gain_sql()
stock.plot_loss_gain()

