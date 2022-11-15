import cv2
import requests
import json
import numpy as np
import time

fileName = input("Enter filename: ")
with open(fileName) as f:
    print ("opened file")
    data = json.load(f)
    print("loaded json")
    i = 0
    for card in data:
        image_uri = ""
        if 'image_uris' in card:
            image_uri = card['image_uris']['small']
        elif 'card_faces' in card and 'image_uris' in card['card_faces'][0]:
            image_uri = card['card_faces'][0]['image_uris']['small']
        
        time.sleep(0.1)
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
        
        if i < 3:
            # print(i)
        #     print(image)
        #     print(len(hashedStr))
            print(hashedStr)
        #     print("----------------------------")
        i += 1

