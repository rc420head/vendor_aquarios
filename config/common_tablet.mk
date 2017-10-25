# Common settings and files
-include vendor/aquarios/config/common.mk

# Add tablet overlays
PRODUCT_PACKAGE_OVERLAYS += vendor/aquarios/overlay/common_tablet

PRODUCT_CHARACTERISTICS := tablet
