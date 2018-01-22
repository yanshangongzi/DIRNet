import tensorflow as tf
from models import DIRNet
from config import get_config
from data import DIRNetDatahandler
import numpy as np
from ops import mkdir


def main():
    sess_config = tf.ConfigProto()
    sess_config.gpu_options.allow_growth = True
    sess = tf.Session(config=sess_config)
    config = get_config(is_train=True)
    mkdir(config.tmp_dir)
    mkdir(config.ckpt_dir)

    reg = DIRNet(sess, config, "DIRNet", is_train=True)
    # reg.restore(config.ckpt_dir)
    dh = DIRNetDatahandler( config=config)

    amnt_pics = np.shape(dh.d_data)[0]
    for epoch in range(3):
        loss_sum = 0
        acc = 0
        for i in range(amnt_pics):
            batch_x, batch_y, batch_labels = dh.get_pair_by_idx(i)
            # loss = reg.fit((1, batch_x[0], batch_x[1], batch_x[2]),
            #                (1, batch_y[0], batch_y[1], batch_y[2]))
            loss, prediction = reg.fit(batch_x, batch_y, batch_labels)
            loss_sum += loss
            if prediction == batch_labels:
                acc += 1
        print("iter {0}: Loss: {1:.4f} Acc: {2:.4f}".format(epoch, loss_sum / amnt_pics, acc / amnt_pics))

        if (epoch + 1) % 5 == 0:
        # if (epoch+1) % config.checkpoint_distance == 0:
        # reg.deploy(config.tmp_dir, batch_x, batch_y)
            reg.save(config.ckpt_dir)

    # for i in range(config.iteration):
    #     # create new random batch
    #     batch_x, batch_y, batch_labels = dh.sample_pair(config.batch_size)
    #
    #     # run sess => minimize loss
    #     loss = reg.fit(batch_x, batch_y,batch_labels)
    #
    #     print("iter {:>6d} : {}".format(i + 1, loss))
    #
    #     if (i + 1) % config.checkpoint_distance == 0:
    #         # reg.deploy(config.tmp_dir, batch_x, batch_y)
    #         reg.save(config.ckpt_dir)


if __name__ == "__main__":
    main()
