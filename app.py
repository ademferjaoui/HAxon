import ctypes
import tkinter as tk
from tkinter import ttk
from mouse import connect, saveLog, responseError, getResource, LOG_NAME
from tray import tray_icon
try:
    from PIL import Image, ImageTk, ImageEnhance
except ImportError:
    Image=None

AUTO_REFRESH_MS=30_000
APP_NAME="Axon"
FONT="Segoe UI"
WIN_W,WIN_H=350,460
PAD=14
ROW_H=28
APPLY_W=74
ENTRY_W=66
BG_IMAGE="bgIm.jpg"
BG_DIM=0.45
BG = "#202020"
SURFACE = "#2d2d2d"
HOVER = "#3a3a3a"
BORDER = "#3f3f3f"
FG = "#f3f3f3"
MUTED = "#a0a0a0"
ACCENT = "#0078d4"
ACCENT_LIGHT = "#4cc2ff"
GREEN = "#3fb950"
ORANGE = "#d29922"
RED = "#f85149"
BAT_GOOD = "Good.Horizontal.TProgressbar"
BAT_WARN = "Warn.Horizontal.TProgressbar"
BAT_LOW = "Low.Horizontal.TProgressbar"
BAT_CHARGING = "Charging.Horizontal.TProgressbar"
SECTION_FONT=(FONT,10,"bold")

class CanvasLabel:
    def __init__(self,canvas,x,y,text,font,color,width=0,tag="ui"):
        self.canvas=canvas
        self.id=canvas.create_text(x,y,text=text,font=font,fill=color,anchor="nw",width=width,tags=tag)
    def config(self,text=None,foreground=None):
        if text is not None:
            self.canvas.itemconfigure(self.id,text=text)
        if foreground is not None:
            self.canvas.itemconfigure(self.id,fill=foreground)

class app(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry(f'{WIN_W}x{WIN_H}')
        self.resizable(False,False)
        self.razer=None
        self.log=[]
        self.hasBattery=True
        self.maxDpi=30000
        self.uiWidgets=[]
        self.batLevel=None
        self.batCharging=False
        self.dpiVar = tk.IntVar(value=800)
        self.dpiText = tk.StringVar(value="800")
        self.pollVar=tk.StringVar(value="1000")
        self.applyDarkTheme()
        self.canvas=tk.Canvas(self,width=WIN_W,height=WIN_H,bg=BG,highlightthickness=0,bd=0)
        self.canvas.pack(fill='both',expand=True)
        self.bgImage=self.loadBackground()
        if self.bgImage:
            self.canvas.create_image(0,0,image=self.bgImage,anchor='nw')
        self.buildFooter()
        self.protocol("WM_DELETE_WINDOW",self.quitApp)
        self.tray=tray_icon(self,on_quit=self.quitApp)
        self.bind("<Unmap>",self.onMinimize)
        self.rescan()
        self.after(AUTO_REFRESH_MS,self.autoRefresh)
    def applyDarkTheme(self):
        self.configure(bg=BG)
        try:
            self.update()
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
            )
        except Exception:
            pass
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=FG, bordercolor=BORDER,darkcolor=BG, lightcolor=BG, troughcolor=SURFACE, focuscolor=ACCENT)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TSeparator", background=BORDER)
        style.configure("TEntry", fieldbackground=SURFACE, foreground=FG, insertcolor=FG, bordercolor=BORDER)

        style.configure("TButton", background=SURFACE, foreground=FG, borderwidth=1, padding=(10, 4))
        style.map("TButton",
                  background=[("active", HOVER), ("pressed", "#454545")],
                  bordercolor=[("active", "#555555")])
        style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff", bordercolor=ACCENT)
        style.map("Accent.TButton",
                  background=[("active", "#1a8ae6"), ("pressed", "#005a9e"), ("disabled", SURFACE)],
                  foreground=[("disabled", MUTED)],
                  bordercolor=[("active", "#1a8ae6")])
        style.configure("Quit.TButton", background="#5a2a2a", foreground=FG, bordercolor="#5a2a2a")
        style.map("Quit.TButton",
                  background=[("active", "#7a3636"), ("pressed", "#4a2020")],
                  bordercolor=[("active", "#7a3636")])

        style.configure("TCombobox", fieldbackground=SURFACE, background=SURFACE,foreground=FG, arrowcolor=FG, borderwidth=1)
        style.map("TCombobox",fieldbackground=[("readonly", SURFACE)],selectbackground=[("readonly", SURFACE)],selectforeground=[("readonly", FG)],background=[("active", HOVER)],foreground=[("disabled", MUTED)])
        self.option_add("*TCombobox*Listbox.background", SURFACE)
        self.option_add("*TCombobox*Listbox.foreground", FG)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        style.configure("Horizontal.TScale", background=BG, troughcolor=SURFACE)
        style.map("Horizontal.TScale", background=[("active", ACCENT)])
        for name,color in ((BAT_GOOD,GREEN),(BAT_WARN,ORANGE),(BAT_LOW,RED),(BAT_CHARGING,ACCENT_LIGHT)):
            style.configure(name, background=color, troughcolor=SURFACE, bordercolor=BORDER, lightcolor=color, darkcolor=color)
    def loadBackground(self):
        if Image is None:
            return None
        try:
            img=Image.open(getResource(BG_IMAGE))
            img.draft("RGB",(WIN_W,WIN_H))
            img=img.convert("RGB")
        except OSError:
            return None
        scale=max(WIN_W/img.width,WIN_H/img.height)
        img=img.resize((int(img.width*scale)+1,int(img.height*scale)+1),getattr(Image,"Resampling",Image).LANCZOS)
        left,top=(img.width-WIN_W)//2,(img.height-WIN_H)//2
        img=img.crop((left,top,left+WIN_W,top+WIN_H))
        img=ImageEnhance.Brightness(img).enhance(BG_DIM)
        return ImageTk.PhotoImage(img)
    def put(self,widget,x,y,w,h):
        self.canvas.create_window(x,y,window=widget,anchor="nw",width=w,height=h,tags="ui")
        self.uiWidgets.append(widget)
    def clearUi(self):
        self.canvas.delete("ui")
        for widget in self.uiWidgets:
            widget.destroy()
        self.uiWidgets=[]
    def buildFooter(self):
        c=self.canvas
        btnY=WIN_H-PAD-30
        c.create_line(PAD,btnY-46,WIN_W-PAD,btnY-46,fill=BORDER,tags="footer")
        self.statusLabel=CanvasLabel(c,PAD,btnY-40,"",(FONT,9),GREEN,WIN_W-2*PAD,"footer")
        half=(WIN_W-2*PAD-8)//2
        rescanBtn=ttk.Button(c,text="Rescan",command=self.rescan)
        quitBtn=ttk.Button(c,text="Quit",style="Quit.TButton",command=self.quitApp)
        c.create_window(PAD,btnY,window=rescanBtn,anchor="nw",width=half,height=30,tags="footer")
        c.create_window(PAD+half+8,btnY,window=quitBtn,anchor="nw",width=half,height=30,tags="footer")
    def setStatus(self,text,error=False):
        self.statusLabel.config(text=text,foreground=RED if error else GREEN)
    def onMinimize(self,event):
        if event.widget is self and self.state()=="iconic":
            if self.razer == None : self.tray.start(self.batLevel,self.batCharging)
            else : self.tray.start(self.batLevel,self.batCharging,self.razer.name)
    def setBattery(self,pct,charging):
        self.batLevel,self.batCharging=pct,charging
        if self.razer == None : self.tray.update(pct,charging)
        else : self.tray.update(pct,charging,(self.razer.name))
    def quitApp(self):
        self.tray.stop()
        if self.razer:
            try:
                self.razer.handle.close()
            except Exception:
                pass
        self.destroy()
    def rescan(self):
        self.setBattery(None,False)
        if self.razer:
            try:
                self.razer.handle.close()
            except Exception:
                pass
        self.setStatus("")
        self.razer,self.log=connect()
        saveLog(self.log)
        self.buildUi()
        self.showMouse()
    def batteryStyle(self,pct,charging):
        if charging:
            return BAT_CHARGING
        if pct>=50:
            return BAT_GOOD
        if pct>=20:
            return BAT_WARN
        return BAT_LOW
    def readBattery(self):
        try :
            pct,charging=self.razer.battery()
        except (responseError, OSError) as e:
            self.setBattery(None,False)
            return f'battery: {e}'
        self.setBattery(pct,charging)
        self.bar['value']=pct
        self.bar.configure(style=self.batteryStyle(pct,charging))
        self.batteryLabel.config(text=f'{pct}%'+("  (charging)" if charging else ""))
        return None
    def showDpi(self,dpi):
        self.setDPIFields(dpi)
        self.dpiLabel.config(text=f'Current DPI : {dpi}')
    def showPoll(self,rate):
        self.pollVar.set(rate)
        self.pollLabel.config(text=f'Current Polling Rate : {rate}')
    def showMouse(self):
        if not self.razer:
            return
        r=self.razer
        error=self.readBattery() if self.hasBattery else None
        if r.lastDpi is not None:
            self.showDpi(r.lastDpi)
        if r.lastPoll is not None:
            self.showPoll(r.lastPoll)
        if error:
            self.setStatus(error,True)
        elif r.lastPoll is None:
            self.setStatus("Connected (could not read the polling rate)")
        else:
            self.setStatus("Connected")
    def refresh(self):
        if not self.razer or not self.hasBattery:
            return
        error=self.readBattery()
        if error:
            self.setStatus(error,True)
    def autoRefresh(self):
        self.refresh()
        self.after(AUTO_REFRESH_MS,self.autoRefresh)
    def snapDPI(self,value):
        return max(100,min(self.maxDpi,int(float(value)/100+0.5)*100))
    def setDPIFields(self,dpi):
        self.dpiVar.set(dpi)
        self.dpiText.set(str(dpi))
    def onSlide(self,value):
        self.setDPIFields(self.snapDPI(value))
    def readDPI(self):
        text=self.dpiText.get().strip()
        if not text.isdigit():
            raise ValueError
        return max(100,min(self.maxDpi,int(text)))
    def applyDPI(self):
        try :
            dpi=self.readDPI()
        except ValueError:
            self.setStatus("DPI must be a whole number",True)
            return
        try :
            self.razer.setDPI(dpi)
            self.showDpi(dpi)
            self.setStatus(f'DPI successfully set to : {dpi}')
        except (responseError,OSError)as e:
            self.setStatus(f'set DPI to {dpi} failed: {e}',True)
    def applyPoll(self):
        try :
            poll=int(self.pollVar.get())
            self.razer.setPOLL(poll)
            self.showPoll(poll)
            self.setStatus(f'Polling Rate successfully set to : {poll}')
        except ValueError:
            self.setStatus("Choose a polling rate first",True)
        except (responseError,OSError) as e:
            self.setStatus(f"set Polling Rate failed: {e}",True)
    def buildUi(self):
        self.clearUi()
        c=self.canvas
        full=WIN_W-2*PAD
        CanvasLabel(c,PAD,PAD,APP_NAME,(FONT,20,"bold"),ACCENT_LIGHT)
        y=PAD+40
        if not self.razer:
            CanvasLabel(c,PAD,y,"Mouse not found.",(FONT,11),RED)
            CanvasLabel(c,PAD,y+28,f"Details saved to {LOG_NAME}",(FONT,10),MUTED)
            return
        r=self.razer
        self.hasBattery=r.profile.get('battery',True)
        self.maxDpi=r.profile.get('max_dpi',30000)
        name=r.name or "Razer device"
        if r.dongle:
            name+="  \u00b7  HyperPolling dongle"
        CanvasLabel(c,PAD,y,name,(FONT,11),MUTED,full); y+=34
        if self.hasBattery:
            CanvasLabel(c,PAD,y,"Battery",SECTION_FONT,ACCENT_LIGHT); y+=22
            self.bar=ttk.Progressbar(c,maximum=100,style=BAT_GOOD)
            self.put(self.bar,PAD,y,full,16); y+=22
            self.batteryLabel=CanvasLabel(c,PAD,y,"?",(FONT,10),FG); y+=34

        applyX=WIN_W-PAD-APPLY_W
        entryX=applyX-8-ENTRY_W
        self.dpiLabel=CanvasLabel(c,PAD,y,"DPI",SECTION_FONT,ACCENT_LIGHT); y+=24
        scale=ttk.Scale(c,from_=100,to=self.maxDpi,variable=self.dpiVar,command=self.onSlide)
        self.put(scale,PAD,y,entryX-8-PAD,ROW_H)
        digitsOnly=(self.register(lambda s: s=="" or (s.isdigit() and len(s)<=6)),"%P")
        dpiEntry=ttk.Entry(c,textvariable=self.dpiText,validate="key",validatecommand=digitsOnly,justify="center")
        dpiEntry.bind("<Return>",lambda e: self.applyDPI())
        self.put(dpiEntry,entryX,y,ENTRY_W,ROW_H)
        self.put(ttk.Button(c,text="Apply",style="Accent.TButton",command=self.applyDPI),applyX,y,APPLY_W,ROW_H)
        y+=ROW_H+14

        self.pollLabel=CanvasLabel(c,PAD,y,"Polling rate",SECTION_FONT,ACCENT_LIGHT); y+=24
        rates=r.available_rates
        self.pollBox=ttk.Combobox(c,textvariable=self.pollVar,values=[str(hz) for hz in rates],state="readonly")
        self.put(self.pollBox,PAD,y,entryX+ENTRY_W-PAD,ROW_H)
        pollApply=ttk.Button(c,text="Apply",style="Accent.TButton",command=self.applyPoll)
        self.put(pollApply,applyX,y,APPLY_W,ROW_H)
        hint=None
        if not rates:
            self.pollBox.state(["disabled"])
            pollApply.state(["disabled"])
            hint="Polling rate is not available on this connection"
        elif r.profile.get('dongle_polling_rate',0)>1000 and r.maxPoll<2000:
            hint="Rates above 1000 Hz need the HyperPolling dongle"
        if hint:
            CanvasLabel(c,PAD,y+ROW_H+6,hint,(FONT,9),MUTED,full)
if __name__ == "__main__":
    app().mainloop()