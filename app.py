from sqlalchemy import create_engine
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="Stock Analysis Dashboard ",
    
    layout="wide"
)

st.markdown("""
<style>
.stApp {
     background: linear-gradient(
        180deg,
        #0b6e2b 0%,
        #148f3d 50%,
        #1db954 100%
    );
}
</style>
""", unsafe_allow_html=True)



st.title(
    "Stock Analysis Dashboard :chart_with_upwards_trend:",
    text_alignment="center"
    )
st.markdown(
    "<h4 style='text-align:center; color:white;'>Welcome to Stock Analysis Dashboard</h4>",
    unsafe_allow_html=True
)

engine = create_engine(
    "mysql+pymysql://root:password@localhost/stock_db"
)


def home():
    st.markdown("""
      <h2 style='text-align:center;
      color:white;'>
      Dashboard Overview
      </h2>""",unsafe_allow_html=True)
    df1=pd.read_sql("select * from open_close",engine )
    df1["stock_type"] = df1["stock_type"].str.strip()
    

    a, b,c, d = st.columns(4, gap='small')
    total = len(df1["Ticker"].unique())
    avg_price =round(df1["avg_price"].mean(), 2)
    avg_volume=int(df1["avg_volume"].mean())
    green = len(df1[df1["stock_type"] == "Green"])
    red = len(df1[df1["stock_type"] == "Red"])


    a.metric("Total Stocks", total)
    b.metric("Avg Price",avg_price)
    c.metric("Avg Volume",avg_volume)
    d.metric("Green/Red",f"{green}/{red}")

    st.divider()

    left, right=st.columns(2)
    top_10=(df1.sort_values('yearly_return',ascending=False).head(10).reset_index(drop=True))
    left.subheader("Top 10 Gainer",text_alignment="center")
    left.write("This section shows the top 10 gainers." )
    left.dataframe(top_10[['Ticker','yearly_return']])
    loss_10=(df1[df1['stock_type']=='Red'].sort_values('yearly_return',ascending=True)).head(10).reset_index(drop=True)
    right.subheader("Top 10 Loser", text_alignment="center")
    right.write("This section shows the top 10 losers.")
    right.dataframe(loss_10[['Ticker','yearly_return','stock_type']])

def volatility():

    st.header("Volatility")
    st.write("To Calculate Volatility Return")
    df=pd.read_sql("select * from stocks",engine)
    df=df.sort_values(['Ticker','date'])
    df['previous_close']=df.groupby('Ticker')['close'].shift(1)
    df['daily_return']=(df['close']-df['previous_close'])/df['previous_close']
    df['previous_close']=df['previous_close'].fillna(0)
    df['daily_return']=df['daily_return'].fillna(0)
    volatility_df=df.groupby('Ticker')['daily_return'].std().reset_index()
    volatility_df.columns=['Ticker','volatility']

#-------------barchart--------------

    fig, ax = plt.subplots(figsize=(12,6))
    ax.bar(volatility_df['Ticker'],volatility_df['volatility'],color='red')
    ax.set_title("Volatility Return")
    ax.set_xlabel("Ticker")
    ax.set_ylabel("volitility")
    plt.xticks(rotation=90)
    st.pyplot(fig)

    st.divider()
    st.markdown("***show a dataframe***",text_alignment="center")
    st.divider()
    st.subheader("Volatility Data")
    st.dataframe(volatility_df)
#----------------------------------------------------------------


def cumulative():
    df = pd.read_sql("SELECT * FROM stocks", engine)
    df=df.sort_values(['Ticker','date']).reset_index(drop=True)
    df['previous_close']=df.groupby('Ticker')['close'].shift(1)
    df['daily_return']=(df['close']-df['previous_close'])/df['previous_close']
    df['previous_close']=df['previous_close'].fillna(0)
    df['daily_return']=df['daily_return'].fillna(0)
    cum_df=df[['Ticker','date','month','daily_return']]
    cum_df['cumulative_return']=df.groupby('Ticker')['daily_return'].cumsum()

#-----------linechart---------

    top5=cum_df.groupby('Ticker')['cumulative_return'].last().sort_values(ascending=False).head(5)
    top5_data = cum_df[cum_df['Ticker'].isin(top5.index)]
    colors = ["red", "blue", "green", "orange", "purple"]
    fig, ax = plt.subplots(figsize=(12, 6))

    for ticker, color in zip(top5.index, colors):

        stock = top5_data[top5_data["Ticker"] == ticker]

        ax.plot(
            stock["month"],
            stock["cumulative_return"],
            label=ticker,
            color=color,
            linewidth=3,
            marker="o"
        )

    ax.set_title("Top 5 Cumulative Returns")
    ax.set_xlabel("Month")
    ax.set_ylabel("Cumulative Return")
    ax.legend()
    plt.xticks(rotation=45)

    st.pyplot(fig)
   
#---------------correlation----------------

def correlation():
      st.header("Correlation Heatmap")
      df = pd.read_sql("SELECT * FROM stocks", engine)
      new_df=pd.pivot_table(df,index='date',columns='Ticker',values='close',aggfunc='mean')
      corr_matrix=new_df.corr()

      fig, ax = plt.subplots(figsize=(12, 6))

      sns.heatmap(
              corr_matrix,
              cmap='coolwarm',
              linewidths=0.5,
              ax=ax
          )
      plt.xticks(rotation=90, fontsize=10)
      plt.yticks(rotation=0, fontsize=10)
      ax.set_title("Stock Price Correlation Heatmap")
      st.pyplot(fig)

#------------sector-----------------------------


def sector():
    st.header("Average Return by Sector",text_alignment='center')
    sec_df = pd.read_sql("SELECT * FROM sector", engine)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=sec_df,x='sector',y='avg_return',
                           hue='sector',ax=ax)
    plt.xlabel('Sector')
    plt.ylabel('Average Return')
    plt.xticks(rotation=90)
    ax.set_title("Average return by Sector")
    st.pyplot(fig)

#-------------loss&gain-------------------------


def monthly():
    l_g=pd.read_sql("select * from loss_gain",engine)
    
    month=l_g['month'].unique()
    selected_month = st.multiselect("Select Month(s)", month)
    if not selected_month:
        st.warning("Please select atleast one month.")

    month_data=l_g[l_g['month'].isin(selected_month)]
    st.subheader("Filtered Month",text_alignment="center")
    st.dataframe(month_data)

    fig, ax=plt.subplots(figsize=(10,5))
    
    sns.barplot(data=month_data,
                            x='Ticker',
                            y='Monthly_return',
                            hue='Ticker',
                            ax=ax)
    ax.set_title(f"Top 5 Gainers & Losers - {', '.join(selected_month)}")
    plt.xticks(rotation=45)
    st.pyplot(fig)
     
pg = st.navigation([
        st.Page(home, title="🏠 Home"),
        st.Page(volatility,title="📈 Volatility"),
        st.Page(cumulative, title="📊 Cumulative"),
        st.Page(correlation, title="🔗 Correlation"),
        st.Page(sector, title="🏢 Sector"),
        st.Page(monthly, title="📅 Monthly")
        ])
     

pg.run()