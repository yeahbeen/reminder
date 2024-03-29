import os
import sys
import json
from log import log

class Config(object):
    config = {}
    log(sys.argv)
    workdir = os.path.dirname(os.path.abspath(sys.argv[0]))
    log("workdir2:"+workdir)
    configfile = workdir+"\\config.json"

    @classmethod
    def init(cls):
        if os.path.exists(Config.configfile):
            if os.path.getsize(Config.configfile) == 0: #崩溃，被清空了
                if os.path.exists(Config.configfile+".bak"):
                    log("use config.json.bak")
                    with open(Config.configfile+".bak") as f:
                        Config.config = json.loads(f.read())
            else:
                with open(Config.configfile) as f:
                    Config.config = json.loads(f.read())
        if len(Config.config) == 0:  #文件为空，初始化
            Config.config["short"] = {}
            Config.config["short"]["enable"] = True
            Config.config["short"]["itvHour"] = "1"
            Config.config["short"]["itvMin"] = "0"
            Config.config["short"]["itvSec"] = "0"
            Config.config["short"]["conHour"] = "0"
            Config.config["short"]["conMin"] = "1"
            Config.config["short"]["conSec"] = "0"
            Config.config["short"]["restset"] = {}
            Config.config["short"]["restset"]["ui"] = "pop"
            Config.config["short"]["restset"]["uipic"] = Config.workdir + "\\picture"
            Config.config["short"]["restset"]["beforesound"] = True
            Config.config["short"]["restset"]["beforesoundpath"] = Config.workdir + "\\sound\\gling.mp3"
            Config.config["short"]["restset"]["beforesoundvol"] = 50
            Config.config["short"]["restset"]["insound"] = True
            Config.config["short"]["restset"]["insoundpath"] = Config.workdir + "\\sound\\relax.mp3"
            Config.config["short"]["restset"]["insoundvol"] = 50
            Config.config["long"] = {}
            Config.config["long"]["enable"] = True
            Config.config["long"]["itvHour"] = "3"
            Config.config["long"]["itvMin"] = "0"
            Config.config["long"]["itvSec"] = "0"
            Config.config["long"]["itvCount"] = "3"
            Config.config["long"]["conHour"] = "0"
            Config.config["long"]["conMin"] = "5"
            Config.config["long"]["conSec"] = "0"
            Config.config["long"]["restset"] = {}
            Config.config["long"]["restset"]["ui"] = "roll"            
            Config.config["long"]["restset"]["uipic"] = Config.workdir + "\\picture"
            Config.config["long"]["restset"]["beforesound"] = True
            Config.config["long"]["restset"]["beforesoundpath"] = Config.workdir + "\\sound\\gong.mp3"
            Config.config["long"]["restset"]["beforesoundvol"] = 50
            Config.config["long"]["restset"]["insound"] = True
            Config.config["long"]["restset"]["insoundpath"] = Config.workdir + "\\sound\\relax.mp3"
            Config.config["long"]["restset"]["insoundvol"] = 50
            Config.config["set"] = {}
            Config.config["set"]["autorun"] = True
            Config.config["set"]["minimize"] = True
            Config.config["set"]["fullscreen"] = True
            Config.config["set"]["afterfullscreen"] = True
            Config.config["set"]["idle"] = True
            Config.config["set"]["afteridle"] = True
            Config.config["set"]["allowskip"] = True
            Config.config["set"]["fsshowtime"] = True
            Config.config["schedule"] = []
            Config.config["sendfile"] = {}
            Config.config["sendfile"]["outpath"] = Config.workdir + "\\ReceiveFiles"

    @classmethod
    def save(cls):
        with open(Config.configfile,"w") as f:
            # log("crash here?")
            # f.write(json.dumps(Config.config,indent=4))
            f.write(json.dumps(Config.config))
            # log("crash here2?")
        os.system(f'copy {Config.configfile} {Config.configfile}.bak')
        # log("crash here3?")