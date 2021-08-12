import sys, os, time, pprint, window
from Utility import *
import pandas as pds
import concurrent.futures as futures

CAPTURE_DIR="./Captures/"
OUT_DIR = "./windowParsed/"
PRETTY_PRINTER=pprint.PrettyPrinter(indent=4)

def get_captures(capDir):
    toRet=[]
    match=COLORS.GREEN
    miss=COLORS.RED

    if(not os.path.isdir(capDir)):
        raise Exception("Argument %s is not a valid directory..."%capDir)
    for f in os.listdir(capDir):
        fType=COLORS.WHITE

        if((not f.startswith("IGN_")) and f.endswith(".pcap")):
            toRet.append(f)
            fType=match
        else:
            fType=miss

        debug(f,fType)
    return toRet

def get_devies(files):
    #devicePrefixes is a set (no duplicates) which contains the prefixes for each device.
    devicePrefixes=sorted(list({"Awox","AmazonDot","AmazonEcho","AmazonShow","DLink","TPLink","Musaic","IView","IDevice","SmartThingsHub","Omna","Wemo"}))
    
    #devices is a dict such that: key=*device_name*:value=*[files]*
    devices = {deviceName:[] for deviceName in devicePrefixes}

    for f in files:
        pref = starts_with_any(f, devicePrefixes)

        if(pref):
            devices[pref].append(f)
        else:
            debug(splits,COLORS.RED)
            
    PRETTY_PRINTER.pprint(devices)
    return devices

def get_device_df(deviceName, deviceID, deviceFiles):
    filesTrue = [os.path.normpath(CAPTURE_DIR + "/" + f) for f in deviceFiles]
    # print(filesTrue)
    # print("%i: %s: %s" % (i, deviceName, filesTrue))
    resDF = window.from_many(filesTrue)

    resDF["Device"] = [deviceName] * len(resDF)
    resDF.index = [deviceID] * len(resDF)

    return resDF

def conglomerate_data(deviceDict):
    congDF = pds.DataFrame()

    for i, dictItem in enumerate(deviceDict.items()):
        deviceName, files = dictItem

        dfIn = get_device_df(deviceName, i, files)

        congDF = congDF.append(dfIn)
    return congDF
        
#this code will be multithreaded to increase performance.
def conglomerate_data_fast(deviceDict):
    dfArr = []
    with futures.ProcessPoolExecutor(max_workers=10) as executer:

        running = [executer.submit(get_device_df, name, i, files ) for i, (name, files) in enumerate(deviceDict.items())]

        for res in futures.as_completed(running):
            dfArr.append(res.result())
    print(len(dfArr))
    congDF = pds.DataFrame().append(dfArr).sort_index()
    return congDF


def main(capDir):
    debug(capDir, COLORS.BLUE)
    caps = get_captures(capDir)
    devices = get_devies(caps)

    csvCong = conglomerate_data_fast(devices)
    csvCong.to_csv(os.path.normpath(OUT_DIR+"/"+"Conglomerate.csv"))

if __name__ == "__main__":
    if(len(sys.argv)==2):
        CAPTURE_DIR = sys.argv[1]
        
    main(CAPTURE_DIR)
