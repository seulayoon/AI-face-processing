# FR 1:N(Identification) Enrollment Code
import cv2
import numpy as np
import time
import os
import argparse

import utils.model_loading as model
import utils.face_cropping as crop
import utils.face_recognition as recognition
import utils.face_draw as draw

# Argparser Setting
parser = argparse.ArgumentParser()
parser.add_argument("-n", "--path", type=str, help="folder path name", default="IJB-A")
args = vars(parser.parse_args())
print(args["path"])

class face_info():
    def __init__(self):
        self.subject_id_list = []
        self.image_list = []
        self.face_image_list = []
        self.emb_list = []

input_folder = args["path"]
scale_percent = 0.4 # the ratio to resize a image

# Save crop image to check
if not os.path.exists('detection_result'):
    os.makedirs('detection_result')

for split_num in range(1, 11):
    
    # Numpy file loading setting
    face = face_info()
    dir_path = os.path.dirname(os.path.abspath(__file__))
    filename_npy = os.path.join(dir_path,'enroll_split{}.npz'.format(split_num))
    npy_file_load = os.path.isfile(filename_npy)
    face = model.npy_loading(face, filename_npy, npy_file_load)

    subject_id_list = []
    file_list = []
    gt_bbox_list = []
    
    with open(input_folder + "/IJB-A_1N_sets/split{}/search_gallery_{}.csv".format(split_num, split_num), 'r') as f:
        header = f.readline()
        while True:
            line = f.readline()
            if not line:
                break
            line = line.rstrip()

            subject_id = int(line.split(',')[1]) # SUBJECT_ID
            subject_id_list.append(subject_id)

            file = line.split(',')[2] # FILE
            file_list.append(file)

            face_x = float(line.split(',')[6]) # FACE_X
            face_y = float(line.split(',')[7]) # FACE_Y
            face_width = float(line.split(',')[8]) # FACE_WIDTH
            face_height = float(line.split(',')[9]) # FACE_HEIGHT
            gt_bbox = np.array([face_x, face_y, face_x + face_width, face_y + face_height])
            gt_bbox_list.append(gt_bbox)

    N_file = len(file_list)
    emb_list = np.zeros((N_file, 512))

    # Model Loading
    detect_model = model.detect_loading(0)
    recognition_model = model.recognition_loading(0)

    for idx, file in enumerate(file_list):
        
        folder_name = file.split('/')[0]
        file_name = file.split('/')[1]
        
        # ABOUT EMBEDDING LAYER
        image = cv2.imread('{}/images/{}'.format(input_folder, file))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        print("idx:", idx)
        print("file:", file)
        print("image.shape:",image.shape)
        image = cv2.resize(image, (int(image.shape[1]*scale_percent), int(image.shape[0]*scale_percent)))
        bbox, landmark = detect_model.detect(image, threshold=0.5, scale=1.0)
        face_img, bbox, landmark = crop.ver0(image, bbox, landmark, gt_bbox_list[idx]*scale_percent)
        face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
        cv2.imshow('detection_result', face_img)
        cv2.waitKey(1)
        if not os.path.exists('detection_result/split{}'.format(split_num)):
            os.makedirs('detection_result/split{}'.format(split_num))
        cv2.imwrite('detection_result/split{}/{}_{}_{}_{}.jpg'.format(split_num, idx, folder_name, file_name, subject_id_list[idx]), face_img)
        emb = recognition_model.get_embedding(face_img)
        emb_list[idx]= emb
        
    if len(face.subject_id_list) == 0 :
        face.subject_id_list = subject_id_list
        face.emb_list = emb_list
    else:
        face.subject_id_list = face.subject_id_list + subject_id_list
        face.emb_list = np.vstack([face.emb_list, emb_list])

    # Result Arrangement
    np.savez(filename_npy, x=face.subject_id_list, y=face.emb_list)
    subject_id_list = list(set(subject_id_list))
    subject_id_list.sort()
    for subject_id in subject_id_list:
        print(subject_id)
    print('Enrolled {} people'.format(len(subject_id_list)))
    print('Enrolled split {}'.format(split_num))
    
print('Enrolled all splits')