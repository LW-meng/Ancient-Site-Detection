from __future__ import print_function, division
import numpy as np
import torch
import torchvision
import torch.nn as nn
import torch.optim as optim
import argparse
from torchvision import transforms
from torchvision import datasets, models, transforms
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from tqdm import tqdm
from collections import Counter

from AncientSites import SitesDataset
from AncientModel_simple import SimpleModel
from AncientResModel import resnet152

def parse_args():
    parser = argparse.ArgumentParser(description='AncientSites Detection')
    parser.add_argument('--batch-size', type=int, default = 128,
                        help='input batch size for training (default: 128)')
    parser.add_argument('--num-epochs', type=int, default = 200,
                        help='Number of epochs to train each model for (default: 10)')
    parser.add_argument('--lr', type=float, default=0.0008,
                        help='learning rate (default: 0.01)')
    parser.add_argument('--root-dir', type = str, default = '',
                        help='root where train and test folders is on')

    parser.add_argument('--seed', type=int, default = 100,
                        help='Random seed (default: 123)')
    args = parser.parse_args()
    return args

def dev(model, dev_loader, device):
    model.eval()
    total_num = 0
    total_correct = 0
    with torch.no_grad():
        for _, batch in enumerate(dev_loader):

            dev_x = batch['Image']
            dev_y = torch.tensor(batch['label'], dtype=torch.long)

            dev_x = dev_x.to(device)
            dev_y = dev_y.to(device)
            output = model(dev_x)
            _, pred_y = output.data.max(1)
            total_correct += (dev_y == pred_y).sum().item()
            total_num += dev_x.size(0)

    return(total_correct / total_num)


def train(model, train_loader, dev_loader, loss_function, device, learning_rate):

    total_step_epoch = len(train_loader)
    optimizer = torch.optim.Adam(model.parameters(), lr = learning_rate)

    for epoch in tqdm(range(args.num_epochs)):

        model.train()

        for i, batch in enumerate(train_loader):
            data = batch['Image']
            labels = torch.tensor(batch['label'], dtype=torch.long)
            data = data.to(device)
            labels = labels.to(device)

            pred_labels = model(data)

            optimizer.zero_grad()
            loss = loss_function(pred_labels, labels)
            loss.backward()

            optimizer.step()

            if (i + 1) % 100 == 0:
                print('loss: at epoch', epoch, 'iter', i, loss.item())

        # decay learning rate
        if((epoch + 1) % 30) == 0:
            for param_group in optimizer.param_groups:
                param_group['lr'] /= 2

        torch.save(model.state_dict(), 'simple/ModelAt' + str(epoch) + 'Epoch.pt')


        accuracy = dev(model, dev_loader, device)
        print(f"Epoch: {epoch+1} | Loss: {loss.item()} | Test accuracy: {accuracy}")

def main():
    transform_data = transforms.Compose([
                transforms.ToTensor(),
                #transforms.Normalize((0.5), (0.5))
            ])

    datasets = SitesDataset('coordinates_train.txt', root_dir = args.root_dir, transform = transform_data)

    trainset, devset = torch.utils.data.random_split(datasets, [45000, 5220])

    train_loader = DataLoader(trainset, batch_size = args.batch_size, shuffle = True, num_workers = 5)
    dev_loader = DataLoader(devset, batch_size = args.batch_size, shuffle = True, num_workers = 5)

    device0 = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    train_classes = [i['label'].item() for i in trainset]
    falseCounter = Counter(train_classes)[0]
    trueCounter = Counter(train_classes)[1]
    ratio = round(falseCounter/trueCounter, 3)
    weights = torch.tensor([ratio, 1.], device = device0)

    loss_function = nn.CrossEntropyLoss(weights)

    
    # model_res = ResModel().to(device0)
    #model_res = SimpleModel().to(device0)
    model_completeRes = resnet152(pretrained = False, progress = False).to(device0)
    train(model = model_completeRes, train_loader = train_loader, dev_loader = dev_loader,
          loss_function = loss_function, device = device0, learning_rate = args.lr)

if __name__ == '__main__':
    args = parse_args()
    torch.manual_seed(args.seed)
    main()
