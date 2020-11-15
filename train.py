#System Modules
import torch
from torch import optim, nn
import sys
import pdb
from tqdm import tqdm
import numpy as np
import datetime
from termcolor import colored

#Custom Modules
sys.path.append('utils');
sys.path.append('dataloaders');
sys.path.append('models');
sys.path.append('losses');
sys.path.append('visuals');

import opts_train
import Augmentation as ag
import Dataloader_misc as dlm
import Model_misc as mdm
import Loss_misc as lm
import Visual_misc as vm

#pdb.set_trace()
args = opts_train.parse_opts()
print (colored('\n'.join(sorted([str(i) + ' : ' + str(j) for (i,j) in vars(args).items()])),'white'))

# input augmentation
DAug = ag.Augmentation(args.aug, args.data_precision);
data_transforms = DAug.applyTransforms();
# target augmentation
TAug = ag.Augmentation(args.aug_target, args.data_precision);
target_transforms = TAug.applyTransforms();

# load dataloader
dsets, dset_loaders, dset_sizes, dset_classes = dlm.load_data_loader(args, args.db,\
 data_transforms, target_transforms)

#pdb.set_trace()
# load model
model = mdm.load(args, dset_classes)

# load visualizer
visualizer = vm.load(args, dset_loaders)

# load loss
criterion = lm.load(args)


if args.optimizer == "SGD":
    optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=0.9);
elif args.optimizer == "ADAM":
    optimizer = optim.Adam(model.parameters(), lr=args.lr,  eps=1e-8, weight_decay = 0)
else:
    print ("Correct optimizer not specified %s"%(args.optimizer))
    exit()

if args.start_from != None:
    optimizer.load_state_dict(torch.load(args.start_from)['optimizer'])
    print(colored('Pre-trained optimizer and amp loaded','white'))

# create learning rate scheduler
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, args.lr_decay_after, gamma = 0.1)

model_path = args.save + 'Exp-'+args.exp_id + '_'+datetime.datetime.now().strftime("%I_%M%p_%B_%d_%Y")+ '.model'
print(colored("Visual path: " + args.save_visuals + 'Exp: ' + args.exp_id + \
        ' Tasks: ' + args.id + ' -- ' +datetime.datetime.now().strftime("%I:%M%p %B %d, %Y"),'white'))

def train():
    n_iter = 0
    epoch_loss = np.Inf
    pbar_total = tqdm(range(args.num_epochs), position=0, leave=True, unit=' epochs')   
    for epoch in pbar_total:
        criterion.set_epoch_count(epoch) #Done to adjust loss weights based on epochs
        #pdb.set_trace()
        pbar_total.set_description('Epoch {}/{} || Val Loss: {:0.5f} || LR: {:.2E}'.format(epoch + 1, args.num_epochs, epoch_loss, scheduler.get_lr()[0]))
        for phase in ['train', 'test']:
            #pdb.set_trace()
        # for phase in ['train']:
            visualizer.init_running_results()
            #torch.cuda.empty_cache()
            model.set_training_mode(phase, epoch)
            if phase == 'test' and not epoch % args.val_after_every == 0:
                scheduler.step()
                continue

            pbar_epoch = tqdm(dset_loaders[phase], position=1, leave=False, unit=' batches')
            for count, data in enumerate(pbar_epoch):
                inputs, labels, ids = data;
                # pdb.set_trace()
                if len(inputs) == 1:
                    inputs = inputs[0].cuda()
                else:
                    #inputs[0] = inputs[0].cuda()
                    inputs[1].x = inputs[1].x.cuda();
                    inputs[1].edge_index = inputs[1].edge_index.long().cuda();
                    #inputs[1].edge_index_local = inputs[1].edge_index_local.long().cuda();
                    #inputs[1].edge_index_global = inputs[1].edge_index_global.long().cuda();
                    # inputs[1].edge_attr = inputs[1].edge_attr.cuda()
                    inputs[1].batch = inputs[1].batch.cuda()
                    inputs[1].pos = inputs[1].pos.cuda().float()

                if phase == 'train':
                    optimizer.zero_grad()
                    outputs = model(inputs, phase)
                    #torch.cuda.synchronize()
                    iter_results = criterion(outputs, labels, phase, epoch)
                    n_iter+=1
                    iter_results['loss'].backward()
                    optimizer.step()
                else:
                    with torch.no_grad():
                        outputs = model(inputs, phase)
                        #pdb.set_trace()
                        iter_results = criterion(outputs, labels, phase, epoch)
                visualizer.update_running_results(iter_results, phase)
            visualizer.compute_epoch_results(len(dset_loaders[phase]))
            visualizer.epoch_write(epoch, phase)

            if phase == 'test':
                epoch_loss = visualizer.get_val_loss()
                if visualizer.checkpoint():
                    if args.pilot == -1:
                        with open(model_path +'_best', 'wb') as f:
                            checkpoint = {
                                'model': model.state_dict(),
                                'optimizer': optimizer.state_dict()
                                #'amp': amp.state_dict()
                            }
                            torch.save(checkpoint, f);
                scheduler.step()
    return 1


train()

