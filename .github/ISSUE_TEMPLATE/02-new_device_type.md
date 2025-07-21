name: Add support for a device
description: A device is missing from the Hubspace plugin
labels: ["enhancement"]
assignees:
  - Expl0dingBanana
body:
  - type: markdown
    attributes:
      value: |
        This issue form is for adding a new device only!
  - type: textarea
    validations:
      required: false
    attributes:
      label: The device
      description: >-
        Provide a link to the product
  - type: textarea
    validations:
      required: false
    attributes:
      label: Features
      description: >-
        What features(s) do you want enabled? Optionally provide screenshots of the
        corresponding app for the feature.
  - type: textarea
    validations:
      required: true
    attributes:
      label: Datadump
      description: >-
        Place to upload ``_dump_hs_devices.json`` for debugging purposes.
  - type: textarea
    attributes:
      label: Additional information
      description: >
        If you have any additional information for us, use the field below.
