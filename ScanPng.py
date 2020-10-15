import json
import os
import sys
import PIL
from PIL import Image
import tinify
import hashlib

inputPath = input("Enter your project path: (Press enter directly to use default path)")
if inputPath == "":
    path = "/Users/xiaoyao/Desktop/Code"
else:
    path = inputPath

tinifyNow = input("You want tinify now? : (yes/no)")

if tinifyNow == "yes":
    inputTinifyKey = input("Enter your tinify key : (Press enter directly to use default key)")
    if inputTinifyKey.lstrip() == "":
        tinify.key = "zjh6DdCLfPkmc5pLj3wQpN0vTVg6XNwD"
    else:
        tinify.key = inputTinifyKey

print("Scanning...")

# 判断图片是否需要压缩
def imageShouldCompress(image):
    format = image.format
    if format != 'PNG':
        return False

    mode = image.mode
    if mode == 'P':#压缩过
        return False
    elif mode == 'RGBA':#没压缩过
        return True
    else:#其他模式，不压缩
        return False

# 执行压缩，返回是否需要停止
def runTiny(imagePath):
    try:
        source = tinify.from_file(imagePath)
    except tinify.errors.ClientError:
        print("Image could not be decoded. (HTTP 400/Decode error) " + imagePath)
    except tinify.errors.AccountError:
        print("Your monthly limit has been exceeded. (HTTP 429/TooManyRequests)     免费压缩次数已耗尽，换个tinify key试试")
        return True
    except tinify.errors.ConnectionError:
        print("网络错误")
    except ConnectionResetError:
        print("连接被关闭")
    except tinify.ClientError:
        print("Check your source image and request options.")
    except tinify.ServerError:
        print("Temporary issue with the Tinify API.")
    except tinify.ConnectionError:
        print("A network connection error occurred.")
    except Exception:
        print("Something wrong.")
    else:
        try:
            source.to_file(imagePath)
        except tinify.errors.AccountError:
            print("Your monthly limit has been exceeded. (HTTP 429/TooManyRequests)     免费压缩次数已耗尽，换个tinify key试试")
            return True
        except Exception:
            print("Something wrong.")
        else:
            print('tinify done:'+imagePath)

    return False

# 获取文件MD5
def getMd5(file):
    m = hashlib.md5()
    with open(file,'rb') as f:
        for line in f:
            m.update(line)
    md5code = m.hexdigest()
    return md5code

# 读取白名单
whiteListPath = sys.path[0] + ("/WhiteList.txt")
try:
    f = open(whiteListPath, "r")
except FileNotFoundError:
    print("White list file not found.")
    unUsedPngWhiteList = {}
    repeatWhiteList = {}
    tinifyWhiteList = {}
else:
    jsonStr = f.read()
    f.close()
    whiteListDict = json.loads(jsonStr)
    unUsedPngWhiteList = whiteListDict["UnUsedPngWhiteList"]
    repeatWhiteList = whiteListDict["RepeatWhiteList"]
    tinifyWhiteList = whiteListDict["TinifyWhiteList"]

totalCountNotInBundle = 0
totalCount = 0
pngDict = {}
# 遍历所有png图片，存入字典
for root, dirs, files in os.walk(path, False):
    for file in files:
        if file.endswith(".png"):
            totalCount += 1
            if ".bundle" in root:
                continue
            if "@2x.png" in file:
                imgName = file.replace("@2x.png", "")
            elif "@3x.png" in file:
                imgName = file.replace("@3x.png", "")
            elif ".png" in file:
                imgName = file.replace(".png", "")
            totalCountNotInBundle += 1
            if imgName in unUsedPngWhiteList:
                continue
            pngDict[imgName] = file

pngRefersDict = pngDict.copy()
codeFileCount = 0
# 遍历代码文件内容，找到未使用的png
for root, dirs, files in os.walk(path, False):
    for file in files:
        if (file.endswith(".m") or file.endswith(".mm") or file.endswith(".js")) or file.endswith(".xib") or file.endswith(".storyboard"):
            codeFileCount += 1
            filePath = root + "/" + file
            f = open(filePath, 'r')
            content = f.read()
            f.close()
            for imgName,imgFullName in pngDict.items():
                if "\"" + imgName + "\"" in content:
                    if imgName in pngRefersDict.keys():
                        pngRefersDict.pop(imgName)


md5Dict = {}
repeatPNGDict = {}

tinifyCount = 0
unTinyCount = 0
shouldBreak = False
# 找出重复图片、批量压缩
for root, dirs, files in os.walk(path, False):
    if shouldBreak:
        break
    for file in files:
        if file.endswith(".png"):
            imagePath = root + "/" + file

            try:
                image = Image.open(imagePath)
            except PIL.UnidentifiedImageError:
                print("图片已损坏 : " + imagePath)
            else:
                md5Str = getMd5(imagePath)
                if file not in repeatWhiteList:
                    if md5Str in md5Dict.keys():
                        repeatPNGDict[md5Dict[md5Str]] = file
                    else:
                        md5Dict[md5Str] = file;
                if file not in tinifyWhiteList:
                    if imageShouldCompress(image):
                        unTinyCount += 1
                        if tinifyNow == "yes":
                            tinifyCount += 1
                            shouldBreak = runTiny(imagePath)



print("\n\n")
print("------------------------------------------------------ Report ------------------------------------------------------")
if shouldBreak:
    print("TinyPng 500 free times run out, please try another key");
print("PNG total count : " + str(totalCount))
print("PNG total count（except in .bundle） : " + str(totalCountNotInBundle))
print("Untiny count : " + str(unTinyCount))
print("Total tinify this time : " + str(tinifyCount))
print("Scan code file count : " + str(codeFileCount))
print("Unused PNG count : " + str(len(pngRefersDict)))
print("\n");
print("Repeat PNG : ")
for key,value in repeatPNGDict.items():
    print(key + " == " + value)
print("\n");
print("Unused PNG list : ")
for key,value in pngRefersDict.items():
    print(key)
print("====================================================== Report ======================================================")

# 写入到txt
f = open(path + "/ScanPngReport.txt", 'w')
if shouldBreak:
    f.write("TinyPng 500 free times run out, please try another key\n");
f.write("PNG total count : " + str(totalCount) + "\n")
f.write("PNG total count（except in .bundle） : " + str(totalCountNotInBundle) + "\n")
f.write("Total tinify this time : " + str(tinifyCount) + "\n")
f.write("Scan code file count : " + str(codeFileCount) + "\n")
f.write("Unused PNG count : " + str(len(pngRefersDict)) + "\n")
f.write("\n\n");
f.write("Repeat PNG : " + "\n")
for key,value in repeatPNGDict.items():
    f.write(key + " == " + value + "\n")
f.write("\n\n");
f.write("Unused PNG list : " + "\n")
for key,value in pngRefersDict.items():
    f.write(key + "\n")
f.close()
print("ScanPngReport were writen on " + path + "/ScanPngReport.txt")