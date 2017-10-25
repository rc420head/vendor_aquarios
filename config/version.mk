#Version of the ROM
AQUARIOS_CODENAME := CONFIDENTIAL
AQUARIOS_REVISION := CR-6.0

ifndef AQUARIOS_BUILDTYPE
  AQUARIOS_BUILDTYPE := UNOFFICIAL
endif

TARGET_PRODUCT_SHORT := $(TARGET_PRODUCT)
TARGET_PRODUCT_SHORT := $(subst aquarios_,,$(TARGET_PRODUCT_SHORT))

AQUARIOS_VERSION := $(AQUARIOS_REVISION)-$(AQUARIOS_CODENAME)-$(AQUARIOS_BUILDTYPE)-$(TARGET_PRODUCT_SHORT)-$(shell date -u +%Y%m%d-%H%M)

PRODUCT_BUILD_PROP_OVERRIDES += BUILD_DISPLAY_ID="$(BUILD_ID)-$(shell whoami)@$(shell hostname)"

# Apply it to build.prop
PRODUCT_PROPERTY_OVERRIDES += \
    ro.modversion=AquariOS-$(AQUARIOS_VERSION) \
    ro.aquarios.version=$(AQUARIOS_VERSION) \
    ro.romstats.url=https://stats.aquarios.org \
    ro.romstats.name=AquariOS \
    ro.romstats.version=$(AQUARIOS_VERSION)
