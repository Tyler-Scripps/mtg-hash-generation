import cv2
import requests
import json
import numpy as np
import time
from pathlib import Path
import os
import csv

def write2dDict(dict2d):
    print("Writing to files")
    print("--------------------------------------------------------------------------")
    for set in dict2d:
        fileName = set + ".csv"
        with open(os.path.join(fullDir, fileName), 'w') as f:
            f.write("id,hash\n")
            for id in dict2d[set]:
                line = id + "," + dict2d[set][id] + "\n"
                f.write(line)

fileName = input("Enter filename: ")
outDir = input("Enter output directory: ")

hashes = {}

#parse any existing files
fullDir = os.path.join(os.getcwd(), outDir)
for file in os.listdir(outDir):
    #if hashes doesn't have this file(set) then ass it
    if file.split(".")[1] == "csv": #only read csv files to allow for things like readme files
        currentSet = file.split(".")[0]
        if currentSet not in hashes:
            hashes[currentSet] = {}

        # print(file)
        with open(os.path.join(fullDir, file), 'r') as f:
            csvFile = csv.reader(f, delimiter=',')
            dataLine = False
            for line in csvFile:
                if dataLine:
                    # print(line)
                    hashes[currentSet][line[0]] = line[1]
                else:
                    dataLine = True

print("loaded data")
    # print(hashes)

#parse bulk file
with open(fileName) as f:
    print ("opened file")
    data = json.load(f)
    print("loaded json")
    i = 0
    hashesGenerated = 0
    for card in data:
        startTime = time.time()
        if card["set"] not in hashes:
            hashes[card["set"]] = {}
        if card["id"] not in hashes[card["set"]]:
            image_uri = ""
            if card["image_status"] != "missing":   #ensure that there is a uri for the card image
                if 'image_uris' in card:
                    image_uri = card['image_uris']['small']
                elif 'card_faces' in card and 'image_uris' in card['card_faces'][0]:
                    image_uri = card['card_faces'][0]['image_uris']['small']
                # print(card["id"])
                resp = requests.get(image_uri, stream=True).raw
                image = np.asarray(bytearray(resp.read()), dtype="uint8")
                image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
                image = cv2.resize(image, [9,8])
                hashedStr = ""
                for row in image:
                    # print(row)
                    for col in range(0, len(row) - 1):
                        if row[col] < row[col+1]:
                            hashedStr = hashedStr + "1"
                        else:
                            hashedStr = hashedStr + "0"
            
                hashes[card["set"]][card["id"]] = hashedStr
                hashesGenerated += 1
                print(hashedStr)
                endTime = time.time()
                deltaTime = endTime - startTime
                print("hashing took", "{:.4f}".format(deltaTime), "seconds")
                if deltaTime < 0.1:
                    time.sleep(0.1 - deltaTime)

        if hashesGenerated % 350 == 0 and hashesGenerated != 0:
            write2dDict(hashes)
        print(i)
        # print('\n')
        i += 1

    write2dDict(hashes) #once done looping do a final write to disk