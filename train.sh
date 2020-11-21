#!/bin/bash

#This is a default ID. No need to change
ID=AIAG

#This is the id of the particular run. Name as you wish
EXPERIMENT_ID=GAT_3_GATP

#Path to the CSV file containing AVA IDs
DB=meta/A2P2_FULL_Corrected.CSV

#Path to AVA images. Note, that images are not used here directly. Instead, this is used to check for missing files in the dataloader.
DATAPATH=/home/ghosalk/DATA/AVADataSet/

#Path to save the trained models
SAVE=/media/nas/02_Data/Aesthetics/MTL_BACKUP/models/MTL/

#Path to save tensorboard files
SAVE_VISUALS=/media/nas/02_Data/Aesthetics/MTL_BACKUP/visuals/runs_live/

#Path to load the feature graph from
FEATURE_PATH=/media/data2/ghosalk/Features/INC_RN_V2/INC_RN_V2_250K_AW_RSZ_5x_8CROP_HDF5_PyTorch_feats.h5

#Initial Learning Rate
LR=1e-4

#Batch size for training and validation
BATCH_SIZE=64
VAL_BATCH_SIZE=32

#Validate after every N epochs
VAL_AFTER=3

OPTIMIZER=ADAM

#Training data precision
FP=32

#Number of images to extract features from. Use -1 if all images are to be used. Use a smaller value for debugging.
PILOT=-1

#Number of workers to use in multiprocessing dataloader
WORKERS=4

# Backbone. Currently supports Inc-ResNet-v2 only. Adding new backbones is trivial.
# Note, backbone is not used here but this is to adjust GNN input parameters accordingly
BASE_MODEL=inceptionresnetv2

#Loss Weights. We tried both EMD and MSE loss. The default is MSE
W_MSE=1
W_EMD=0

#Number of output layers
A2_D=10

 CUDA_VISIBLE_DEVICES=0 python3 -W ignore train.py --id $ID --exp_id $EXPERIMENT_ID --db $DB --datapath $DATAPATH --save $SAVE --save_visuals $SAVE_VISUALS --feature_path $FEATURE_PATH \
  --base_model $BASE_MODEL  --A2_D $A2_D \
  --lr $LR --batch_size $BATCH_SIZE --batch_size_test $VAL_BATCH_SIZE --optimizer $OPTIMIZER --data_precision $FP --val_after_every $VAL_AFTER --n_workers $WORKERS \
  --w_emd $W_EMD --w_mse $W_MSE \
  --pilot $PILOT
#################################################################################################