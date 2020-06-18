/*
 * Copyright 2016-present Open Networking Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.onosproject.drivers.opticalemulator.roadm.rest;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;
import org.apache.commons.configuration.HierarchicalConfiguration;
import org.onlab.packet.ChassisId;
import org.onosproject.drivers.utilities.XmlConfigParser;
import org.onosproject.net.AnnotationKeys;
import org.onosproject.net.ChannelSpacing;
import org.onosproject.net.CltSignalType;
import org.onosproject.net.DefaultAnnotations;
import org.onosproject.net.Device;
import org.onosproject.net.DeviceId;
import org.onosproject.net.GridType;
import org.onosproject.net.OchSignal;
import org.onosproject.net.OduSignalType;
import org.onosproject.net.PortNumber;
import org.onosproject.net.SparseAnnotations;
import org.onosproject.net.device.DefaultDeviceDescription;
import org.onosproject.net.device.DeviceDescription;
import org.onosproject.net.device.DeviceDescriptionDiscovery;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.device.PortDescription;
import org.onosproject.net.driver.AbstractHandlerBehaviour;
import org.onosproject.protocol.rest.RestSBController;
import org.slf4j.Logger;

import javax.ws.rs.core.MediaType;
import java.util.List;

import static com.google.common.base.Preconditions.checkNotNull;
import static org.onosproject.net.optical.device.OchPortHelper.ochPortDescription;
import static org.onosproject.net.optical.device.OduCltPortHelper.oduCltPortDescription;
import static org.slf4j.LoggerFactory.getLogger;

/**
 * Discovers the ports from a Ciena WaveServer Rest device.
 */
//TODO: Use CienaRestDevice
public class OpticalEmulatorDeviceDescription extends AbstractHandlerBehaviour
        implements DeviceDescriptionDiscovery {

    private final Logger log = getLogger(getClass());

    private static final String PORT_ID = "port-id";
    private static final String XML = "xml";
    private static final String ENABLED = "enabled";
    private static final String PORTS = "ports";
    private static final String PORT_IN = "port-in";
    private static final String PORT_OUT = "port-out";

    private static final String CHANNEL_ID =
            "optical-emulator-channel";

    private static final String PORT_REQUEST =
            "optical-emulator-port";

    @Override
    public DeviceDescription discoverDeviceDetails() {
        log.debug("getting device description");
        DeviceService deviceService = checkNotNull(handler().get(DeviceService.class));
        DeviceId deviceId = handler().data().deviceId();
        Device device = deviceService.getDevice(deviceId);

        if (device == null) {
            return new DefaultDeviceDescription(deviceId.uri(),
                                                Device.Type.ROADM,
                                                "Optical-Emulator",
                                                "ROADM",
                                                "Unknown",
                                                "Unknown",
                                                new ChassisId());
        } else {
            return new DefaultDeviceDescription(device.id().uri(),
                                                Device.Type.ROADM,
                                                device.manufacturer(),
                                                device.hwVersion(),
                                                device.swVersion(),
                                                device.serialNumber(),
                                                device.chassisId());
        }
    }

    @Override
    public List<PortDescription> discoverPortDetails() {
        List<PortDescription> ports = Lists.newArrayList();
        Integer ifCount = 1;
        DefaultAnnotations.Builder annotations = DefaultAnnotations.builder();
        for (int i=0; i<6; i++){

          annotations.set(AnnotationKeys.CHANNEL_ID, String.valueOf(ifCount));
          // TX/OUT and RX/IN ports
          annotations.set(AnnotationKeys.PORT_OUT, String.valueOf(ifCount));
          annotations.set(AnnotationKeys.PORT_IN, String.valueOf(ifCount));
          ports.add(ochPortDescription(PortNumber.portNumber(ifCount), true, OduSignalType.ODU4, true,
                                  new OchSignal(GridType.FLEX, ChannelSpacing.CHL_6P25GHZ, 1, 1), annotations.build()));
          ifCount++;
        }

        System.out.println("==========================================");
        System.out.println("==========================================");
        ///////////////////////////////////////////////////////////////
        return ports;

        //return getPorts();
    }

}

