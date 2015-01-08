"""
Script to classify accelerometer data
"""

from common_imports import *


def classify_accl_thres(df):

    pred_label = []
    for idx in df.index:
        row = df.ix[idx]
        try:
            x = row['x_value']
            y = row['y_value']
            z = row['z_value']
            if (float(x) >= -2 and float(x) <= 1 and float(y) >= -2
                    and float(y) <= 1 and float(z) >= 8 and float(z) <= 10):
                pred_label.append("On Table")
            else:
                pred_label.append("On User")

        except Exception, e:
            logger.exception("ClassifyMotion:: %s", e)

    return pred_label
