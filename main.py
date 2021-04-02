from window import Window
import datetime as dt

date = dt.date(2021,3,30)

app = Window(f"projections_last30/{date.strftime('%y_%m_%d')}.csv")
app.mainloop()