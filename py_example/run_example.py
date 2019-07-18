import os
import subprocess
import argparse
import numpy as np
from sklearn.metrics import recall_score, precision_score, accuracy_score
import torch
from torch.utils.data import DataLoader

from data_processing.PathMinerLoader import PathMinerLoader
from data_processing.PathMinerDataset import PathMinerDataset
from model.ProjectClassifier import ProjectClassifier


# Example shows how to pass data generated by PathMiner to PyTorch Dataset for further convenient usage and build a
# classifier to solve a toy problem of distinguishing files between 2 projects.


# If projects aren't loaded or processed yet then do it.
def load_projects():
    necessary_files = ['node_types.csv', 'paths.csv', 'tokens.csv', 'path_contexts.csv']
    if not any(fname in os.listdir('processed_data/') for fname in necessary_files):
        print("Some of the files are missing. Downloading projects and processing them")
        subprocess.call('./prepare_data.sh')


# Add labels with project info to path contexts.
def label_contexts(path_contexts):
    path_contexts['project'] = path_contexts['id'].map(lambda filename: 0 if 'project1' in filename else 1)


# Create training and validation dataset from path contexts.
def split2datasets(loader, test_size=0.5, keep_contexts=200):
    index = np.random.permutation(loader.path_contexts.index)
    n_test = int(test_size * len(loader.path_contexts))
    test_indices = index[:n_test]
    train_indices = index[n_test:]
    return PathMinerDataset(loader, train_indices, keep_contexts), PathMinerDataset(loader, test_indices, keep_contexts)


# Train a model, print training summary and results on test dataset after every epoch.
def train(train_loader, test_loader, model, optimizer, loss_function, n_epochs=3, log_batches=5):
    print("Start training")
    for epoch in range(n_epochs):
        print("Epoch #{}".format(epoch + 1))
        current_loss = 0
        for n_batch, sample in enumerate(train_loader):
            contexts, labels = sample['contexts'], sample['labels']
            optimizer.zero_grad()

            predictions = model(contexts)
            #predictions.cuda()
            loss = loss_function(predictions, labels.cuda())
            #loss.cuda()
            loss.backward()
            optimizer.step()

            current_loss += loss.item()
            if (n_batch + 1) % log_batches == 0:
                print("After {} batches: average loss {}".format(n_batch + 1, current_loss / log_batches))
                current_loss = 0

        with torch.no_grad():
            total = len(test_loader.dataset)
            predictions = np.zeros(total)
            targets = np.zeros(total)
            cur = 0
            for sample in test_loader:
                contexts, labels = sample['contexts'], sample['labels']
                batched_predictions = model(contexts)
                #batched_predictions.cuda()
                # binarize the prediction
                batched_predictions = (batched_predictions > 0.5).cpu().numpy()
                batched_targets = (labels > 0.5).numpy()
                predictions[cur:cur + len(batched_predictions)] = batched_predictions
                targets[cur:cur + len(batched_targets)] = batched_targets
                cur += len(batched_predictions)
            print("accuracy: {:.3f}, precision: {:.3f}, recall: {:.3f}".format(
                accuracy_score(targets, predictions),
                precision_score(targets, predictions),
                recall_score(targets, predictions)
            ))
    print("Training completed")


def main(args):
    print("Checking GPU status")
    print(torch.cuda.is_available, torch.cuda.device_count(), torch.cuda.get_device_name(0), torch.cuda.current_device())
    print("Checking if projects are loaded and processed")
    load_projects()
    print("Loading generated data")
    loader = PathMinerLoader.from_folder(args.source_folder)
    print("Labeling contexts")
    label_contexts(loader.path_contexts)
    print("Creating datasets")
    train_dataset, test_dataset = split2datasets(loader, keep_contexts=500)
    train_loader = DataLoader(train_dataset, args.batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, args.batch_size)

    model = ProjectClassifier(len(loader.tokens) + 1, len(loader.paths) + 1, 8)
    optimizer = torch.optim.Adam(model.parameters())
    loss_function = torch.nn.BCELoss()

    model.cuda()
    #model = torch.nn.DataParallel(model)
    #loss_function.cuda()

    train(train_loader, test_loader, model, optimizer, loss_function, n_epochs=10, log_batches=20)


if __name__ == '__main__':
    np.random.seed(42)

    parser = argparse.ArgumentParser()
    parser.add_argument('--source_folder', type=str, default='processed_data/',
                        help='Folder containing output of PathMiner')
    parser.add_argument('--batch_size', type=int, default=8, help='Batch size for training')

    args = parser.parse_args()
    main(args)
