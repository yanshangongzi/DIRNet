import numpy as np
import gzip
from pathlib import Path
#import imageio
import scipy.ndimage as ndimage
from skimage.transform import resize
from skimage import color
import scipy.misc
from config import get_config
import random
import h5py
import random


class DIRNetDatahandler(object):

    '''
    reads the data
    :param config: config object
    '''
    def __init__(self, config):
        self.s_data = []
        self.d_data = []
        self.config = config
        self.labels = []
        # read data from folder
        if not config.use_saved_data:
            print("getting data")
            self.s_data, s_data_names = self.get_data(self.config.s_dir)
            self.d_data, d_data_names = self.get_data(self.config.d_dir)
            label_names, labels_raw = self.load_labels(self.config.label_path)
            index = 0

            # delete files that are only contained in one of the folders
            to_be_deleted = []
            for i in s_data_names:
                if i in d_data_names and i in label_names:
                    index += 1

                    self.labels.append(int(labels_raw[label_names.index(i)]))
                else:
                    to_be_deleted.append(index)
                    index += 1
            self.s_data = np.delete(self.s_data, to_be_deleted, 0)
            self.labels = np.asarray(self.labels)

            # delete files that are only contained in one of the folders
            to_be_deleted = []
            index = 0
            for i in d_data_names:
                if i in s_data_names:
                    index += 1
                else:
                    to_be_deleted.append(index)
                    index += 1
            self.d_data = np.delete(self.d_data, to_be_deleted, 0)

            # create evaluation datasets
            # eval_idx = np.random.choice(len(self.d_data) - 1,
            #                             int(np.round(config.eval_split_fraction * len(self.d_data))))
            # train_idx = [x for x in range(len(self.d_data) - 1) if x not in eval_idx]

            # There are 20 patients for each of the 5 disease classes
            # we want to get so many patients for eval from each class
            amnt_pat_for_eval = int(np.round(config.eval_split_fraction * 20))
            eval_patients_ids = np.empty((5, amnt_pat_for_eval)) # stores the indices for the evaluation date for each disease
            # eval_idx = np.empty(config.eval_split_fraction * len(self.d_data))
            # train_idx = np.empty((1-config.eval_split_fraction) * len(self.d_data))
            eval_idx = []
            train_idx = []
            for i in range(5):
                eval_patients_ids[i] =random.sample(range(1,20), amnt_pat_for_eval)
                # print(eval_patients_ids[i])
            for i in range(len(self.s_data)-1):
                # label_names, labels_raw
                image_name = label_names[i]
                num = image_name.split("_")[0][-3:]
                pat_id = num.lstrip("0")
                pat_label = int(labels_raw[i])
                # if this patient
                if (int(pat_id)%20)+1 in eval_patients_ids[pat_label]:
                    eval_idx.append(i)
                else:
                    train_idx.append(i)
            print('eval pairs size ' + str(len(eval_idx)))
            print('train pairs size ' + str(len(train_idx)))
            s_train = self.s_data[train_idx]
            s_eval = self.s_data[eval_idx]
            d_train = self.d_data[train_idx]
            d_eval = self.d_data[eval_idx]
            labels_train = self.labels[train_idx]
            labels_eval = self.labels[eval_idx]

            a = [0, 0, 0, 0, 0]
            for i in labels_eval:
                a[int(i)] += 1
            print('distribution of labels in eval set:')
            print(a)
            b = [0, 0, 0, 0, 0]
            for i in labels_train:
                b[int(i)] += 1
            print('distribution of labels in train set:')
            print(b)
            self.s_data = s_train
            self.d_data = d_train
            self.labels = labels_train

            self.s_data_eval = s_eval
            self.d_data_eval = d_eval
            self.labels_eval = labels_eval

            # save numpy arrays as .h5 if config.save is true
            if self.config.save:
                with h5py.File('{}.h5'.format(self.config.s_data_filename), 'w') as hf:
                    hf.create_dataset(self.config.s_data_filename, data=self.s_data)
                with h5py.File('{}.h5'.format(self.config.d_data_filename), 'w') as hf:
                    hf.create_dataset(self.config.d_data_filename, data=self.d_data)
                with h5py.File('{}.h5'.format(self.config.label_filename), 'w') as hf:
                    hf.create_dataset(self.config.label_filename, data=self.labels)

                with h5py.File('{}.h5'.format(self.config.s_data_eval_filename), 'w') as hf:
                    hf.create_dataset(self.config.s_data_eval_filename, data=self.s_data_eval)
                with h5py.File('{}.h5'.format(self.config.d_data_eval_filename), 'w') as hf:
                    hf.create_dataset(self.config.d_data_eval_filename, data=self.d_data_eval)
                with h5py.File('{}.h5'.format(self.config.label_eval_filename), 'w') as hf:
                    hf.create_dataset(self.config.label_eval_filename, data=self.labels_eval)
        else:

            # load numpy arrays from .h5 files
            def h5py_dataset_iterator(g, prefix=''):
                for key in g.keys():
                    item = g[key]
                    path = '{}/{}'.format(prefix, key)
                    if isinstance(item, h5py.Dataset):  # test for dataset
                        yield (path, item)
                    elif isinstance(item, h5py.Group):  # test for group (go down)
                        yield from h5py_dataset_iterator(item, path)

            # load s_data
            with h5py.File(self.config.s_data_filename + '.h5', 'r') as hf:
                for (path, dset) in h5py_dataset_iterator(hf):
                    self.s_data = hf[dset.name][:]

            # load d_data
            with h5py.File(self.config.d_data_filename + '.h5', 'r') as hf:
                for (path, dset) in h5py_dataset_iterator(hf):
                    self.d_data = hf[dset.name][:]

            with h5py.File(self.config.label_filename + '.h5', 'r') as hf:
                for (path, dset) in h5py_dataset_iterator(hf):
                    self.labels = hf[dset.name][:]

            # load s_data
            with h5py.File(self.config.s_data_eval_filename + '.h5', 'r') as hf:
                for (path, dset) in h5py_dataset_iterator(hf):
                    self.s_data_eval = hf[dset.name][:]

            # load d_data
            with h5py.File(self.config.d_data_eval_filename + '.h5', 'r') as hf:
                for (path, dset) in h5py_dataset_iterator(hf):
                    self.d_data_eval = hf[dset.name][:]

            with h5py.File(self.config.label_eval_filename + '.h5', 'r') as hf:
                for (path, dset) in h5py_dataset_iterator(hf):
                    self.labels_eval = hf[dset.name][:]


    def load_labels(self, path):
        """

        :param path: path to label file
        :type path: string
        :return: pathnames and labels
        :rtype: list,list
        """
        pathnames = []
        labels = []

        with open(path) as label_f:
            label_data = label_f.readlines()
            for line in label_data:
                if line is not "":
                    line = line.split(',')
                    slice_number = line[0].split('.')
                    slice_number = slice_number[len(slice_number) - 2]
                    # print((line[0].split(".")[0].split('_')[0]) + "_" + slice_number)
                    pathnames.append((line[0].split(".")[0].split('_')[0]) + "_" + slice_number)
                    labels.append(line[1])
            return pathnames, labels

    def extract_patientnumber(self, filepath):
        '''
        extract patient number from  filename
        :param filepath: path to file
        return: patientnumber
        '''
        if self.config.os_is_windows:
            image_name = str(filepath).split("\\")
        else:
            image_name = str(filepath).split("/")
        image_name = image_name[len(image_name) - 1]
        num = image_name.split("_")[0][-3:]
        return num.lstrip("0")

    def get_data(self, path):
        '''
        load images from path into numpy array
        :param path: path to folder
        return: numpy array with images and list with pathnames (images,pathnames)
        '''

        pathlist = Path(path).glob('**/*.png')
        imagelist = []
        pathnames = []
        if self.config.os_is_windows:
            splitchar = '\\'
        else:
            splitchar = '/'
        for image_path in pathlist:
            print(image_path)
            # maybe interesting at some  point
            slice_number = str(image_path).split(".")
            slice_number = slice_number[len(slice_number) - 2]
            if str(image_path).split(".")[len(slice_number) - 5].split(splitchar)[-1].split('_')[0].startswith("nz"):
                # print(str(image_path).split(".")[len(slice_number) - 6].split(splitchar)[-1].split('_')[
                #           0] + "_" + slice_number)
                pathnames.append(
                    str(image_path).split(".")[len(slice_number) - 6].split(splitchar)[-1].split('_')[
                        0] + "_" + slice_number)
            else:
                # print(str(image_path).split(".")[len(slice_number) - 5].split(splitchar)[-1].split('_')[
                #           0] + "_" + slice_number)
                pathnames.append(
                    str(image_path).split(".")[len(slice_number) - 5].split(splitchar)[-1].split('_')[
                        0] + "_" + slice_number)
            num = str(image_path).split(".")[2]

            # load images from file; rgb-> grayscale; resize to size defined in config.im_size
            # res_im = resize(color.rgb2gray(imageio.imread(str(image_path))), self.config.im_size, mode='constant')
            res_im = ndimage.imread(str(image_path), flatten=True)
            imagelist.append(res_im)

        # list to numpy array
        imagelist = np.asarray(imagelist)

        # create colorchannel for grayscaled images
        # not needed if rgb is used -> comment this  line out
        imagelist = np.expand_dims(imagelist, axis=4)

        return imagelist, pathnames

    def sample_pair(self, batch_size):
        '''
        sample random pairs of moving and fixed images
        :param batch_size: number of moving/fixed images to be retrieved
        return: numpy arrays x and y with shape [batch_size, height, width,color_channels] and numpy array with all labels
        '''
        choice = np.random.choice(len(self.d_data) - 1, batch_size)

        x = self.s_data[choice]
        y = self.d_data[choice]
        labels = self.labels[choice]

        return x, y, labels


    def get_pair_by_idx(self, idx, batch_size=1):
        '''
        sample a batch of pairs of moving and fixed images and label, starting by the pair at the index.
        If index+batch_size is not a valid index, the missing ones are sampled starting at index 0
        :param batch_size: number of moving/fixed images images to be retrieved
        :param idx: index in the data from where the samples should be retrived.
        return: numpy arrays x and y with shape [batch_size, height, width,color_channels] and numpy array with all labels
        '''
        x = self.s_data[np.expand_dims(idx, 0)]
        y = self.d_data[np.expand_dims(idx, 0)]
        labels = self.labels[np.expand_dims(idx, 0)]
        # :TODO: adjust for batchsize other than 1
        return x, y, labels


    def get_eval_pair_by_idx(self, idx, batch_size=1):
        '''
        sample a batch of pairs of moving and fixed images and label, starting by the pair at the index.
        If index+batch_size is not a valid index, the missing ones are sampled starting at index 0
        :param batch_size: number of moving/fixed images images to be retrieved
        :param idx: index in the data from where the samples should be retrived.
        return: numpy arrays x and y with shape [batch_size, height, width,color_channels] and numpy array with all labels
        '''
        x = self.s_data_eval[np.expand_dims(idx, 0)]
        y = self.d_data_eval[np.expand_dims(idx, 0)]
        labels = self.labels_eval[np.expand_dims(idx, 0)]
        # :TODO: adjust for batchsize other than 1
        return x, y, labels