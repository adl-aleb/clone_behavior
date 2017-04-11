import csv
import numpy as np
import cv2
import os

import sklearn
from sklearn.utils import shuffle

lines =[]

#with open("data/driving_log.csv") as csvfile:
#    reader = csv.reader(csvfile)
#    for line in reader:
#        lines.append(line)

path = 'data_folders/'

os.chdir(path)

PATHS = ['data/driving_log.csv',
         'center_lane/driving_log.csv',
         'recovery_from_sides/driving_log.csv',
         'smooth_curves/driving_log.csv']
print(PATHS)

#         'curves/driving_log.csv' ]
# the first line is the column names.
for PATH in PATHS:
    with open(PATH) as csvfile:
        reader = csv.reader(csvfile)
        for line in reader:
            lines.append(line)
        
print("lines: ", len(lines))        
from sklearn.model_selection import train_test_split
train_samples, validation_samples = train_test_split(lines, test_size=0.2)
   

print("train samples: ", len(train_samples))

def generator(samples, batch_size=128):
    num_samples = len(samples)
    while 1: # Loop forever so the generator never terminates
        shuffle(samples)
        for offset in range(0, num_samples, batch_size):
            batch_samples = samples[offset:offset+batch_size]

            images = []
            angles = []
            for batch_sample in batch_samples:
                for i in range(3):
                    name = 'IMG/'+batch_sample[i].split('/')[-1]
                    image = cv2.imread(name)
                    images.append(image)
                    correction=0
                    if i==1:
                        correction=0.2
                    if i==2:
                        correction=-0.2
                    angle = float(batch_sample[3])+correction
                    angles.append(angle)
                    
                    images.append(np.fliplr(image)) 
                    angles.append(angle*-1.0)
            

            # trim image to only see section with road
            X_train = np.array(images)
            y_train = np.array(angles)
            yield sklearn.utils.shuffle(X_train, y_train)



            
# compile and train the model using the generator function
train_generator = generator(train_samples, batch_size=32)
validation_generator = generator(validation_samples, batch_size=32)


from keras.models import Sequential, Model
from keras.layers import Dense, Flatten, Lambda
from keras.layers.convolutional import Convolution2D
from keras.layers import MaxPooling2D
from keras.layers import Cropping2D
import matplotlib.pyplot as plt

epochs = 5

input_shape=(160,320,3)
print("setting model")
#based on NVIDIA Architecture
model = Sequential()
model.add(Lambda(lambda x: (x / 255.0) - 0.5, input_shape=input_shape))  #input_shape=(160,320,3)
model.add(Cropping2D(cropping=((70,25),(0,0))))#70rowTop,25B,L,R
model.add(Convolution2D(24,5,5,subsample=(2,2) ,activation='relu'))
model.add(Convolution2D(36,5,5,subsample=(2,2) ,activation='relu'))
model.add(Convolution2D(48,5,5,subsample=(2,2) ,activation='relu'))
model.add(Convolution2D(64,3,3,activation='relu'))
model.add(Convolution2D(64,3,3,activation='relu'))
model.add(Flatten())
model.add(Dense(100))
model.add(Dense(50))
model.add(Dense(10))
model.add(Dense(1))

print("compiling model")

model.compile(loss='mse', optimizer = 'adam')
print("fitting model")
model.fit_generator(train_generator, samples_per_epoch= len(train_samples), validation_data=validation_generator, nb_val_samples=len(validation_samples), nb_epoch=epochs)
print("save model")

model.save('model.h5')
exit()
