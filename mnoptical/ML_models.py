# The TensorFLow library is needed to use ML models. 
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import load_model
from tensorflow import math as TFmath


# Custom loss function
def customLoss(y_actual, y_pred):
    loaded_size = tf.dtypes.cast(TFmath.count_nonzero(y_actual), tf.float32)
    y_pred_cast_unloaded_to_zero = TFmath.divide_no_nan(TFmath.multiply(y_pred, y_actual), y_actual)
    error = TFmath.abs(TFmath.subtract(y_pred_cast_unloaded_to_zero, y_actual))
    custom_loss = TFmath.divide(TFmath.reduce_sum(error), loaded_size)
    return custom_loss


# Function for the prediction of WDG
def predictWDG(input_features, ML_model):
    if ML_model == 'ML_1':
        model_name = './saved_models/ML_Model_Booster_rd1_co1.h5'
    elif ML_model == 'ML_2':
        model_name = './saved_models/ML_Model_Preamp_rd2_co1.h5'
    elif ML_model == 'ML_3':
        model_name = './saved_models/ML_Model_LineAmp1.h5'

    # Load the model and use a custom loss function
    model = load_model(
        model_name,
        custom_objects={"customLoss": customLoss}
    )
    return model.predict(input_features)

