import collections
import numpy as np
import os.path as osp

from chainercv.datasets.cub.cub_utils import CUBDatasetBase
from chainercv import utils


class CUBKeypointDataset(CUBDatasetBase):

    """`Caltech-UCSD Birds-200-2011`_ dataset  with annotated keypoints.

    .. _`Caltech-UCSD Birds-200-2011`:
        http://www.vision.caltech.edu/visipedia/CUB-200-2011.html

    An index corresponds to each image.

    When queried by an index, this dataset returns a corresponding
    :obj:`img, keypoint, kp_mask`, a tuple of an image, keypoints
    and a mask that indicates visible keypoints in the image. The data
    type of the three elements are :obj:`float32, float32, bool`.

    The keypoints are packed into a two dimensional array of shape
    :math:`(K, 2)`, where :math:`K` is the number of keypoints in the
    array. Note that :math:`K=15` in this dataset, and not all fifteen
    keypoints are visible in an image. When a keypoint is not visible,
    the values stored for that keypoint are undefined. The second axis
    corresponds to the :math:`x` and :math:`y` coordinates of the
    keypoints in the image.

    A keypoint mask array indicates whether a keypoint is visible in the
    image or not. This is a boolean array of shape :math:`(K,)`.

    Args:
        data_dir (string): Path to the root of the training data. If this is
            :obj:`auto`, this class will automatically download data for you
            under :obj:`$CHAINER_DATASET_ROOT/pfnet/chainercv/cub`.
        mode ({`train`, `test`}): Select train or test split used in
            [Kanazawa]_.
        crop_bbox (bool): If true, this class returns an image cropped
            by the bounding box of the bird inside it.

    .. [Kanazawa] Angjoo Kanazawa, David W. Jacobs, \
       Manmohan Chandraker. WarpNet: Weakly Supervised Matching for \
       Single-view Reconstruction. https://arxiv.org/abs/1604.05592.

    """

    def __init__(self, data_dir='auto', mode='train', crop_bbox=True):
        super(CUBKeypointDataset, self).__init__(
            data_dir=data_dir, crop_bbox=crop_bbox)

        # set mode
        test_images = np.load(
            osp.join(osp.split(osp.split(osp.abspath(__file__))[0])[0],
                     'data/cub_keypoint_dataset_test_image_ids.npy'))
        # the original one has ids starting from 1
        test_images = test_images - 1
        train_images = np.setdiff1d(np.arange(len(self.fns)), test_images)
        if mode == 'train':
            self.selected_ids = train_images
        elif mode == 'test':
            self.selected_ids = test_images
        else:
            raise ValueError('invalid mode')

        # load keypoint
        parts_loc_file = osp.join(self.data_dir, 'parts/part_locs.txt')
        self.kp_dict = collections.OrderedDict()
        self.kp_mask_dict = collections.OrderedDict()
        for loc in open(parts_loc_file):
            values = loc.split()
            id_ = int(values[0]) - 1

            if id_ not in self.kp_dict:
                self.kp_dict[id_] = []
            if id_ not in self.kp_mask_dict:
                self.kp_mask_dict[id_] = []

            keypoint = [float(v) for v in values[2:4]]
            kp_mask = bool(int(values[4]))

            self.kp_dict[id_].append(keypoint)
            self.kp_mask_dict[id_].append(kp_mask)

    def __len__(self):
        return len(self.selected_ids)

    def get_example(self, i):
        # this i is transformed to id for the entire dataset
        original_idx = self.selected_ids[i]
        img = utils.read_image_as_array(osp.join(
            self.data_dir, 'images', self.fns[original_idx]))  # RGB
        keypoint = np.array(self.kp_dict[original_idx], dtype=np.float32)
        kp_mask = np.array(self.kp_mask_dict[original_idx], dtype=np.bool)

        if self.crop_bbox:
            bbox = self.bboxes[original_idx]  # (x, y, width, height)
            img = img[bbox[1]: bbox[1] + bbox[3], bbox[0]: bbox[0] + bbox[2]]
            keypoint[:, :2] = keypoint[:, :2] - np.array([bbox[0], bbox[1]])

        if img.ndim == 2:
            img = utils.gray2rgb(img)

        img = img[:, :, ::-1]  # RGB to BGR
        img = img.transpose(2, 0, 1).astype(np.float32)
        return img, keypoint, kp_mask