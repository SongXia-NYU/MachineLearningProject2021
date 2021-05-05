from openchem.data.graph_data_layer import GraphDataset
from openchem.utils.graph import Attribute
from openchem.utils.utils import identity


def get_atomic_attributes(atom):
    attr_dict = {}

    atomic_num = atom.GetAtomicNum()
    atomic_mapping = {5: 0, 7: 1, 6: 2, 8: 3, 9: 4, 15: 5, 16: 6, 17: 7, 35: 8,
                      53: 9}
    if atomic_num in atomic_mapping.keys():
        attr_dict['atom_element'] = atomic_mapping[atomic_num]
    else:
        attr_dict['atom_element'] = 10
    attr_dict['valence'] = atom.GetTotalValence()
    attr_dict['charge'] = atom.GetFormalCharge()
    attr_dict['hybridization'] = atom.GetHybridization().real
    attr_dict['aromatic'] = int(atom.GetIsAromatic())
    return attr_dict


node_attributes = {}
node_attributes['valence'] = Attribute('node', 'valence', one_hot=True, values=[1, 2, 3, 4, 5, 6])
node_attributes['charge'] = Attribute('node', 'charge', one_hot=True, values=[-1, 0, 1, 2, 3, 4])
node_attributes['hybridization'] = Attribute('node', 'hybridization',
                                             one_hot=True, values=[0, 1, 2, 3, 4, 5, 6, 7])
node_attributes['aromatic'] = Attribute('node', 'aromatic', one_hot=True,
                                        values=[0, 1])
node_attributes['atom_element'] = Attribute('node', 'atom_element',
                                            one_hot=True,
                                            values=list(range(11)))

from openchem.data.utils import read_smiles_property_file
import pandas as pd

data = pd.read_csv("../data/raw/esol.csv")
data_train = data[data["group"] == "train"]
# Here we use valid as test which is to fit openchem architecture
data_test = data[data["group"] == "valid"]
X_train, y_train = data_train["cano_smiles"].values, data_train["activity"].values.reshape(-1, 1)
X_test, y_test = data_test["cano_smiles"].values, data_test["activity"].values.reshape(-1, 1)

from openchem.data.utils import save_smiles_property_file

save_smiles_property_file('../data/processed/train.smi', X_train, y_train)
save_smiles_property_file('../data/processed/test.smi', X_test, y_test)

train_dataset = GraphDataset(get_atomic_attributes, node_attributes,
                             '../data/processed/train.smi',
                             delimiter=',', cols_to_read=[0, 1])
test_dataset = GraphDataset(get_atomic_attributes, node_attributes,
                            '../data/processed/test.smi',
                            delimiter=',', cols_to_read=[0, 1])


from openchem.models.Graph2Label import Graph2Label
from openchem.modules.encoders.gcn_encoder import GraphCNNEncoder
from openchem.modules.mlp.openchem_mlp import OpenChemMLP

from torch.optim import Adam
from torch.optim.lr_scheduler import StepLR
import torch.nn.functional as F
from sklearn.metrics import r2_score
import torch.nn as nn

model = Graph2Label

model_params = {
    'task': 'regression',
    'random_seed': 42,
    'use_clip_grad': False,
    'batch_size': 256,
    'num_epochs': 101,
    'logdir': 'logs/logp_gcnn_logs',
    'print_every': 10,
    'save_every': 5,
    'train_data_layer': train_dataset,
    'val_data_layer': test_dataset,
    'eval_metrics': r2_score,
    'criterion': nn.MSELoss(),
    'optimizer': Adam,
    'optimizer_params': {
        'lr': 0.0005,
    },
    'lr_scheduler': StepLR,
    'lr_scheduler_params': {
        'step_size': 15,
        'gamma': 0.8
    },
    'encoder': GraphCNNEncoder,
    'encoder_params': {
        'input_size': train_dataset[0]["node_feature_matrix"].shape[1],
        'encoder_dim': 128,
        'n_layers': 5,
        'hidden_size': [128]*5,
    },
    'mlp': OpenChemMLP,
    'mlp_params': {
        'input_size': 128,
        'n_layers': 2,
        'hidden_size': [128, 1],
        'activation': [F.relu, identity]
    }
}

print("hello")
