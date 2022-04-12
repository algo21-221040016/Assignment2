# Assignment2
Second assignment for algo-trading

Industry rotation strategy is commonly used in asset allocation especially when the stock market
shows obvious tendency, such as bull market or bear market. The most widely-used industry factor is 
industry momentum. But in this research report, authors tried to build another factor which is 
Financial Analyst Pros Index, FAPI.FAPI tried to combine the thoughts of analysts in stock markets, which 
is a new kind of index to reflect the prosperity of industry.

The construction of FAPI referd to PMI index and calculate the profit forecast of 
different brokers on different industry in markets regularly and then get the amount of brokers that 
rise the forecasted profits. Finally, FAPI is the weighted proportion according to 
diffusion index.

This research report also gives a kind of strategy to apply FAPI. Simply speaking, we 
first use FAPI to allocate industries and then use PB-ROE strategy to choose the stocks
in industry.

However, in the process of reappearance of the idea, I find it hard to 
get the python api of wind(I don't have a wind account). Thus, I downloaded 
the forecast date of analysts in 2021 and corresponding financial data to finish
the offline calculation, which leads to that some functions in the code are
designed only for this specific case. If the python api is available, there will
be a little difference but I believe that the general idea is similar.

On the other hand, in this assignnent, I only focused on the construction of 
FAPI and ignored the strategy and application of FAPI. More details of 
my thoughts can be found in the notes on the code.

Thanks for reading