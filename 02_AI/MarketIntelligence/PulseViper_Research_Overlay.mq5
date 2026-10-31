// PulseViper research overlay: chart drawing only; no trading code.
#property copyright "PulseViper research"
#property version   "1.00"
#property indicator_chart_window
#property indicator_plots 0
#property strict

input int InpRefreshSeconds = 5;
input int InpMaxAgeMinutes = 20;
input bool InpShowBlockedSell = false;

string PREFIX = "PV_RESEARCH_";
string FILE_NAME = "PulseViper_Signal_Levels.csv";

void DrawLevel(const string tag, const double price, const color col, const ENUM_LINE_STYLE style)
{
   string name = PREFIX + tag;
   if(price <= 0) { ObjectDelete(0, name); return; }
   if(ObjectFind(0, name) < 0)
      if(!ObjectCreate(0, name, OBJ_HLINE, 0, 0, price)) return;
   ObjectSetDouble(0, name, OBJPROP_PRICE, price);
   ObjectSetInteger(0, name, OBJPROP_COLOR, col);
   ObjectSetInteger(0, name, OBJPROP_STYLE, style);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetString(0, name, OBJPROP_TEXT, "PV " + tag);
}

void ClearLevels()
{
   string tags[] = {"BUY","BUY_SL","BUY_TP1","BUY_TP2","SELL","SELL_SL","SELL_TP1","SELL_TP2"};
   for(int i=0; i<ArraySize(tags); ++i)
      ObjectDelete(0, PREFIX + tags[i]);
}

int OnInit()
{
   EventSetTimer(MathMax(1, InpRefreshSeconds));
   IndicatorSetString(INDICATOR_SHORTNAME, "PulseViper Read-Only Levels");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   ClearLevels();
   Comment("");
}

int OnCalculate(const int rates_total,const int prev_calculated,const datetime &time[],
                const double &open[],const double &high[],const double &low[],
                const double &close[],const long &tick_volume[],
                const long &volume[],const int &spread[])
{
   return rates_total;
}

void OnTimer()
{
   int f=FileOpen(FILE_NAME, FILE_READ|FILE_CSV|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ, ',');
   if(f == INVALID_HANDLE) { ClearLevels(); Comment("PulseViper: waiting for Python signal exporter"); return; }
   string v=FileReadString(f);
   string sym=FileReadString(f);
   string stamp=FileReadString(f);
   string decision=FileReadString(f);
   double buy=FileReadNumber(f);
   double buySL=FileReadNumber(f);
   double buyTP1=FileReadNumber(f);
   double buyTP2=FileReadNumber(f);
   int buyOK=(int)FileReadNumber(f);
   double sell=FileReadNumber(f);
   double sellSL=FileReadNumber(f);
   double sellTP1=FileReadNumber(f);
   double sellTP2=FileReadNumber(f);
   int sellOK=(int)FileReadNumber(f);
   FileClose(f);

   long epoch=(long)StringToInteger(stamp);
   // TimeGMT is independent from broker chart timezone.
   long age=(long)TimeGMT()-epoch;
   if(v!="PV1" || sym!=_Symbol || epoch<=0 || age<0 || age>InpMaxAgeMinutes*60)
   {
      ClearLevels();
      Comment("PulseViper: stale/mismatched signal. Chart=",_Symbol," file=",sym);
      return;
   }

   DrawLevel("BUY", buyOK==1 ? buy : 0, clrDeepSkyBlue, STYLE_SOLID);
   DrawLevel("BUY_SL", buyOK==1 ? buySL : 0, clrTomato, STYLE_DASH);
   DrawLevel("BUY_TP1", buyOK==1 ? buyTP1 : 0, clrLimeGreen, STYLE_DOT);
   DrawLevel("BUY_TP2", buyOK==1 ? buyTP2 : 0, clrLimeGreen, STYLE_DOT);

   bool showSell=(sellOK==1 || InpShowBlockedSell);
   DrawLevel("SELL", showSell ? sell : 0, clrOrangeRed, STYLE_SOLID);
   DrawLevel("SELL_SL", showSell ? sellSL : 0, clrTomato, STYLE_DASH);
   DrawLevel("SELL_TP1", showSell ? sellTP1 : 0, clrOrange, STYLE_DOT);
   DrawLevel("SELL_TP2", showSell ? sellTP2 : 0, clrOrange, STYLE_DOT);

   Comment("PulseViper research | ",decision," | ",TimeToString((datetime)epoch,TIME_DATE|TIME_MINUTES),
           " UTC | BUY:",(buyOK==1?"possible":"blocked")," | SELL:",(sellOK==1?"possible":"blocked"),
           "\nNot a live trade signal; no trading permission.");
   ChartRedraw(0);
}
