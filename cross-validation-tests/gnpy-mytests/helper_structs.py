
transceiver = {
      "uid": "",
      "metadata": {
        "location": {
          "region": "",
          "latitude": 0,
          "longitude": 0
        }
      },
      "type": "Transceiver"
    }

fibre_span = {
      "uid": "",
      "metadata": {
        "location": {
          "latitude": 1,
          "longitude": 1
        }
      },
      "type": "Fiber",
      "type_variety": "SSMF",
      "params": {
        "length": 0.0,
        "length_units": "km",
        "loss_coef": 0.22,
        "con_in": 0.00,
        "con_out": 0.00
      }
    }

edfa = {
    "uid": "",
    "type": "Edfa",
    "type_variety": "",
    "operational": {
        "gain_target": 0,
        "tilt_target": 0
    },
    "metadata": {
        "location": {
            "region": "",
            "latitude": 2,
            "longitude": 2
        }
    }
}

roadm = {
    "uid": "",
    "type": "Roadm",
    "params": {
        "target_pch_out_db": -17,
        "restrictions": {
          "preamp_variety_list": [],
          "booster_variety_list": []
        }
    },
    "metadata": {
        "location": {
            "region": "",
            "latitude": 3,
            "longitude": 3
             }
        }
}
