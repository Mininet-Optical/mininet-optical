## emulator driver

### To build `.oar` file (faster):

1. put the whole folder (`opticalemulator`) into `onos/drivers/`
2. `cd onos/drivers`
3. `bazel build //drivers/opticalemulator/roadm:onos-drivers-opticalemulator-roadm-oar`
4. copy `bazel-bin/drivers/opticalemulator/roadm/onos-drivers-opticalemulator-roadm-oar.oar`
   to wherever you like, and install it into onos as desired.

### To build as part of ONOS (slower):

1. put the whole folder (`opticalemulator`) into `onos/drivers/`
2. at `onos/tools/build/bazel/modules.bzl`
        add     `"//drivers/opticalemulator/roadm:onos-drivers-opticalemulator-roadm-oar": [],`
        into    `DRIVER_MAP`
3. `cd onos`
4. `bazel build onos`
