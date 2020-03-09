emulator driver

1. put the whole folder (opticalemulator) in to onos/drivers/

2. at onos/tools/build/bazel/modules.bzl

        add     "//drivers/opticalemulator/roadm:onos-drivers-opticalemulator-roadm-oar": [],
        
        into    DRIVER_MAP
        
3. bazel build onos
