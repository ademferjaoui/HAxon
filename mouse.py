import hid
import os
import time
import sys
import json
from pathlib import Path
RAZER_VID=0x1532
TXNS=[0x1F,0x3F,0xFF,0x9F]
STATUS={
    0x01:"device busy",
    0x03:"command failed",
    0x04:"command timed out",
    0x05:"command not supported",
}
HYPERPOLL_RATES = {
    8000: 0x01,
    4000: 0x02,
    2000: 0x04,
    1000: 0x08,
    500:  0x10,
    250:  0x20,
    125:  0x40,
}
HYPERPOLL_RATES_INV={0x01:8000,0x02:4000,0x04:2000,0x08:1000,0x10:500,0x20:250,0x40:125,}
LEGACY_POLLING_RATES={
    1000: 0x01,
    500: 0x02,
    125: 0x08,
}
LEGACY_POLLING_RATES_INV={
    0x08: 125,
    0x02:500,
    0x01:1000
}
LEGACY_COMMANDS=(
    ((0x00,0xC0,0x01),(0x00,0x40,0x01)),
    ((0x00,0x85,0x01),(0x00,0x05,0x01)),
)

def getAppDir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

def getDataDir():
    base=os.environ.get("LOCALAPPDATA")
    if getattr(sys, "frozen", False) and base:
        folder=Path(base)/"Axon"
        try:
            folder.mkdir(parents=True,exist_ok=True)
            return folder
        except OSError:
            pass
    return getAppDir()

def getResource(name):
    local=getAppDir()/name
    if local.exists():
        return local
    bundled=getattr(sys,"_MEIPASS",None)
    if bundled and (Path(bundled)/name).exists():
        return Path(bundled)/name
    return local

LOG_NAME="Axon.log"
MICE_PATH=getResource("mice.json")
MOUSE_PATH=getDataDir()/"mouse.json"
DEFAULT_PROFILE={"name":"Unknown device","wireless":False,"hyperpoll":False,"max_dpi":16000,"polling_rate":1000}

def loadJson(path):
    try:
        with open(path,encoding="utf-8") as f:
            return json.load(f)
    except (OSError,json.JSONDecodeError):
        return {}

def pidKey(pid):
    return f"0x{pid:04X}"

CACHE=loadJson(MOUSE_PATH)
PROFILES=None

def getProfile(pid):
    global PROFILES
    key=pidKey(pid)
    if CACHE.get("pid")==key and isinstance(CACHE.get("profile"),dict):
        return CACHE["profile"]
    if PROFILES is None:
        PROFILES=loadJson(MICE_PATH)
    return PROFILES.get(key,DEFAULT_PROFILE)

class responseError(Exception):
    pass

def buildCommand(txn,ccls,cid,size,args=()):
    cmd=bytearray(91)
    cmd[2]=txn
    cmd[6]=size
    cmd[7]=ccls
    cmd[8]=cid
    cmd[9:9+len(args)]=bytes(args)
    chks=0
    for b in cmd[3:89]:
        chks^=b
    cmd[89]=chks
    return bytes(cmd)

class mouse:
    def __init__(self,handle,txn,pid,iface,product=""):
        self.profile=getProfile(pid).copy()
        self.handle,self.txn,self.name,self.pid,self.iface=handle,txn,self.profile.get('name'),pid,iface
        self.dongle='hyperpolling' in f"{product} {self.name or ''}".lower()
        cap=self.profile.get('polling_rate',1000)
        if self.dongle:
            cap=max(cap,self.profile.get('dongle_polling_rate',0))
            if cap<=1000:
                cap=8000
        self.maxPoll=cap
        self.hyperpoll=False
        self.legacyIndex=0
        self.lastDpi=None
        self.lastPoll=None
    def save_mouse(self):
        entry={"pid":pidKey(self.pid),"iface":self.iface,"txn":self.txn,"profile":self.profile}
        try :
            with open(MOUSE_PATH, 'w', encoding="utf-8") as f :
                json.dump(entry,f)
        except OSError:
            pass 

    def transact(self,ccls,cid,size,args=()):
        self.handle.send_feature_report(buildCommand(self.txn,ccls,cid,size,args))
        time.sleep(0.04)
        resp=bytearray(self.handle.get_feature_report(0,91))
        if len(resp)==90:
            resp=bytearray([0])+resp
        if len(resp)<91:
            raise(responseError("short response"))
        if resp[1]!= 0x02:
            raise(responseError(STATUS.get(resp[1], f'unexpected status{resp[1]:#04x}')))
        return resp
    def battery(self):
        pct=self.transact(0x07,0x80,0x02)[10]*100//255
        try :
            charging=self.transact(0x07,0x84,0x02)[10]!=0
        except (responseError,OSError):
            charging=False
        return pct,charging
    def getDPI(self):
        dpi=self.transact(0x04,0x85,0x07,[0x01])
        return (dpi[10]<<8)|dpi[11]
    def setDPI(self,dpi):
        dpiH,dpiL=dpi>>8,dpi & 0xFF
        self.transact(0x04,0x05,0x07,[0x01,dpiH,dpiL,dpiH,dpiL,0,0])
    @property
    def available_rates(self):
        if self.hyperpoll:
            table,cap=HYPERPOLL_RATES,self.maxPoll
        else:
            table,cap=LEGACY_POLLING_RATES,min(self.maxPoll,1000)
        return sorted(rate for rate in table if rate<=cap)
    def getPOLL(self):
        attempts=[]
        if self.maxPoll>=2000:
            attempts.append((True,None,(0x00,0xC1,0x02),[0x01,0x00],10,HYPERPOLL_RATES_INV))
        for i,(get,_) in enumerate(LEGACY_COMMANDS):
            attempts.append((False,i,get,[],9,LEGACY_POLLING_RATES_INV))
        error=None
        for hyper,i,cmd,args,index,codes in attempts:
            try:
                pCode=self.transact(cmd[0],cmd[1],cmd[2],args)[index]
                if pCode not in codes:
                    raise responseError(f"unknown polling code {pCode:#04x}")
            except responseError as e:
                error=e
                continue
            self.hyperpoll=hyper
            if i is not None:
                self.legacyIndex=i
            return codes[pCode]
        raise error
    def setPOLL(self,poll):
        if poll not in self.available_rates:
            raise responseError(f"{poll} Hz is not available on this connection")
        if self.hyperpoll:
            self.transact(0x00, 0x41, 0x02, [0x01, HYPERPOLL_RATES[poll]])
            return
        error=None
        for i in sorted(range(len(LEGACY_COMMANDS)),key=lambda n: n!=self.legacyIndex):
            cmd=LEGACY_COMMANDS[i][1]
            try:
                self.transact(cmd[0],cmd[1],cmd[2],[LEGACY_POLLING_RATES[poll]])
            except responseError as e:
                error=e
                continue
            self.legacyIndex=i
            return
        raise error

def saveLog(lines):
    logPath = getDataDir() / LOG_NAME
    try:
        with open(logPath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n\n")
    except OSError:
        pass
def connect():
    log=[]
    infos=hid.enumerate(RAZER_VID,0)

    if not infos:
        return None, ["No Razer device found"]
    cPid,cIface,cTxn=CACHE.get("pid"),CACHE.get("iface"),CACHE.get("txn")
    def priority(i):
        if pidKey(i["product_id"])!=cPid:
            return 2
        return 0 if i["interface_number"]==cIface else 1
    infos.sort(key=priority)
    for info in infos:        
        pid, iface = info["product_id"], info["interface_number"]
        handle = hid.device()      
        try:
            handle.open_path(info["path"])
        except OSError as e: 
            log.append(f"pid {pid:#06x} iface {iface}: open failed ({e})")
            continue        
 
        razer = mouse(handle, TXNS[0], pid, iface, info.get("product_string") or "")
        txns = list(TXNS)
        if priority(info)==0 and cTxn in txns:
            txns.remove(cTxn)
            txns.insert(0,cTxn)
        for txn in txns:      
            razer.txn = txn   
            try:
                razer.lastDpi = razer.getDPI()
                try:
                    razer.lastPoll = razer.getPOLL()
                except responseError as e:
                    log.append(f"polling rate read failed: {e}")
                log.append(f"connected: {razer.name} pid {pid:#06x} iface {iface} txn {txn:#04x} dongle={razer.dongle} hyperpoll={razer.hyperpoll} maxPoll={razer.maxPoll}")
                if (pidKey(pid),iface,txn)!=(cPid,cIface,cTxn):
                    razer.save_mouse()
                return razer, log
            except (responseError, OSError, ValueError) as e: 
                log.append(f"pid {pid:#06x} iface {iface} txn {txn:#04x}: {e}")
        handle.close()             
    return None, log