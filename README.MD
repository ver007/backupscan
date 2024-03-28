### backupScan 是一个专门用于备份文件及敏感文件扫描工具

---

#### main.py 为主启动扫描文件

```

[scanBackup] $ python main.py
usage: main.py [-h] [-t TARGET] [-d DELAY] [-thread THREAD] [-timeout TIMEOUT]
               [-version]

optional arguments:
  -h, --help        show this help message and exit
  -t TARGET         target: "/target.txt,192.168.1.1,www.site.com"
  -d DELAY          speed
  -thread THREAD    scan thread num
  -timeout TIMEOUT  http timeout
  -version          show program's version number and exit

```