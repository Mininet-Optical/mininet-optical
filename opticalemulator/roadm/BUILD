COMPILE_DEPS = CORE_DEPS + JACKSON + [
    "@javax_ws_rs_api//jar",
    "//utils/rest:onlab-rest",
    "//drivers/utilities:onos-drivers-utilities",
    "//protocols/rest/api:onos-protocols-rest-api",
    "//apps/optical-model:onos-apps-optical-model",
    "//drivers/optical:onos-drivers-optical",
]

BUNDLES = [
    ":onos-drivers-opticalemulator-roadm",
    "//drivers/utilities:onos-drivers-utilities",
]

REQUIRED_APPS = [
    "org.onosproject.restsb",
    "org.onosproject.optical-model",
    "org.onosproject.drivers.optical",
]

osgi_jar_with_tests(
    resources = glob(["src/main/resources/**"]),
    resources_root = "src/main/resources",
    test_deps = TEST_ADAPTERS,
    deps = COMPILE_DEPS,
)

onos_app(
    app_name = "org.onosproject.drivers.opticalemulator.roadm",
    category = "Drivers",
    description = "Adds support for Optical Emulator ROADM devices.",
    included_bundles = BUNDLES,
    required_apps = REQUIRED_APPS,
    title = "Optical Emulator ROADM Drivers",
    url = "http://onosproject.org",
)
